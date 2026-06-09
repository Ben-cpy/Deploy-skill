#!/usr/bin/env python3
"""Deterministic KV-cache capacity calculator for LLM serving diagnostics.

Inputs are explicit: model config, runtime log extraction JSON, and optional
parallelism/memory overrides. Outputs are JSON so reports can cite formulas,
intermediate values, and runtime calibration without relying on ad-hoc agent
reasoning.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


DTYPE_BYTES = {
    "float32": 4,
    "fp32": 4,
    "torch.float32": 4,
    "bfloat16": 2,
    "bf16": 2,
    "torch.bfloat16": 2,
    "float16": 2,
    "fp16": 2,
    "half": 2,
    "torch.float16": 2,
    "float8": 1,
    "fp8": 1,
    "int8": 1,
    "uint8": 1,
}


def as_int(value: Any, default: int | None = None) -> int | None:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def as_float(value: Any, default: float | None = None) -> float | None:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def dtype_bytes(dtype: str | None, override: int | None = None) -> int:
    if override:
        return override
    if not dtype:
        return 2
    normalized = str(dtype).replace("torch.", "").lower()
    return DTYPE_BYTES.get(normalized, 2)


def ceil_div(a: int, b: int) -> int:
    return (a + b - 1) // b


def load_json(path: Path | None) -> dict[str, Any]:
    if not path:
        return {}
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def infer_model_profile(cfg: dict[str, Any], model_profile: str) -> str:
    if model_profile != "auto":
        return model_profile
    model_type = str(cfg.get("model_type", "")).lower()
    arch = " ".join(str(x) for x in cfg.get("architectures", [])).lower()
    if "glm_moe_dsa" in model_type or "dsa" in arch:
        return "glm_dsa"
    if any(k in cfg for k in ["kv_lora_rank", "q_lora_rank"]):
        return "mla"
    return "standard"


def infer_attention_kind(cfg: dict[str, Any], profile: str) -> str:
    if profile in {"mla", "glm_dsa"}:
        return "MLA/DSA"
    heads = as_int(cfg.get("num_attention_heads") or cfg.get("n_head"), 0) or 0
    kv_heads = as_int(cfg.get("num_key_value_heads") or cfg.get("num_kv_heads"), heads) or heads
    if kv_heads == heads:
        return "MHA"
    if kv_heads == 1:
        return "MQA"
    return "GQA"


def standard_kv_dims(cfg: dict[str, Any]) -> dict[str, Any]:
    heads = as_int(cfg.get("num_attention_heads") or cfg.get("n_head"))
    kv_heads = as_int(cfg.get("num_key_value_heads") or cfg.get("num_kv_heads"), heads)
    hidden = as_int(cfg.get("hidden_size") or cfg.get("n_embd"))
    head_dim = as_int(cfg.get("head_dim"))
    if head_dim is None and heads and hidden:
        head_dim = hidden // heads
    if kv_heads is None or head_dim is None:
        raise ValueError("standard KV formula requires num_key_value_heads and head_dim")
    return {
        "logical_kv_elements_per_layer_token": 2 * kv_heads * head_dim,
        "heads": heads,
        "kv_heads": kv_heads,
        "head_dim": head_dim,
        "formula": "2 * num_key_value_heads * head_dim",
    }


def mla_kv_dims(cfg: dict[str, Any], profile: str) -> dict[str, Any]:
    kv_lora_rank = as_int(cfg.get("kv_lora_rank"))
    qk_rope_head_dim = as_int(cfg.get("qk_rope_head_dim"), 0) or 0
    qk_nope_head_dim = as_int(cfg.get("qk_nope_head_dim"), 0) or 0
    v_head_dim = as_int(cfg.get("v_head_dim"))
    heads = as_int(cfg.get("num_attention_heads") or cfg.get("n_head"))
    kv_heads = as_int(cfg.get("num_key_value_heads") or cfg.get("num_kv_heads"), 1) or 1

    if kv_lora_rank is not None:
        elements = kv_lora_rank + qk_rope_head_dim
        formula = "kv_lora_rank + qk_rope_head_dim"
        if profile == "glm_dsa" and v_head_dim is not None and qk_nope_head_dim:
            formula += " (GLM-DSA latent KV; qk_nope_head_dim/v_head_dim tracked as metadata)"
        return {
            "logical_kv_elements_per_layer_token": elements,
            "heads": heads,
            "kv_heads": kv_heads,
            "kv_lora_rank": kv_lora_rank,
            "qk_rope_head_dim": qk_rope_head_dim,
            "qk_nope_head_dim": qk_nope_head_dim,
            "v_head_dim": v_head_dim,
            "formula": formula,
        }

    dims = standard_kv_dims(cfg)
    dims["formula"] += " (fallback because kv_lora_rank is absent)"
    return dims


def apply_sliding_window(layers: int, cfg: dict[str, Any], max_model_len: int | None) -> dict[str, Any]:
    sliding_window = as_int(cfg.get("sliding_window"))
    if not sliding_window or not max_model_len:
        return {
            "effective_full_attention_layers": layers,
            "sliding_window": sliding_window,
            "capacity_token_equivalent_factor": 1.0,
            "note": "No sliding-window discount applied.",
        }
    # Capacity is still reported as full-context token-equivalent. Runtime can
    # store fewer tokens for SWA layers once sequence length exceeds window.
    equivalent = (layers * max_model_len) / max(1, layers * min(max_model_len, sliding_window))
    return {
        "effective_full_attention_layers": layers,
        "sliding_window": sliding_window,
        "capacity_token_equivalent_factor": equivalent,
        "note": "SWA present. Token-equivalent capacity depends on request length; runtime log is authoritative for schedulable tokens.",
    }


def get_runtime(log_extract: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    return (
        log_extract.get("kv_summary", {}) if isinstance(log_extract.get("kv_summary"), dict) else {},
        log_extract.get("parallelism", {}) if isinstance(log_extract.get("parallelism"), dict) else {},
        log_extract.get("runtime", {}) if isinstance(log_extract.get("runtime"), dict) else {},
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-config", type=Path, required=True, help="model config.json")
    parser.add_argument("--log-extract-json", type=Path, help="JSON from vllm_kv_log_extract.py")
    parser.add_argument("--out", type=Path, help="write JSON result")
    parser.add_argument("--model-profile", default="auto", choices=["auto", "standard", "mla", "glm_dsa"])
    parser.add_argument("--tp-size", type=int, help="tensor parallel size override")
    parser.add_argument("--dp-size", type=int, help="data parallel size override")
    parser.add_argument("--pp-size", type=int, help="pipeline parallel size override")
    parser.add_argument("--dcp-size", type=int, help="decode-context parallel size override")
    parser.add_argument("--kv-cache-memory-bytes", type=int, help="per-rank KV cache memory budget override")
    parser.add_argument("--kv-cache-memory-gib", type=float, help="per-rank KV cache memory budget override")
    parser.add_argument("--dtype-bytes", type=int, help="KV cache element bytes override")
    parser.add_argument("--kv-tp-policy", choices=["auto", "shard_heads", "replicate_latent", "replicate", "none"], default="auto")
    parser.add_argument("--dcp-kv-policy", choices=["auto", "none", "shard_context"], default="auto")
    parser.add_argument("--tp-padding-multiple", type=int, default=1, help="pad KV heads/latent dims to this multiple per TP rank")
    parser.add_argument("--mla-tp-waste-factor", type=float, default=1.0, help="extra resident KV multiplier for MLA/DSA TP kernels")
    parser.add_argument("--max-model-len", type=int, help="override runtime max_model_len")
    args = parser.parse_args()

    cfg = load_json(args.model_config)
    log_extract = load_json(args.log_extract_json)
    kv_summary, parallelism, runtime = get_runtime(log_extract)

    profile = infer_model_profile(cfg, args.model_profile)
    attention_kind = infer_attention_kind(cfg, profile)
    layers = as_int(cfg.get("num_hidden_layers") or cfg.get("n_layer"))
    if not layers:
        raise ValueError("model config must include num_hidden_layers or n_layer")

    tp = args.tp_size or as_int(parallelism.get("tp_size"), 1) or 1
    dp = args.dp_size or as_int(parallelism.get("dp_size"), 1) or 1
    pp = args.pp_size or as_int(parallelism.get("pp_size"), 1) or 1
    dcp = args.dcp_size or as_int(parallelism.get("dcp_size"), 1) or 1
    resident_layers_per_pp_rank = ceil_div(layers, pp)
    max_model_len = args.max_model_len or as_int(runtime.get("max_model_len")) or as_int(cfg.get("max_position_embeddings"))

    kv_dtype = runtime.get("kv_cache_dtype") or cfg.get("torch_dtype") or cfg.get("dtype")
    element_bytes = dtype_bytes(str(kv_dtype) if kv_dtype is not None else None, args.dtype_bytes)

    dims = mla_kv_dims(cfg, profile) if profile in {"mla", "glm_dsa"} else standard_kv_dims(cfg)
    logical_per_layer = int(dims["logical_kv_elements_per_layer_token"])
    logical_bytes_per_token = layers * logical_per_layer * element_bytes

    kv_policy = args.kv_tp_policy
    if kv_policy == "auto":
        kv_policy = "replicate_latent" if profile in {"mla", "glm_dsa"} else "shard_heads"

    dcp_policy = args.dcp_kv_policy
    if dcp_policy == "auto":
        dcp_policy = "none"

    padding_multiple = max(1, args.tp_padding_multiple)
    tp_padding_factor = 1.0
    tp_waste_factor = 1.0

    if kv_policy == "shard_heads":
        kv_heads = as_int(dims.get("kv_heads"), 1) or 1
        head_dim = as_int(dims.get("head_dim"), 1) or 1
        per_rank_heads = ceil_div(kv_heads, tp)
        if padding_multiple > 1:
            per_rank_heads = int(math.ceil(per_rank_heads / padding_multiple) * padding_multiple)
        resident_per_layer = 2 * per_rank_heads * head_dim
        ideal_per_rank = logical_per_layer / tp
        tp_padding_factor = resident_per_layer / ideal_per_rank if ideal_per_rank else 1.0
        tp_waste_factor = resident_per_layer * tp / logical_per_layer if logical_per_layer else 1.0
    elif kv_policy == "replicate_latent":
        latent_dim = logical_per_layer
        if padding_multiple > 1:
            latent_dim = int(math.ceil(latent_dim / padding_multiple) * padding_multiple)
        resident_per_layer = latent_dim
        tp_padding_factor = resident_per_layer / logical_per_layer if logical_per_layer else 1.0
        tp_waste_factor = tp * tp_padding_factor * max(1.0, args.mla_tp_waste_factor)
        resident_per_layer = int(resident_per_layer * max(1.0, args.mla_tp_waste_factor))
    elif kv_policy == "replicate":
        resident_per_layer = logical_per_layer
        tp_waste_factor = float(tp)
    else:
        resident_per_layer = logical_per_layer
        tp_waste_factor = 1.0

    dcp_divisor = dcp if dcp_policy == "shard_context" else 1
    if dcp_divisor > 1:
        resident_per_layer = ceil_div(resident_per_layer, dcp_divisor)

    resident_bytes_per_token_per_rank = resident_layers_per_pp_rank * resident_per_layer * element_bytes

    kv_memory_bytes = args.kv_cache_memory_bytes
    if kv_memory_bytes is None and args.kv_cache_memory_gib is not None:
        kv_memory_bytes = int(args.kv_cache_memory_gib * 1024**3)
    if kv_memory_bytes is None:
        kv_memory_bytes = as_int(kv_summary.get("available_kv_cache_memory_bytes"))
    if kv_memory_bytes is None:
        kv_memory_bytes = as_int(kv_summary.get("current_kv_cache_memory_bytes"))
    if kv_memory_bytes is None:
        kv_memory_bytes = as_int(kv_summary.get("suggested_kv_cache_memory_fit_bytes"))

    static_per_dp_tokens_raw = kv_memory_bytes // resident_bytes_per_token_per_rank if kv_memory_bytes else None
    block_size = as_int(runtime.get("block_size"))
    if static_per_dp_tokens_raw is not None and block_size:
        static_per_dp_tokens = (static_per_dp_tokens_raw // block_size) * block_size
    else:
        static_per_dp_tokens = static_per_dp_tokens_raw
    runtime_tokens = as_int(kv_summary.get("gpu_kv_cache_tokens"))
    selected_per_dp_tokens = runtime_tokens or static_per_dp_tokens
    aggregate_tokens = selected_per_dp_tokens * dp if selected_per_dp_tokens is not None else None

    calibration: dict[str, Any] = {}
    if runtime_tokens and kv_memory_bytes:
        observed_bytes_per_token = kv_memory_bytes / runtime_tokens
        calibration = {
            "runtime_tokens": runtime_tokens,
            "kv_memory_bytes": kv_memory_bytes,
            "observed_resident_bytes_per_token_per_rank": observed_bytes_per_token,
            "formula_resident_bytes_per_token_per_rank": resident_bytes_per_token_per_rank,
            "runtime_to_formula_ratio": observed_bytes_per_token / resident_bytes_per_token_per_rank
            if resident_bytes_per_token_per_rank
            else None,
        }

    result = {
        "inputs": {
            "model_config": str(args.model_config),
            "log_extract_json": str(args.log_extract_json) if args.log_extract_json else None,
            "model_profile": profile,
            "attention_kind": attention_kind,
            "tp_size": tp,
            "dp_size": dp,
            "pp_size": pp,
            "dcp_size": dcp,
            "kv_cache_dtype": kv_dtype,
            "dtype_bytes": element_bytes,
            "max_model_len": max_model_len,
        },
        "model_kv_formula": {
            "num_layers": layers,
            "resident_layers_per_pp_rank": resident_layers_per_pp_rank,
            "per_layer_elements": logical_per_layer,
            "logical_kv_bytes_per_token_all_ranks": logical_bytes_per_token,
            "formula": dims["formula"],
            "fields": {k: v for k, v in dims.items() if k != "formula"},
        },
        "parallelism_effects": {
            "kv_tp_policy": kv_policy,
            "dcp_kv_policy": dcp_policy,
            "resident_kv_elements_per_layer_token_per_tp_rank": resident_per_layer,
            "resident_kv_bytes_per_token_per_tp_rank": resident_bytes_per_token_per_rank,
            "tp_replication_or_padding_factor": tp_waste_factor,
            "tp_padding_factor": tp_padding_factor,
            "dcp_divisor_applied": dcp_divisor,
            "dp_note": "DP multiplies aggregate serving capacity, not single-session KV capacity.",
            "pp_note": "PP divides layers across pipeline stages; static capacity uses ceil(num_layers / pp_size) layers per rank and runtime log remains authoritative.",
            "dcp_note": "Default DCP policy is conservative none; use --dcp-kv-policy shard_context only when the engine's KV layout is known to shard context residency.",
        },
        "runtime_log": {
            "kv_summary": kv_summary,
            "runtime": runtime,
            "parallelism": parallelism,
        },
        "capacity": {
            "kv_cache_memory_bytes_per_rank": kv_memory_bytes,
            "static_formula_per_dp_tokens_raw": static_per_dp_tokens_raw,
            "block_size": block_size,
            "static_formula_per_dp_tokens": static_per_dp_tokens,
            "runtime_reported_per_dp_tokens": runtime_tokens,
            "selected_per_dp_tokens": selected_per_dp_tokens,
            "selected_aggregate_tokens": aggregate_tokens,
            "usable_context_tokens_per_dp": selected_per_dp_tokens,
            "aggregate_usable_context_tokens": aggregate_tokens,
            "capacity_unit_note": "Token-equivalent usable KV/context capacity. Do not report derived request concurrency in capacity summaries.",
            "selection_rule": "runtime_reported_per_dp_tokens overrides static formula when present; otherwise use static_formula_per_dp_tokens.",
        },
        "sliding_window": apply_sliding_window(layers, cfg, max_model_len),
        "calibration": calibration,
        "caveats": [
            "For MLA/DSA, TP may replicate latent KV or pad kernel layouts; use --kv-tp-policy and --mla-tp-waste-factor to match known engine behavior.",
            "For DP, aggregate tokens are not a single shared KV pool.",
            "For hybrid/SWA models, runtime vLLM token capacity is more reliable than pure full-context token-equivalent math.",
        ],
    }

    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
