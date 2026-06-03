#!/usr/bin/env python3
"""Codex Stop hook for the LLM serving KV diagnostics workflow."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


WATCHED_PREFIXES = (
    "experiments/",
    "runs/",
    "results/",
    "reports/",
    "figures/",
)

BLOCKED_PREFIXES = (
    "vllm/",
    "sglang/",
    "lmcache/",
    "mooncake/",
    "transformers/",
    "torch/",
    "flashinfer/",
    "site-packages/vllm",
    "site-packages/sglang",
    "site-packages/lmcache",
    "site-packages/transformers",
    "site-packages/torch",
)


def emit(allow: bool, reason: str, details: dict | None = None) -> int:
    payload = {
        "allow": allow,
        "decision": "allow" if allow else "block",
        "reason": reason,
    }
    if details:
        payload["details"] = details
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if allow else 1


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="replace")
    except FileNotFoundError:
        return ""


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=False)


def git_paths(args: list[str]) -> list[str]:
    result = run(["git", *args])
    if result.returncode != 0:
        return []
    return [line.replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def changed_paths() -> list[str]:
    paths = set(git_paths(["diff", "--name-only", "HEAD"]))
    paths.update(git_paths(["diff", "--cached", "--name-only"]))
    paths.update(git_paths(["ls-files", "--others", "--exclude-standard"]))
    return sorted(paths)


def state_requests_check() -> tuple[bool, str, bool]:
    state_path = Path(".codex_runtime/kv_workflow_state.json")
    if not state_path.exists():
        return False, "", False
    try:
        state = json.loads(read_text(state_path))
    except json.JSONDecodeError:
        return True, "kv_workflow_state.json is invalid, run checks", True
    try:
        stage = int(state.get("stage", 0))
    except (TypeError, ValueError):
        stage = 0
    if state.get("workflow_active") is True:
        return True, "workflow_active=true", stage >= 2
    if stage >= 2:
        return True, f"stage={state.get('stage')}", True
    if state.get("phase") in {"execute", "review_fix", "rerun"}:
        return True, f"phase={state.get('phase')}", stage >= 2
    return False, "", False


def diff_requests_check(paths: list[str]) -> tuple[bool, str]:
    for path in paths:
        if path.startswith(WATCHED_PREFIXES):
            return True, f"diff touches {path}"
    return False, ""


def check_no_source_edits(paths: list[str]) -> list[str]:
    return [path for path in paths if path.startswith(BLOCKED_PREFIXES)]


def check_process() -> list[str]:
    errors: list[str] = []
    process = Path("PROCESS.md")
    if not process.exists():
        return ["PROCESS.md is missing"]
    bullet_count = sum(1 for line in read_text(process).splitlines() if re.match(r"^\s*(-|\d+\.)\s+", line))
    if bullet_count > 20:
        errors.append(f"PROCESS.md has {bullet_count} bullets; compact to <= 20")
    return errors


def check_official_docs(paths: list[str], stage_requires_docs: bool) -> list[str]:
    if stage_requires_docs or any(path.startswith(("experiments/", "runs/", "results/", "reports/")) for path in paths):
        if not Path("reports/official_docs_lock.md").exists():
            return ["reports/official_docs_lock.md is required before execution-stage reporting"]
    return []


def check_long_logs_in_reports() -> list[str]:
    errors: list[str] = []
    for report in Path("reports").glob("*.md"):
        lines = read_text(report).splitlines()
        in_fence = False
        streak = 0
        max_streak = 0
        for line in lines:
            if line.strip().startswith("```"):
                in_fence = not in_fence
                streak = 0
                continue
            looks_log_like = bool(re.search(r"(INFO|ERROR|WARN|DEBUG|Traceback|Exception|\[\d{2}:\d{2}:\d{2}\])", line))
            if in_fence and looks_log_like:
                streak += 1
                max_streak = max(max_streak, streak)
            elif line.strip():
                streak = 0
        if max_streak > 40:
            errors.append(f"{report.as_posix()} appears to paste >40 consecutive log-like lines")
    return errors


def check_canonical() -> list[str]:
    canonical = Path("results/canonical")
    if not canonical.exists() or not any(canonical.iterdir()):
        return []
    required_any = [
        ("final launch command", ["final_launch_command.sh", "launch_command.sh", "command.sh"]),
        ("metrics", ["final_metrics.json", "metrics.json", "summary.json"]),
        ("run manifest", ["run_manifest.yaml", "run_manifest.yml", "manifest.yaml"]),
    ]
    errors: list[str] = []
    names = {path.name for path in canonical.iterdir() if path.is_file()}
    for label, candidates in required_any:
        if not any(name in names for name in candidates):
            errors.append(f"results/canonical missing {label}: one of {', '.join(candidates)}")
    return errors


def check_figures_embedded() -> list[str]:
    figures = list(Path("figures").glob("*.png"))
    if not figures:
        return []
    reports_text = "\n".join(read_text(report) for report in Path("reports").glob("*.md"))
    errors = []
    for figure in figures:
        if figure.name not in reports_text and figure.as_posix() not in reports_text:
            errors.append(f"{figure.as_posix()} is not referenced by reports/*.md")
    return errors


def main() -> int:
    if not Path("AGENTS.md").exists():
        return emit(True, "AGENTS.md not found; skip KV workflow stop check")

    paths = changed_paths()
    active, active_reason, stage_requires_docs = state_requests_check()
    changed, diff_reason = diff_requests_check(paths)
    if not active and not changed:
        return emit(True, "not in KV execution/review stage and no watched workflow diff; skip heavy checks")

    errors: list[str] = []
    blocked = check_no_source_edits(paths)
    if blocked:
        errors.append("forbidden source edits: " + ", ".join(blocked))
    errors.extend(check_official_docs(paths, stage_requires_docs))
    errors.extend(check_process())
    errors.extend(check_long_logs_in_reports())
    errors.extend(check_canonical())
    errors.extend(check_figures_embedded())

    if errors:
        return emit(
            False,
            "KV workflow stop check failed. Re-read AGENTS.md, PROCESS.md, prompts/12_GUARDRAILS_HOOKS_AND_BUDGETS.md, prompts/15_STOP_HOOK_AND_COMMIT_CHECKS.md, and prompts/16_REAL_EXECUTION_EVIDENCE.md; fix blocking evidence, canonical, report, figure, PROCESS, or source-edit issues before final response.",
            {"trigger": active_reason or diff_reason, "errors": errors},
        )

    return emit(
        True,
        "KV workflow stop check passed. Final response should cite user-facing reports/figures and avoid raw logs.",
        {"trigger": active_reason or diff_reason},
    )


if __name__ == "__main__":
    raise SystemExit(main())
