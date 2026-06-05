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
    "config/workflow_manifest.json",
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
        lock = Path("reports/official_docs_lock.md")
        if not lock.exists():
            return ["reports/official_docs_lock.md is required before execution-stage reporting"]
        text = read_text(lock).lower()
        required_terms = [
            "source",
            "type",
            "url",
            "version",
            "command",
            "project command",
            "difference",
            "uncertainty",
        ]
        missing = [term for term in required_terms if term not in text]
        if missing:
            return [f"reports/official_docs_lock.md missing command-alignment fields: {', '.join(missing)}"]
        auxiliary_count = len(re.findall(r"\b(auxiliary|community)\b", text))
        official_count = len(re.findall(r"\b(official docs|official repo|model card|user provided)\b", text))
        if official_count == 0 and auxiliary_count > 0:
            return ["reports/official_docs_lock.md cannot rely only on auxiliary/community sources"]
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


def check_active_run_lock() -> list[str]:
    lock = Path(".codex_runtime/active_benchmark_run.json")
    if not lock.exists():
        return []
    try:
        data = json.loads(read_text(lock))
    except json.JSONDecodeError:
        return [".codex_runtime/active_benchmark_run.json is invalid; clear or repair the active run lock before final response"]
    status = str(data.get("status", "active")).lower()
    if status in {"done", "completed", "released"}:
        return []
    if data.get("parallel_allowed") is True and data.get("user_requested_stacked_load") is True:
        return []
    return [
        ".codex_runtime/active_benchmark_run.json indicates an active benchmark; finish/release it before starting or finalizing comparable workload results"
    ]


def is_required_task(task: dict) -> bool:
    return bool(task.get("required") or task.get("approved"))


def task_status(task: dict) -> str:
    return str(task.get("status", "")).strip().lower()


def task_id(stage: dict, task: dict) -> str:
    return str(task.get("id") or f"stage{stage.get('stage', '?')}_{task.get('description', 'task')}")


def task_path_exists(value: object) -> list[str]:
    missing: list[str] = []
    if isinstance(value, str):
        if value and not Path(value).exists():
            missing.append(value)
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, str) and item and not Path(item).exists():
                missing.append(item)
    return missing


def iter_manifest_tasks(manifest: dict):
    for stage in manifest.get("stages", []):
        if not isinstance(stage, dict):
            continue
        for task in stage.get("tasks", []):
            if isinstance(task, dict):
                yield stage, task


def check_workflow_manifest(enforce_required: bool) -> tuple[list[str], list[dict]]:
    manifest_path = Path("config/workflow_manifest.json")
    if not manifest_path.exists():
        return (["config/workflow_manifest.json is missing"], [])
    try:
        manifest = json.loads(read_text(manifest_path))
    except json.JSONDecodeError as exc:
        return ([f"config/workflow_manifest.json is invalid JSON: {exc}"], [])

    errors: list[str] = []
    remaining: list[dict] = []
    serial_required = manifest.get("serial_benchmark_required")
    if serial_required is not True:
        errors.append("config/workflow_manifest.json must set serial_benchmark_required=true")

    for stage, task in iter_manifest_tasks(manifest):
        required = is_required_task(task)
        status = task_status(task)
        plan_only = bool(task.get("plan_only"))
        completed = status in {"completed", "complete", "success", "canonical", "skipped", "blocked"}
        tid = task_id(stage, task)

        if enforce_required and required and not completed:
            remaining.append(
                {
                    "stage": stage.get("stage"),
                    "task": tid,
                    "status": status or "missing",
                    "next_action": task.get("description") or "complete this required task",
                }
            )
            continue

        if required and status == "skipped" and not str(task.get("blocked_reason", "")).strip():
            errors.append(f"{tid} is skipped without blocked_reason or user-accepted reason")
        if required and status == "blocked" and not str(task.get("blocked_reason", "")).strip():
            errors.append(f"{tid} is blocked without blocked_reason")

        if status in {"completed", "complete", "success", "canonical"}:
            missing_paths: list[str] = []
            for path_value in task.get("artifact_paths", []):
                missing_paths.extend(task_path_exists(path_value))

            evidence = task.get("evidence", {})
            if isinstance(evidence, dict):
                for key, value in evidence.items():
                    if key in {"run_id", "notes"}:
                        continue
                    missing_paths.extend(task_path_exists(value))
                execution_keys = {"command_file", "raw_log", "serve_log", "client_log", "log_extract", "metrics"}
                requires_execution = any(key in evidence for key in execution_keys)
                if requires_execution and not plan_only:
                    if not str(evidence.get("run_id", "")).strip() and "run_id" in evidence:
                        errors.append(f"{tid} missing run_id in evidence")
                    for key in ("command_file", "log_extract", "metrics"):
                        if key in evidence and not str(evidence.get(key, "")).strip():
                            errors.append(f"{tid} missing evidence.{key}")
                    if not any(str(evidence.get(key, "")).strip() for key in ("raw_log", "serve_log", "client_log")) and any(
                        key in evidence for key in ("raw_log", "serve_log", "client_log")
                    ):
                        errors.append(f"{tid} missing raw_log/serve_log/client_log evidence")
            elif not plan_only:
                errors.append(f"{tid} evidence must be an object")

            for path in sorted(set(missing_paths)):
                errors.append(f"{tid} missing artifact/evidence path: {path}")

    if remaining:
        errors.append(f"{len(remaining)} required/approved task(s) remain unfinished")
    return errors, remaining


def check_final_deliverables(paths: list[str], stage_requires_docs: bool) -> list[str]:
    final_touched = any(path.startswith(("reports/final", "results/canonical", "figures/final")) for path in paths)
    state_final = False
    state_path = Path(".codex_runtime/kv_workflow_state.json")
    if state_path.exists():
        try:
            state = json.loads(read_text(state_path))
            state_final = int(state.get("stage", 0) or 0) >= 10 or str(state.get("phase", "")).lower() in {"final", "report", "review_fix"}
        except (json.JSONDecodeError, TypeError, ValueError):
            state_final = False
    if not final_touched and not state_final:
        return []

    errors: list[str] = []
    required = [
        "reports/final_deployment_card.md",
        "reports/final_report.md",
        "results/canonical/final_launch_command.sh",
        "results/canonical/final_metrics.json",
        "results/canonical/run_manifest.yaml",
    ]
    for item in required:
        if not Path(item).exists():
            errors.append(f"final workflow check missing {item}")
    if not Path("reports/final_report.pdf").exists() and not Path("reports/final_report_pdf_dependency_missing.md").exists():
        errors.append("final workflow check missing reports/final_report.pdf or reports/final_report_pdf_dependency_missing.md")
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
    errors.extend(check_active_run_lock())
    manifest_errors, remaining_tasks = check_workflow_manifest(enforce_required=stage_requires_docs or active)
    errors.extend(manifest_errors)
    errors.extend(check_final_deliverables(paths, stage_requires_docs))

    if errors:
        details = {"trigger": active_reason or diff_reason, "errors": errors}
        if remaining_tasks:
            details["remaining_tasks"] = remaining_tasks
        return emit(
            False,
            "KV workflow stop check failed. Re-read AGENTS.md, PROCESS.md, prompts/12_GUARDRAILS_HOOKS_AND_BUDGETS.md, prompts/15_STOP_HOOK_AND_COMMIT_CHECKS.md, and prompts/16_REAL_EXECUTION_EVIDENCE.md; fix blocking evidence, canonical, report, figure, PROCESS, or source-edit issues before final response.",
            details,
        )

    return emit(
        True,
        "KV workflow stop check passed. Final response should cite user-facing reports/figures and avoid raw logs.",
        {"trigger": active_reason or diff_reason},
    )


if __name__ == "__main__":
    raise SystemExit(main())
