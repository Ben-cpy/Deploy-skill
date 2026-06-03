from __future__ import annotations

import argparse
import asyncio
import csv
import json
import math
import os
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import httpx
from transformers import AutoTokenizer, PreTrainedTokenizerBase


JSON_HEADERS = {
    "accept": "application/json",
    "content-type": "application/json",
}


@dataclass(frozen=True)
class BenchConfig:
    base_url: str
    model: str
    tokenizer: str
    api_key: str
    request_concurrency: int
    active_sessions: int
    num_sessions: int
    initial_input_tokens: int
    shared_prefix_tokens: int
    delta_input_tokens: int
    num_rounds: int
    output_tokens: int
    results_dir: Path
    timeout: float
    temperature: float
    seed: int | None
    startup_ramp_seconds: float
    request_min_tokens: bool
    request_ignore_eos: bool
    dry_run: bool


@dataclass
class RequestMetric:
    session_id: int
    round_id: int
    target_input_tokens: int
    measured_input_tokens: int
    target_output_tokens: int
    output_tokens: int
    ttft_s: float | None
    tpot_s: float | None
    latency_s: float
    output_tokens_per_s: float
    status_code: int | None
    error: str | None


@dataclass(frozen=True)
class TheoreticalKvCacheStats:
    per_round_prompt_tokens: list[int]
    per_round_reusable_tokens: list[int]
    per_round_peak_request_kv_tokens: list[int]
    per_round_peak_request_concurrency_kv_tokens: list[int]
    per_round_peak_active_sessions_kv_tokens: list[int]
    round0_cross_session_prefix_tokens: int
    total_prompt_tokens: int
    total_reusable_tokens: int
    overall_hit_rate: float
    steady_state_prompt_tokens: int
    steady_state_reusable_tokens: int
    steady_state_hit_rate: float | None


@dataclass(frozen=True)
class ResultArtifacts:
    jsonl_path: Path
    summary_csv_path: Path
    round_metrics_csv_path: Path | None
    round_metrics_png_path: Path | None


class TokenTextFactory:
    def __init__(self, tokenizer: PreTrainedTokenizerBase) -> None:
        self.tokenizer = tokenizer

    def make_token_ids(self, token_count: int, salt: str) -> list[int]:
        if token_count <= 0:
            return []

        seed_text = (
            f"{salt}. This benchmark context is synthetic and deterministic. "
            "It contains repeated neutral text for vLLM latency measurement. "
        )
        seed_ids = self.tokenizer.encode(seed_text, add_special_tokens=False)
        if not seed_ids:
            raise ValueError("Tokenizer produced no token ids for benchmark seed text")

        repeats = math.ceil(token_count / len(seed_ids))
        return (seed_ids * repeats)[:token_count]

    def make_text(self, token_count: int, salt: str) -> str:
        if token_count <= 0:
            return ""
        return self.tokenizer.decode(
            self.make_token_ids(token_count, salt),
            skip_special_tokens=True,
        )

    def make_text_from_segments(self, segments: list[tuple[int, str]]) -> str:
        token_ids: list[int] = []
        for token_count, salt in segments:
            token_ids.extend(self.make_token_ids(token_count, salt))
        if not token_ids:
            return ""
        return self.tokenizer.decode(token_ids, skip_special_tokens=True)


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be > 0")
    return parsed


def non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return parsed


def non_negative_float(value: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return parsed


def parse_args() -> BenchConfig:
    parser = argparse.ArgumentParser(
        description="Simulate multi-round agent sessions against vLLM Chat Completions."
    )
    parser.add_argument("--base-url", default="http://localhost:8000/v1")
    parser.add_argument("--model", required=True)
    parser.add_argument("--tokenizer", default=None)
    parser.add_argument("--api-key", default=os.getenv("OPENAI_API_KEY", "EMPTY"))
    parser.add_argument(
        "--request-concurrency",
        type=positive_int,
        default=None,
        help="Maximum number of in-flight inference requests.",
    )
    parser.add_argument(
        "--concurrency",
        type=positive_int,
        default=None,
        help="Deprecated alias of --request-concurrency.",
    )
    parser.add_argument(
        "--active-sessions",
        type=positive_int,
        default=None,
        help=(
            "Maximum number of live conversation sessions resident at the same time. "
            "Defaults to --num-sessions."
        ),
    )
    parser.add_argument("--num-sessions", type=positive_int, required=True)
    parser.add_argument("--initial-input-tokens", type=positive_int, required=True)
    parser.add_argument(
        "--shared-prefix-tokens",
        type=non_negative_int,
        default=0,
        help=(
            "Shared prefix tokens embedded in the first user turn for every session. "
            "Must be <= --initial-input-tokens."
        ),
    )
    parser.add_argument("--delta-input-tokens", type=positive_int, required=True)
    parser.add_argument("--num-rounds", type=positive_int, required=True)
    parser.add_argument("--output-tokens", type=positive_int, required=True)
    parser.add_argument("--results-dir", type=Path, default=Path("bench-results"))
    parser.add_argument("--timeout", type=float, default=600.0)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument(
        "--startup-ramp-seconds",
        type=non_negative_float,
        default=1.0,
        help=(
            "Spread initial session starts over this many seconds. "
            "Set to 0 to launch immediately."
        ),
    )
    parser.add_argument(
        "--no-min-tokens",
        action="store_true",
        help="Do not send vLLM min_tokens in the request payload.",
    )
    parser.add_argument(
        "--no-ignore-eos",
        action="store_true",
        help="Do not send vLLM ignore_eos in the request payload.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only compute and print theoretical estimates, do not send benchmark requests.",
    )
    args = parser.parse_args()
    if args.request_concurrency is None and args.concurrency is None:
        parser.error("one of --request-concurrency or --concurrency is required")
    if (
        args.request_concurrency is not None
        and args.concurrency is not None
        and args.request_concurrency != args.concurrency
    ):
        parser.error("--request-concurrency and --concurrency must match when both are set")
    if args.shared_prefix_tokens > args.initial_input_tokens:
        parser.error("--shared-prefix-tokens must be <= --initial-input-tokens")
    active_sessions = args.active_sessions or args.num_sessions
    if active_sessions > args.num_sessions:
        parser.error("--active-sessions must be <= --num-sessions")
    request_concurrency = args.request_concurrency or args.concurrency

    return BenchConfig(
        base_url=args.base_url.rstrip("/"),
        model=args.model,
        tokenizer=args.tokenizer or args.model,
        api_key=args.api_key,
        request_concurrency=request_concurrency,
        active_sessions=active_sessions,
        num_sessions=args.num_sessions,
        initial_input_tokens=args.initial_input_tokens,
        shared_prefix_tokens=args.shared_prefix_tokens,
        delta_input_tokens=args.delta_input_tokens,
        num_rounds=args.num_rounds,
        output_tokens=args.output_tokens,
        results_dir=args.results_dir,
        timeout=args.timeout,
        temperature=args.temperature,
        seed=args.seed,
        startup_ramp_seconds=args.startup_ramp_seconds,
        request_min_tokens=not args.no_min_tokens,
        request_ignore_eos=not args.no_ignore_eos,
        dry_run=args.dry_run,
    )


def render_chat_tokens(
    tokenizer: PreTrainedTokenizerBase, messages: list[dict[str, str]]
) -> list[int]:
    try:
        rendered = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
        )
    except (AttributeError, ValueError):
        joined = "\n".join(f"{message['role']}: {message['content']}" for message in messages)
        rendered = tokenizer.encode(joined + "\nassistant:", add_special_tokens=True)

    if isinstance(rendered, list) and rendered and isinstance(rendered[0], list):
        return list(rendered[0])
    return list(rendered)


def count_text_tokens(tokenizer: PreTrainedTokenizerBase, text: str) -> int:
    if not text:
        return 0
    return len(tokenizer.encode(text, add_special_tokens=False))


def common_prefix_length(left: list[int], right: list[int]) -> int:
    shared = 0
    for left_token, right_token in zip(left, right):
        if left_token != right_token:
            break
        shared += 1
    return shared


def build_theoretical_messages(
    session_id: int,
    round_id: int,
    config: BenchConfig,
    text_factory: TokenTextFactory,
) -> list[dict[str, str]]:
    private_initial_tokens = config.initial_input_tokens - config.shared_prefix_tokens
    messages = [
        {
            "role": "user",
            "content": text_factory.make_text_from_segments(
                [
                    (
                        config.shared_prefix_tokens,
                        f"shared initial prefix {config.shared_prefix_tokens}",
                    ),
                    (
                        private_initial_tokens,
                        f"session {session_id} private initial suffix {private_initial_tokens}",
                    ),
                ]
            ),
        }
    ]

    for prior_round in range(round_id):
        messages.append(
            {
                "role": "assistant",
                "content": text_factory.make_text(
                    config.output_tokens,
                    f"session {session_id} round {prior_round} assistant placeholder",
                ),
            }
        )
        messages.append(
            {
                "role": "user",
                "content": text_factory.make_text(
                    config.delta_input_tokens,
                    f"session {session_id} round {prior_round} private delta",
                ),
            }
        )

    return messages


def compute_theoretical_kv_cache_stats(
    config: BenchConfig,
    tokenizer: PreTrainedTokenizerBase,
) -> TheoreticalKvCacheStats:
    text_factory = TokenTextFactory(tokenizer)
    per_round_prompt_tokens: list[int] = []

    for round_id in range(config.num_rounds):
        messages = build_theoretical_messages(
            session_id=0,
            round_id=round_id,
            config=config,
            text_factory=text_factory,
        )
        per_round_prompt_tokens.append(len(render_chat_tokens(tokenizer, messages)))

    round0_cross_session_prefix_tokens = 0
    if config.num_sessions > 1:
        first_session_tokens = render_chat_tokens(
            tokenizer,
            build_theoretical_messages(
                session_id=0,
                round_id=0,
                config=config,
                text_factory=text_factory,
            ),
        )
        second_session_tokens = render_chat_tokens(
            tokenizer,
            build_theoretical_messages(
                session_id=1,
                round_id=0,
                config=config,
                text_factory=text_factory,
            ),
        )
        round0_cross_session_prefix_tokens = common_prefix_length(
            first_session_tokens,
            second_session_tokens,
        )

    per_round_reusable_tokens = []
    for round_id, prompt_tokens in enumerate(per_round_prompt_tokens):
        if round_id == 0:
            per_round_reusable_tokens.append(round0_cross_session_prefix_tokens)
        else:
            per_round_reusable_tokens.append(per_round_prompt_tokens[round_id - 1])

    active_request_upper_bound = min(
        config.request_concurrency,
        config.active_sessions,
        config.num_sessions,
    )
    active_session_upper_bound = min(config.active_sessions, config.num_sessions)
    per_round_peak_request_kv_tokens = [
        prompt_tokens + config.output_tokens for prompt_tokens in per_round_prompt_tokens
    ]
    per_round_peak_request_concurrency_kv_tokens = [
        peak_request_tokens * active_request_upper_bound
        for peak_request_tokens in per_round_peak_request_kv_tokens
    ]
    per_round_peak_active_sessions_kv_tokens = [
        peak_request_tokens * active_session_upper_bound
        for peak_request_tokens in per_round_peak_request_kv_tokens
    ]

    total_prompt_tokens = config.num_sessions * sum(per_round_prompt_tokens)
    total_reusable_tokens = 0
    if config.num_sessions > 1:
        total_reusable_tokens += (
            config.num_sessions - 1
        ) * round0_cross_session_prefix_tokens
    total_reusable_tokens += config.num_sessions * sum(per_round_reusable_tokens[1:])

    overall_hit_rate = (
        total_reusable_tokens / total_prompt_tokens if total_prompt_tokens > 0 else 0.0
    )

    steady_state_prompt_tokens = config.num_sessions * sum(per_round_prompt_tokens[1:])
    steady_state_reusable_tokens = config.num_sessions * sum(per_round_reusable_tokens[1:])
    steady_state_hit_rate = None
    if steady_state_prompt_tokens > 0:
        steady_state_hit_rate = steady_state_reusable_tokens / steady_state_prompt_tokens

    return TheoreticalKvCacheStats(
        per_round_prompt_tokens=per_round_prompt_tokens,
        per_round_reusable_tokens=per_round_reusable_tokens,
        per_round_peak_request_kv_tokens=per_round_peak_request_kv_tokens,
        per_round_peak_request_concurrency_kv_tokens=per_round_peak_request_concurrency_kv_tokens,
        per_round_peak_active_sessions_kv_tokens=per_round_peak_active_sessions_kv_tokens,
        round0_cross_session_prefix_tokens=round0_cross_session_prefix_tokens,
        total_prompt_tokens=total_prompt_tokens,
        total_reusable_tokens=total_reusable_tokens,
        overall_hit_rate=overall_hit_rate,
        steady_state_prompt_tokens=steady_state_prompt_tokens,
        steady_state_reusable_tokens=steady_state_reusable_tokens,
        steady_state_hit_rate=steady_state_hit_rate,
    )


def percentile(values: Iterable[float], p: float) -> float | None:
    sorted_values = sorted(values)
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = (len(sorted_values) - 1) * p
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return sorted_values[low]
    weight = rank - low
    return sorted_values[low] * (1 - weight) + sorted_values[high] * weight


def summarize(records: list[RequestMetric]) -> list[dict[str, Any]]:
    groups: dict[str, list[RequestMetric]] = {"all": records}
    for record in records:
        groups.setdefault(f"round_{record.round_id}", []).append(record)

    rows: list[dict[str, Any]] = []
    for group, group_records in sorted(groups.items()):
        successful = [record for record in group_records if record.error is None]
        ttft = [record.ttft_s for record in successful if record.ttft_s is not None]
        tpot = [record.tpot_s for record in successful if record.tpot_s is not None]
        latency = [record.latency_s for record in successful]
        throughput = [record.output_tokens_per_s for record in successful]
        rows.append(
            {
                "group": group,
                "requests": len(group_records),
                "errors": len(group_records) - len(successful),
                "input_tokens_mean": mean_or_none(
                    record.measured_input_tokens for record in successful
                ),
                "output_tokens_mean": mean_or_none(record.output_tokens for record in successful),
                "ttft_p50_s": percentile(ttft, 0.50),
                "ttft_p95_s": percentile(ttft, 0.95),
                "ttft_p99_s": percentile(ttft, 0.99),
                "tpot_p50_s": percentile(tpot, 0.50),
                "tpot_p95_s": percentile(tpot, 0.95),
                "tpot_p99_s": percentile(tpot, 0.99),
                "latency_p50_s": percentile(latency, 0.50),
                "latency_p95_s": percentile(latency, 0.95),
                "latency_p99_s": percentile(latency, 0.99),
                "throughput_p50_tok_s": percentile(throughput, 0.50),
                "throughput_p95_tok_s": percentile(throughput, 0.95),
                "throughput_p99_tok_s": percentile(throughput, 0.99),
            }
        )
    return rows


def mean_or_none(values: Iterable[float]) -> float | None:
    items = list(values)
    if not items:
        return None
    return statistics.fmean(items)


def build_round_metrics_rows(
    records: list[RequestMetric],
    summary_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    summary_by_round: dict[int, dict[str, Any]] = {}
    for row in summary_rows:
        group = row["group"]
        if isinstance(group, str) and group.startswith("round_"):
            summary_by_round[int(group.split("_", 1)[1])] = row

    per_round: dict[int, dict[str, list[float] | list[int]]] = {}
    for record in records:
        if record.error is not None or record.status_code != 200:
            continue
        bucket = per_round.setdefault(
            record.round_id,
            {
                "session_ids": [],
                "ttft_s": [],
                "tpot_s": [],
                "latency_s": [],
                "measured_input_tokens": [],
            },
        )
        bucket["session_ids"].append(record.session_id)
        bucket["ttft_s"].append(record.ttft_s if record.ttft_s is not None else 0.0)
        bucket["tpot_s"].append(record.tpot_s if record.tpot_s is not None else 0.0)
        bucket["latency_s"].append(record.latency_s)
        bucket["measured_input_tokens"].append(record.measured_input_tokens)

    rows: list[dict[str, Any]] = []
    for round_id in sorted(per_round):
        summary = summary_by_round.get(round_id)
        if summary is None:
            continue
        bucket = per_round[round_id]
        rows.append(
            {
                "round_id": round_id,
                "samples": len(bucket["ttft_s"]),
                "session_count": len(set(bucket["session_ids"])),
                "measured_input_tokens_min": min(bucket["measured_input_tokens"]),
                "measured_input_tokens_max": max(bucket["measured_input_tokens"]),
                "input_tokens_mean": summary["input_tokens_mean"],
                "ttft_min_s": min(bucket["ttft_s"]),
                "ttft_max_s": max(bucket["ttft_s"]),
                "ttft_p50_s": summary["ttft_p50_s"],
                "ttft_p95_s": summary["ttft_p95_s"],
                "tpot_min_s": min(bucket["tpot_s"]),
                "tpot_max_s": max(bucket["tpot_s"]),
                "tpot_p50_s": summary["tpot_p50_s"],
                "tpot_p95_s": summary["tpot_p95_s"],
                "latency_min_s": min(bucket["latency_s"]),
                "latency_max_s": max(bucket["latency_s"]),
            }
        )
    return rows


def write_round_metrics_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    fieldnames = [
        "round_id",
        "samples",
        "session_count",
        "measured_input_tokens_min",
        "measured_input_tokens_max",
        "input_tokens_mean",
        "ttft_min_s",
        "ttft_max_s",
        "ttft_p50_s",
        "ttft_p95_s",
        "tpot_min_s",
        "tpot_max_s",
        "tpot_p50_s",
        "tpot_p95_s",
        "latency_min_s",
        "latency_max_s",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def plot_round_metrics(
    rows: list[dict[str, Any]],
    config: BenchConfig,
    output_path: Path,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rounds = [row["round_id"] for row in rows]
    ttft_p50 = [row["ttft_p50_s"] for row in rows]
    ttft_p95 = [row["ttft_p95_s"] for row in rows]
    tpot_p50 = [row["tpot_p50_s"] for row in rows]
    tpot_p95 = [row["tpot_p95_s"] for row in rows]

    fig, axes = plt.subplots(2, 1, figsize=(11, 8.5), sharex=True, constrained_layout=True)
    colors = {
        "p50": "#c62828",
        "p95": "#ef6c00",
    }

    axes[0].plot(rounds, ttft_p50, marker="o", linewidth=2.2, color=colors["p50"], label="TTFT p50")
    axes[0].plot(rounds, ttft_p95, marker="s", linewidth=2.0, color=colors["p95"], label="TTFT p95")
    axes[1].plot(rounds, tpot_p50, marker="o", linewidth=2.2, color=colors["p50"], label="TPOT p50")
    axes[1].plot(rounds, tpot_p95, marker="s", linewidth=2.0, color=colors["p95"], label="TPOT p95")

    axes[0].set_ylabel("TTFT (s)")
    axes[1].set_ylabel("TPOT (s/token)")
    axes[1].set_xlabel("Round")
    axes[0].grid(True, alpha=0.25)
    axes[1].grid(True, alpha=0.25)
    axes[0].legend(loc="upper left")
    axes[1].legend(loc="upper left")

    title = "Multiturn round trend: TTFT / TPOT"
    subtitle_parts = [
        f"request_concurrency={config.request_concurrency}",
        f"active_sessions={config.active_sessions}",
        f"sessions={config.num_sessions}",
        f"input={config.initial_input_tokens}+round*{config.delta_input_tokens}",
        f"output={config.output_tokens}",
    ]
    title += "\n" + ", ".join(subtitle_parts)
    fig.suptitle(title, fontsize=14)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


async def run_session(
    session_id: int,
    config: BenchConfig,
    tokenizer: PreTrainedTokenizerBase,
    text_factory: TokenTextFactory,
    client: httpx.AsyncClient,
    request_semaphore: asyncio.Semaphore,
    active_session_semaphore: asyncio.Semaphore,
) -> list[RequestMetric]:
    async with active_session_semaphore:
        await stagger_initial_start(session_id, config)
        records: list[RequestMetric] = []
        private_initial_tokens = (
            config.initial_input_tokens - config.shared_prefix_tokens
        )
        messages = [
            {
                "role": "user",
                "content": text_factory.make_text_from_segments(
                    [
                        (
                            config.shared_prefix_tokens,
                            f"shared initial prefix {config.shared_prefix_tokens}",
                        ),
                        (
                            private_initial_tokens,
                            f"session {session_id} private initial suffix {private_initial_tokens}",
                        ),
                    ]
                ),
            }
        ]

        target_input = config.initial_input_tokens
        for round_id in range(config.num_rounds):
            measured_input = len(render_chat_tokens(tokenizer, messages))
            metric, assistant_text = await run_one_request(
                session_id=session_id,
                round_id=round_id,
                target_input_tokens=target_input,
                measured_input_tokens=measured_input,
                messages=messages,
                config=config,
                tokenizer=tokenizer,
                client=client,
                request_semaphore=request_semaphore,
            )
            records.append(metric)

            if metric.error is not None:
                break
            if round_id == config.num_rounds - 1:
                break

            messages.append({"role": "assistant", "content": assistant_text})
            target_input += config.delta_input_tokens
            messages.append(
                {
                    "role": "user",
                    "content": text_factory.make_text(
                        config.delta_input_tokens,
                        f"session {session_id} round {round_id} private delta",
                    ),
                }
            )

        return records


async def stagger_initial_start(session_id: int, config: BenchConfig) -> None:
    delay = startup_delay_seconds(session_id, config)
    if delay > 0:
        await asyncio.sleep(delay)


def startup_delay_seconds(session_id: int, config: BenchConfig) -> float:
    if config.startup_ramp_seconds <= 0:
        return 0.0

    ramp_slots = min(config.active_sessions, config.num_sessions)
    if ramp_slots <= 1:
        return 0.0
    if session_id >= ramp_slots:
        return 0.0

    slot = session_id
    return config.startup_ramp_seconds * slot / ramp_slots


async def run_one_request(
    *,
    session_id: int,
    round_id: int,
    target_input_tokens: int,
    measured_input_tokens: int,
    messages: list[dict[str, str]],
    config: BenchConfig,
    tokenizer: PreTrainedTokenizerBase,
    client: httpx.AsyncClient,
    request_semaphore: asyncio.Semaphore,
) -> tuple[RequestMetric, str]:
    payload: dict[str, Any] = {
        "model": config.model,
        "messages": messages,
        "stream": True,
        "max_tokens": config.output_tokens,
        "temperature": config.temperature,
    }
    if config.seed is not None:
        payload["seed"] = config.seed + session_id * 1000 + round_id
    if config.request_ignore_eos:
        payload["ignore_eos"] = True
    if config.request_min_tokens:
        payload["min_tokens"] = config.output_tokens

    first_token_time: float | None = None
    start: float | None = None
    status_code: int | None = None
    error: str | None = None
    chunks: list[str] = []

    async with request_semaphore:
        start = time.perf_counter()
        try:
            async with client.stream(
                "POST", "/chat/completions", json=payload, timeout=config.timeout
            ) as response:
                status_code = response.status_code
                response.raise_for_status()
                async for line in response.aiter_lines():
                    content = parse_sse_content(line)
                    if content is None:
                        continue
                    if content and first_token_time is None:
                        first_token_time = time.perf_counter()
                    chunks.append(content)
        except Exception as exc:  # noqa: BLE001 - record benchmark failures per request.
            error = f"{type(exc).__name__}: {exc}"

    end = time.perf_counter()
    if start is None:
        start = end
    assistant_text = "".join(chunks)
    output_tokens = count_text_tokens(tokenizer, assistant_text)
    latency = end - start
    ttft = None if first_token_time is None else first_token_time - start
    tpot = None
    if first_token_time is not None and output_tokens > 1:
        tpot = (end - first_token_time) / (output_tokens - 1)
    elif first_token_time is not None and output_tokens == 1:
        tpot = 0.0

    metric = RequestMetric(
        session_id=session_id,
        round_id=round_id,
        target_input_tokens=target_input_tokens,
        measured_input_tokens=measured_input_tokens,
        target_output_tokens=config.output_tokens,
        output_tokens=output_tokens,
        ttft_s=ttft,
        tpot_s=tpot,
        latency_s=latency,
        output_tokens_per_s=output_tokens / latency if latency > 0 else 0.0,
        status_code=status_code,
        error=error,
    )
    return metric, assistant_text


def parse_sse_content(line: str) -> str | None:
    if not line.startswith("data:"):
        return None
    data = line.removeprefix("data:").strip()
    if not data or data == "[DONE]":
        return None
    try:
        payload = json.loads(data)
    except json.JSONDecodeError:
        return None

    choices = payload.get("choices") or []
    if not choices:
        return None
    delta = choices[0].get("delta") or {}
    content = delta.get("content")
    if content is None:
        return None
    return str(content)


async def run_benchmark(config: BenchConfig) -> list[RequestMetric]:
    tokenizer = AutoTokenizer.from_pretrained(config.tokenizer, trust_remote_code=True)
    return await run_benchmark_with_tokenizer(config, tokenizer)


async def run_benchmark_with_tokenizer(
    config: BenchConfig,
    tokenizer: PreTrainedTokenizerBase,
) -> list[RequestMetric]:
    text_factory = TokenTextFactory(tokenizer)
    request_semaphore = asyncio.Semaphore(config.request_concurrency)
    active_session_semaphore = asyncio.Semaphore(config.active_sessions)

    headers = dict(JSON_HEADERS)
    if config.api_key:
        headers["authorization"] = f"Bearer {config.api_key}"

    async with httpx.AsyncClient(base_url=config.base_url, headers=headers) as client:
        session_tasks = [
            run_session(
                session_id=session_id,
                config=config,
                tokenizer=tokenizer,
                text_factory=text_factory,
                client=client,
                request_semaphore=request_semaphore,
                active_session_semaphore=active_session_semaphore,
            )
            for session_id in range(config.num_sessions)
        ]
        nested = await asyncio.gather(*session_tasks)

    return [record for session_records in nested for record in session_records]


def write_results(config: BenchConfig, records: list[RequestMetric]) -> ResultArtifacts:
    config.results_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    jsonl_path = config.results_dir / f"requests-{stamp}.jsonl"
    summary_csv_path = config.results_dir / f"summary-{stamp}.csv"

    with jsonl_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")

    summary_rows = summarize(records)
    with summary_csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    round_metrics_rows = build_round_metrics_rows(records, summary_rows)
    round_metrics_csv_path: Path | None = None
    round_metrics_png_path: Path | None = None
    if round_metrics_rows:
        round_metrics_csv_path = config.results_dir / "round_metrics.csv"
        write_round_metrics_csv(round_metrics_rows, round_metrics_csv_path)
        round_metrics_png_path = config.results_dir / "round_metrics.png"
        plot_round_metrics(round_metrics_rows, config, round_metrics_png_path)

    return ResultArtifacts(
        jsonl_path=jsonl_path,
        summary_csv_path=summary_csv_path,
        round_metrics_csv_path=round_metrics_csv_path,
        round_metrics_png_path=round_metrics_png_path,
    )


def format_value(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def format_k_tokens(tokens: int) -> str:
    return f"{tokens / 1000.0:.2f}K"


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def render(cells: list[str]) -> str:
        return " | ".join(cell.ljust(widths[index]) for index, cell in enumerate(cells))

    print(render(headers))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(render(row))


def print_summary(records: list[RequestMetric], artifacts: ResultArtifacts) -> None:
    rows = summarize(records)
    all_row = next(row for row in rows if row["group"] == "all")
    print("Benchmark complete")
    print(f"Requests: {all_row['requests']}  Errors: {all_row['errors']}")
    print(
        "TTFT p50/p95/p99: "
        f"{format_value(all_row['ttft_p50_s'])}/"
        f"{format_value(all_row['ttft_p95_s'])}/"
        f"{format_value(all_row['ttft_p99_s'])} s"
    )
    print(
        "TPOT p50/p95/p99: "
        f"{format_value(all_row['tpot_p50_s'])}/"
        f"{format_value(all_row['tpot_p95_s'])}/"
        f"{format_value(all_row['tpot_p99_s'])} s"
    )
    print(
        "Latency p50/p95/p99: "
        f"{format_value(all_row['latency_p50_s'])}/"
        f"{format_value(all_row['latency_p95_s'])}/"
        f"{format_value(all_row['latency_p99_s'])} s"
    )
    print(f"Per-request JSONL: {artifacts.jsonl_path}")
    print(f"Aggregate CSV: {artifacts.summary_csv_path}")
    if artifacts.round_metrics_csv_path is not None:
        print(f"Round metrics CSV: {artifacts.round_metrics_csv_path}")
    if artifacts.round_metrics_png_path is not None:
        print(f"Round metrics PNG: {artifacts.round_metrics_png_path}")


def print_theoretical_kv_cache_stats(
    config: BenchConfig,
    stats: TheoreticalKvCacheStats,
) -> None:
    print("Theoretical KV cache hit rate before load")
    print(
        "Definition: token-level prefix reuse upper bound during prefill; "
        "actual runtime can be lower."
    )
    print(
        "Assumptions: prefix cache enabled, reusable KV not evicted, "
        "no block-alignment/hash loss, assistant output length ~= --output-tokens."
    )
    print(
        "Note: round0 reusable prefix is measured on the fully rendered prompt, so it may "
        "be larger than --shared-prefix-tokens because chat template tokens and fixed prompt "
        "headers also contribute."
    )
    if not config.request_min_tokens or not config.request_ignore_eos:
        print(
            "Note: current request payload does not force full output length; "
            "later-round actual hit rate may deviate from this nominal estimate."
        )

    table_rows: list[list[str]] = []
    for round_id, prompt_tokens in enumerate(stats.per_round_prompt_tokens):
        reusable_tokens = stats.per_round_reusable_tokens[round_id]
        peak_request_kv_tokens = stats.per_round_peak_request_kv_tokens[round_id]
        peak_request_concurrency_kv_tokens = (
            stats.per_round_peak_request_concurrency_kv_tokens[round_id]
        )
        peak_active_sessions_kv_tokens = (
            stats.per_round_peak_active_sessions_kv_tokens[round_id]
        )
        hit_rate = reusable_tokens / prompt_tokens if prompt_tokens > 0 else 0.0
        table_rows.append(
            [
                str(round_id),
                str(prompt_tokens),
                str(reusable_tokens),
                f"{hit_rate:.2%}",
                f"{peak_request_kv_tokens} ({format_k_tokens(peak_request_kv_tokens)})",
                (
                    f"{peak_request_concurrency_kv_tokens} "
                    f"({format_k_tokens(peak_request_concurrency_kv_tokens)})"
                ),
                (
                    f"{peak_active_sessions_kv_tokens} "
                    f"({format_k_tokens(peak_active_sessions_kv_tokens)})"
                ),
            ]
        )
    print_table(
        [
            "round",
            "prompt_tokens",
            "reusable_tokens",
            "nominal_hit_rate",
            "peak_kv/request",
            "peak_kv@req_conc",
            "peak_kv@active_sess",
        ],
        table_rows,
    )

    print(
        "Round0 cross-session common prefix upper bound: "
        f"{stats.round0_cross_session_prefix_tokens} tokens"
    )
    print(
        "Peak KV estimate definition: prompt_tokens + --output-tokens per request."
    )
    print(
        "Peak KV @ request concurrency upper bound multiplies by "
        "min(request_concurrency, active_sessions, num_sessions)="
        f"{min(config.request_concurrency, config.active_sessions, config.num_sessions)}."
    )
    print(
        "Peak KV @ active sessions upper bound multiplies by "
        f"min(active_sessions, num_sessions)={min(config.active_sessions, config.num_sessions)}."
    )
    print(
        "Overall cold-start upper bound: "
        f"{stats.total_reusable_tokens}/{stats.total_prompt_tokens} "
        f"({stats.overall_hit_rate:.2%})"
    )
    if stats.steady_state_hit_rate is not None:
        print(
            "Steady-state rounds>=1 upper bound: "
            f"{stats.steady_state_reusable_tokens}/{stats.steady_state_prompt_tokens} "
            f"({stats.steady_state_hit_rate:.2%})"
        )
    print("")


def main() -> None:
    config = parse_args()
    tokenizer = AutoTokenizer.from_pretrained(config.tokenizer, trust_remote_code=True)
    theoretical_stats = compute_theoretical_kv_cache_stats(config, tokenizer)
    print_theoretical_kv_cache_stats(config, theoretical_stats)
    if config.dry_run:
        print("Dry run complete")
        print("No benchmark requests were sent")
        return
    records = asyncio.run(run_benchmark_with_tokenizer(config, tokenizer))
    artifacts = write_results(config, records)
    print_summary(records, artifacts)


if __name__ == "__main__":
    main()