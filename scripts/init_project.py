#!/usr/bin/env python3
"""Initialize a project for the LLM serving KV diagnostics skill."""

from __future__ import annotations

import argparse
import datetime as dt
import shutil
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
ASSETS = SKILL_DIR / "assets"
REFERENCES = SKILL_DIR / "references"

HOOKS_JSON = """{
  "hooks": {
    "Stop": [
      {
        "command": "python .codex/hooks/stop_kv_check.py"
      }
    ]
  }
}
"""

AGENTS_MD = """# AGENTS.md

## 一句话目标

执行单节点 LLM serving / KV cache 诊断 workflow：基于官方文档、真实运行日志、KV pressure workload 和 canonical 数据，给出可复现部署结论。

## 当前阶段读取规则

只读取当前阶段 prompt 与必要横向规范。不要一次性加载所有 prompt。

必读：

```text
README.md
PROCESS.md
prompts/00_WORKFLOW_MAP.md
prompts/00_ROLE_AND_RESEARCH_TASTE.md
prompts/12_GUARDRAILS_HOOKS_AND_BUDGETS.md
config/workflow_manifest.json
当前阶段 prompt
```

按需读：

```text
prompts/11_LOG_EXTRACTION_AND_PERSISTENCE.md
prompts/13_INTERACTION_READABILITY_AND_TERMS.md
prompts/14_DATA_UNIQUENESS_AND_CANONICALIZATION.md
prompts/15_STOP_HOOK_AND_COMMIT_CHECKS.md
prompts/16_REAL_EXECUTION_EVIDENCE.md
PLOT_STYLE.md
hooks/*
```

## 不可越界

- 不修改推理引擎源码、site-packages 中的 engine 代码、vendor runtime 代码。
- 不把失败/无效结果写入 `results/canonical/`。
- 不把大段 raw log 粘贴到 report。
- 不在未完成 smoke test 时运行 benchmark。
- 不在 prefix cache 未确认命中时评价 LMCache 收益。
- 不在没有真实执行证据时标记执行类任务完成。
- 不并发运行多个 benchmark/workload/trial 来生成可比结果。
- 不把 Mooncake 当作默认必做项；只有用户明确启用 multi-node/offload extension 时才进入 scope。

## 输出规范

- 用户 md 使用中文。
- 图和表使用 academic English。
- 图必须保存为 png 并插入 md。
- 每个实验必须写清楚 Question、Bottleneck、Mechanism、Evidence、Contribution、Decision。
- 每个术语首次出现给一句话解释。

## Stop 前检查

如果当前任务是执行阶段，且修改了 `experiments/`、`runs/`、`results/`、`reports/`、`figures/` 任一目录，必须通过 `.codex/hooks/stop_kv_check.py`。纯讨论、纯规划、只编辑 prompt 文档时不触发重型检查。

Stop 前必须读取 `config/workflow_manifest.json`。如果 required/approved 子任务仍未完成，或 completed execution task 缺少 command、run_id、log extract、metrics、report、必要 figure，继续补跑或补产物，不要 final。

## 最终交付

用户主要阅读：

```text
reports/final_report.md
reports/final_report.pdf
reports/final_deployment_card.md
```

如果 PDF renderer 缺失，保留 `reports/final_report.md`，并写 `reports/final_report_pdf_dependency_missing.md`。
"""

README_MD = """# LLM Serving KV Diagnostics

## 当前目标

单节点 LLM serving / KV cache 诊断。

## 如何运行

1. 填写 `config/workflow.yaml`。
2. 检查 `config/workflow_manifest.json`，确认 Stage 1-10 子任务、required 状态和 plan-only 例外。
3. 运行 Stage 1 锁定官方文档和 scope。
4. 按 `prompts/00_WORKFLOW_MAP.md` 顺序执行。
5. 每阶段只读当前阶段 prompt 和必要横向规范。
6. 执行阶段 stop 前运行 `.codex/hooks/stop_kv_check.py`。

## 用户主要查看

```text
reports/final_report.md
reports/final_report.pdf
reports/final_deployment_card.md
reports/official_docs_lock.md
reports/basic-info.md
reports/workload_sizing.md
reports/baseline_kv_behavior.md
reports/parallelism_decision.md
reports/offload_decision.md
reports/parameter_decision.md
PROCESS.md
```

`reports/final_report.md` 是主要阅读入口，正文中文，按 Stage 1-10 组织，只引用 canonical 数据、关键表和关键 png。若缺少 PDF 渲染工具，保留 Markdown，并生成 `reports/final_report_pdf_dependency_missing.md` 说明缺失依赖。

## 原始数据

raw log 在 `runs/raw/`，失败/无效运行的必要摘要在 `runs/scratch_failed/`，最终有效结果在 `results/canonical/`。

## 执行规则

- 继续执行时先看 `config/workflow_manifest.json`，不要只完成少数子任务就宣称完成。
- 每个完成的执行类任务必须记录 run_id、command、log extract、metrics、report 和必要 png。
- benchmark/workload/trial 默认串行执行；不要并发运行多个 workload 污染可比性。
- Mooncake 不是默认主流程；只有用户明确启用 multi-node/offload extension 时才进入 scope。
"""

PROCESS_MD = """# PROCESS.md

- 初始化：项目采用单节点 LLM serving / KV cache 诊断 workflow；后续每个阶段结束或 commit 追加 1-3 条可复用经验，最多保留 20 条。
"""

WORKFLOW_YAML = """engine: vllm
backend: cuda_or_cann
container: ""
model_path: ""
model_alias: ""
base_url: "http://127.0.0.1:8000/v1"
base_launch_command: ""

skip:
  engine_acquisition: true
  model_download: true
  lmcache: false
  mooncake: true
  parallelism_comparison: false

docs:
  require_official_docs_lock: true
  require_launch_command_alignment: true

execution:
  serial_benchmark_required: true
  allow_parallel_stacked_load_only_when_user_requested: true
  active_run_lock: ".codex_runtime/active_benchmark_run.json"

manifest:
  path: "config/workflow_manifest.json"

budgets:
  smoke_launch_max_attempts: 3
  single_request_max_attempts: 3
  parallelism_configs_max: 3
  lmcache_bringup_max_attempts: 3
  mooncake_bringup_max_attempts: 3
  parameter_trial_max: 6
  single_bottleneck_trial_max: 3

paths:
  multi_turn_py: "multi-turn.py"
  reports_dir: "reports"
  figures_dir: "figures"
  attempts_dir: "runs/attempts"
  raw_runs_dir: "runs/raw"
  failed_runs_dir: "runs/scratch_failed"
  canonical_dir: "results/canonical"
  plot_style: "PLOT_STYLE.md"
"""

GITIGNORE_BLOCK = """# LLM serving KV diagnostics
runs/attempts/
runs/raw/
runs/scratch_failed/
*.log
*.out
*.err
*.tmp
*.bak
__pycache__/
*.pyc
.pytest_cache/
.codex_runtime/
"""


def write_file(path: Path, content: str, force: bool, changed: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8", errors="replace") == content:
        return
    if path.exists() and not force:
        backup = path.with_suffix(path.suffix + f".bak.{dt.datetime.now().strftime('%Y%m%d%H%M%S')}")
        shutil.copy2(path, backup)
    path.write_text(content, encoding="utf-8", newline="\n")
    changed.append(str(path))


def copy_file(src: Path, dest: Path, force: bool, changed: list[str]) -> None:
    write_file(dest, src.read_text(encoding="utf-8", errors="replace"), force, changed)


def copy_tree_files(src_dir: Path, dest_dir: Path, force: bool, changed: list[str]) -> None:
    for src in src_dir.rglob("*"):
        if src.is_file():
            copy_file(src, dest_dir / src.relative_to(src_dir), force, changed)


def append_block(path: Path, marker: str, block: str, changed: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    if marker in existing:
        return
    prefix = existing.rstrip() + "\n\n" if existing.strip() else ""
    path.write_text(prefix + block.rstrip() + "\n", encoding="utf-8", newline="\n")
    changed.append(str(path))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--force", action="store_true", help="overwrite managed workflow files")
    parser.add_argument("--no-copy-multi-turn", action="store_true", help="do not copy bundled multi-turn.py")
    args = parser.parse_args()

    project = args.project.resolve()
    project.mkdir(parents=True, exist_ok=True)
    changed: list[str] = []

    for directory in [
        "config",
        "prompts",
        "hooks",
        "templates",
        "experiments",
        "instrumentation",
        "runs/attempts",
        "runs/raw",
        "runs/scratch_failed",
        "results/canonical",
        "reports",
        "figures",
        ".codex/hooks",
    ]:
        (project / directory).mkdir(parents=True, exist_ok=True)

    write_file(project / "AGENTS.md", AGENTS_MD, args.force, changed)
    write_file(project / "README.md", README_MD, args.force, changed)
    write_file(project / "PROCESS.md", PROCESS_MD, args.force, changed)
    write_file(project / "config" / "workflow.yaml", WORKFLOW_YAML, args.force, changed)
    copy_file(ASSETS / "templates" / "WORKFLOW_MANIFEST_TEMPLATE.json", project / "config" / "workflow_manifest.json", args.force, changed)
    copy_file(REFERENCES / "matplotlib_paper_style.md", project / "PLOT_STYLE.md", args.force, changed)

    copy_tree_files(REFERENCES / "prompts", project / "prompts", args.force, changed)
    copy_tree_files(REFERENCES / "hooks_specs", project / "hooks", args.force, changed)
    copy_tree_files(ASSETS / "templates", project / "templates", args.force, changed)

    if not args.no_copy_multi_turn:
        copy_file(ASSETS / "multi-turn.py", project / "multi-turn.py", args.force, changed)

    copy_file(ASSETS / "project_hooks" / "stop_kv_check.py", project / ".codex" / "hooks" / "stop_kv_check.py", args.force, changed)
    write_file(project / ".codex" / "hooks.json", HOOKS_JSON, args.force, changed)
    append_block(project / ".gitignore", "# LLM serving KV diagnostics", GITIGNORE_BLOCK, changed)

    print("Initialized LLM serving KV diagnostics project.")
    print(f"Project: {project}")
    print("Changed files:")
    for item in changed:
        print(f"- {item}")
    print("Next: run /hooks in Codex inside this project to inspect and trust .codex/hooks/stop_kv_check.py.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
