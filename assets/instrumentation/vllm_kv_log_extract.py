#!/usr/bin/env python3
"""Extract deterministic KV-capacity inputs from vLLM startup logs.

The script intentionally does not infer model topology. It only turns vLLM log
lines into a compact JSON payload consumed by kv_capacity_calculator.py.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path
from typing import Any


SIZE_UNITS = {
    "b": 1,
    "kb": 1000,
    "mb": 1000**2,
    "gb": 1000**3,
    "tb": 1000**4,
    "kib": 1024,
    "mib": 1024**2,
    "gib": 1024**3,
    "tib": 1024**4,
}


KEY_PATTERNS = [
    "Available KV cache memory",
    "GPU KV cache size",
    "NPU KV cache size",
    "Free memory on device",
    "Current KV cache memory",
    "kv_cache_dtype",
    "tensor_parallel_size",
    "pipeline_parallel_size",
    "data_parallel_size",
    "decode_context_parallel_size",
    "enable_prefix_caching",
    "enable_chunked_prefill",
    "Block size is set",
    "Using attention backend",
    "attention backend",
    "quantization",
    "GPU KV cache usage",
    "Prefix cache hit rate",
    "preempt",
    "recompute",
    "OOM",
]


def parse_size_to_bytes(value: str, unit: str | None) -> int:
    number = float(value.replace(",", ""))
    if not unit:
        return int(number)
    return int(number * SIZE_UNITS[unit.lower()])


def parse_number(value: str) -> int:
    return int(value.replace(",", ""))


def last_match(pattern: str, text: str, flags: int = re.IGNORECASE) -> re.Match[str] | None:
    matches = list(re.finditer(pattern, text, flags))
    return matches[-1] if matches else None


def parse_non_default_args(text: str) -> dict[str, Any]:
    match = last_match(r"non-default args:\s*(\{.*?\})(?:\n|$)", text)
    if not match:
        return {}
    raw = match.group(1)
    try:
        return ast.literal_eval(raw)
    except Exception:
        return {"_parse_error": raw[:1000]}


def parse_engine_config_pairs(text: str) -> dict[str, Any]:
    match = last_match(r"Initializing .*? engine .*? with config:\s*(.*)", text)
    if not match:
        return {}
    line = match.group(1)
    pairs: dict[str, Any] = {}
    for key in [
        "dtype",
        "max_seq_len",
        "tensor_parallel_size",
        "pipeline_parallel_size",
        "data_parallel_size",
        "decode_context_parallel_size",
        "quantization",
        "kv_cache_dtype",
        "device_config",
        "served_model_name",
        "enable_prefix_caching",
        "enable_chunked_prefill",
    ]:
        item = re.search(rf"\b{re.escape(key)}=([^,]+)", line)
        if item:
            pairs[key] = item.group(1).strip()
    return pairs


def parse_scalar_log_args(text: str) -> dict[str, Any]:
    """Parse stable scalar args even when the full Python dict is not literal."""
    scalars: dict[str, Any] = {}
    match = last_match(r"non-default args:\s*(.*)", text)
    if not match:
        return scalars
    line = match.group(1)
    for key in [
        "max_model_len",
        "max_num_batched_tokens",
        "max_num_seqs",
        "tensor_parallel_size",
        "pipeline_parallel_size",
        "data_parallel_size",
        "decode_context_parallel_size",
        "gpu_memory_utilization",
        "port",
    ]:
        item = re.search(rf"['\"]{re.escape(key)}['\"]:\s*([0-9.]+)", line)
        if item:
            value = item.group(1)
            scalars[key] = float(value) if "." in value else int(value)
    for key in [
        "model",
        "model_tag",
        "served_model_name",
        "quantization",
        "kv_cache_dtype",
        "dtype",
    ]:
        item = re.search(rf"['\"]{re.escape(key)}['\"]:\s*['\"]([^'\"]+)['\"]", line)
        if item:
            scalars[key] = item.group(1)
    for key in ["enable_prefix_caching", "enable_chunked_prefill", "trust_remote_code", "enable_expert_parallel"]:
        item = re.search(rf"['\"]{re.escape(key)}['\"]:\s*(True|False)", line)
        if item:
            scalars[key] = item.group(1) == "True"
    return scalars


def extract(log_path: Path) -> dict[str, Any]:
    text = log_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    key_lines = [line for line in lines if any(p.lower() in line.lower() for p in KEY_PATTERNS)]

    non_default_args = parse_non_default_args(text)
    scalar_log_args = parse_scalar_log_args(text)
    engine_config = parse_engine_config_pairs(text)

    data: dict[str, Any] = {
        "source_log": str(log_path),
        "key_lines": key_lines[-160:],
        "non_default_args": non_default_args,
        "scalar_log_args": scalar_log_args,
        "engine_config": engine_config,
        "warnings": {},
        "kv_summary": {},
        "memory_profile": {},
        "parallelism": {},
        "runtime": {},
    }

    match = last_match(r"Available KV cache memory:\s*([0-9.,]+)\s*([KMGT]i?B)", text)
    if match:
        data["kv_summary"]["available_kv_cache_memory_bytes"] = parse_size_to_bytes(match.group(1), match.group(2))
        data["kv_summary"]["available_kv_cache_memory_text"] = match.group(0)

    match = last_match(r"(?:GPU|NPU) KV cache size:\s*([0-9,]+)\s*tokens", text)
    if match:
        data["kv_summary"]["gpu_kv_cache_tokens"] = parse_number(match.group(1))
        data["kv_summary"]["gpu_kv_cache_tokens_text"] = match.group(0)

    match = last_match(r"Block size is set to\s*([0-9]+)", text)
    if match:
        data["runtime"]["block_size"] = int(match.group(1))

    free_memory_matches = []
    memory_profile_matches = []
    for match in re.finditer(
        r"Free memory on device \(([0-9.]+)/([0-9.]+)\s*GiB\).*?"
        r"Desired GPU memory utilization is \(([0-9.]+),\s*([0-9.]+)\s*GiB\).*?"
        r"Actual usage:\s*([0-9.]+)\s*GiB for weights,\s*([0-9.]+)\s*GiB for peak activation,\s*"
        r"([0-9.]+)\s*GiB for non-torch memory(?:,\s*([0-9.]+)\s*GiB for [^.]+ memory)?\.",
        text,
        re.IGNORECASE,
    ):
        free_memory_matches.append(
            {
                "free_gib": float(match.group(1)),
                "total_gib": float(match.group(2)),
                "gpu_memory_utilization": float(match.group(3)),
                "desired_memory_gib": float(match.group(4)),
            }
        )
        memory_profile_matches.append(
            {
                "weights_gib": float(match.group(5)),
                "peak_activation_gib": float(match.group(6)),
                "non_torch_gib": float(match.group(7)),
                "graph_or_other_gib": float(match.group(8)) if match.group(8) else None,
                "line": match.group(0),
            }
        )

    if free_memory_matches:
        data["memory_profile"]["device_memory_samples"] = free_memory_matches
    if memory_profile_matches:
        data["memory_profile"]["actual_usage_samples"] = memory_profile_matches

    kv_cache_memory_bytes = [int(m.group(1)) for m in re.finditer(r"--kv-cache-memory=(\d+)", text)]
    if kv_cache_memory_bytes:
        data["kv_summary"]["suggested_kv_cache_memory_fit_bytes"] = min(kv_cache_memory_bytes)
        data["kv_summary"]["suggested_kv_cache_memory_full_bytes"] = max(kv_cache_memory_bytes)

    match = last_match(r"Current KV cache memory:\s*([0-9.]+)\s*([KMGT]i?B)", text)
    if match:
        data["kv_summary"]["current_kv_cache_memory_bytes"] = parse_size_to_bytes(match.group(1), match.group(2))

    combined = {**non_default_args, **scalar_log_args, **engine_config}
    for src, dst in [
        ("tensor_parallel_size", "tp_size"),
        ("pipeline_parallel_size", "pp_size"),
        ("data_parallel_size", "dp_size"),
        ("decode_context_parallel_size", "dcp_size"),
    ]:
        value = combined.get(src)
        if value is not None:
            try:
                data["parallelism"][dst] = int(str(value).strip())
            except ValueError:
                pass

    for src, dst in [
        ("max_model_len", "max_model_len"),
        ("max_seq_len", "max_model_len"),
        ("max_num_batched_tokens", "max_num_batched_tokens"),
        ("max_num_seqs", "max_num_seqs"),
    ]:
        value = combined.get(src)
        if value is not None:
            try:
                data["runtime"][dst] = int(str(value).strip())
            except ValueError:
                pass

    for src, dst in [
        ("kv_cache_dtype", "kv_cache_dtype"),
        ("dtype", "dtype"),
        ("quantization", "quantization"),
        ("device_config", "device_config"),
        ("enable_prefix_caching", "enable_prefix_caching"),
        ("enable_chunked_prefill", "enable_chunked_prefill"),
    ]:
        if src in combined:
            data["runtime"][dst] = combined[src]

    lower = text.lower()
    data["warnings"] = {
        "preemption_lines": [line for line in lines if "preempt" in line.lower()][-40:],
        "recompute_lines": [line for line in lines if "recompute" in line.lower()][-40:],
        "oom_lines": [line for line in lines if "out of memory" in line.lower() or "oom" in line.lower()][-40:],
        "has_worker_crash": "worker" in lower and ("crash" in lower or "died" in lower),
    }
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", required=True, type=Path, help="vLLM serve.log path")
    parser.add_argument("--out", type=Path, help="write JSON to this path")
    parser.add_argument("--text-out", type=Path, help="write compact key-line extract")
    args = parser.parse_args()

    payload = extract(args.log)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)

    if args.text_out:
        args.text_out.parent.mkdir(parents=True, exist_ok=True)
        args.text_out.write_text("\n".join(payload["key_lines"]) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
