---
name: llm-serving-kv-diagnostics
description: Initialize and operate a single-node LLM serving and KV cache diagnostic workflow for vLLM/SGLang-style deployments. Use when Codex needs to bootstrap a project with prompts, templates, multi-turn.py, project-level Codex Stop hooks, evidence checks, plotting rules, and staged experiments for smoke bring-up, KV capacity estimation, prefix cache validation, baseline load tests, parallelism comparison, LMCache/offload evaluation, parameter tuning, and final deployment reporting.
---

# LLM Serving KV Diagnostics

## Core Model

Use this skill for a single-node, KV-pressure-driven LLM serving diagnostic workflow. The goal is not a generic benchmark harness; it is a reproducible deployment investigation that answers whether an engine/model/hardware stack can start reliably, fit the intended KV cache workload, hit prefix cache, benefit from offload, and keep or reject a small number of tuning choices.

Skill installation only makes these instructions and resources available to Codex. Project hooks are not installed automatically by the skill loader. When the user asks to initialize or bootstrap a target project, run the initializer below to create project-level files and hooks.

## Initialize A Project

Run this from any Codex session after the skill is available:

```bash
python <skill_dir>/scripts/init_project.py --project <project_root>
```

Use `--force` only when the user explicitly allows replacing managed files. By default, existing files are preserved by writing `.bak.<timestamp>` backups before replacement.

The initializer creates or updates:

```text
AGENTS.md
README.md
PROCESS.md
PLOT_STYLE.md
config/workflow.yaml
prompts/
hooks/
templates/
experiments/
instrumentation/
runs/attempts/
runs/raw/
runs/scratch_failed/
results/canonical/
reports/
figures/
.codex/hooks.json
.codex/hooks/stop_kv_check.py
multi-turn.py
```

After initialization, tell the user to run `/hooks` in Codex inside the target project and inspect/trust the project Stop hook. Do not start vLLM, run benchmarks, or modify engine source during initialization.

## Operating Workflow

Read only the material needed for the current stage. Start with:

```text
prompts/README.md
AGENTS.md
PROCESS.md
prompts/00_WORKFLOW_MAP.md
prompts/00_ROLE_AND_RESEARCH_TASTE.md
prompts/12_GUARDRAILS_HOOKS_AND_BUDGETS.md
current stage prompt
```

Then load horizontal references only when needed:

```text
prompts/11_LOG_EXTRACTION_AND_PERSISTENCE.md
prompts/13_INTERACTION_READABILITY_AND_TERMS.md
prompts/14_DATA_UNIQUENESS_AND_CANONICALIZATION.md
prompts/15_STOP_HOOK_AND_COMMIT_CHECKS.md
prompts/16_REAL_EXECUTION_EVIDENCE.md
references/matplotlib_paper_style.md
references/hooks_specs/*
```

Main stages:

```text
1. Official Docs & Scope Lock
2. Environment & Stack Locking
3. Engine Smoke Bring-up
4. Model Memory & KV Cache Estimate
5. Workload Sizing with multi-turn.py
6. Baseline KV-oriented Load Test
7. Parallelism Comparison
8. KV Cache Offload Extension
9. Targeted vLLM Parameter Tuning
10. Final Deployment Report
```

## Hard Rules

Do not modify vLLM, SGLang, LMCache, Mooncake, Transformers, Torch, FlashInfer, site-packages engine code, or vendor runtime source. If profiling needs a hack, add a switchable and reversible monkey patch under `instrumentation/` and document its risk.

Use official docs as the first source for deployment, tuning, and offload behavior. Community posts can support but cannot replace official documentation.

Persist all service logs to files. Reports should cite extracted metrics and raw log paths, not paste long logs.

Only validated successful runs may enter `results/canonical/`. Failed or invalid runs belong in `runs/scratch_failed/` or candidate locations.

User-facing Markdown should be Chinese. Matplotlib figure text, table headers, axes, titles, legends, and filenames should be English where possible. For any plotting task, read `references/matplotlib_paper_style.md` or project `PLOT_STYLE.md` first.

Every experiment report must state `Question`, `Bottleneck`, `Mechanism`, `Evidence`, `Contribution`, and `Decision`. Execution tasks cannot be marked complete without real command/log/metric evidence unless the user explicitly asks for plan-only work.

## multi-turn.py

Use the bundled `assets/multi-turn.py` as the default workload generator. The project initializer copies it to the target project root unless `--no-copy-multi-turn` is used.

Typical command shape:

```bash
python3 multi-turn.py \
  --base-url http://127.0.0.1:8008/v1 \
  --model dsv4 \
  --tokenizer /workspace/models/DeepSeek-V4-Flash-w8a8-mtp \
  --request-concurrency 5 \
  --active-sessions 5 \
  --num-sessions 5 \
  --initial-input-tokens 3500 \
  --shared-prefix-tokens 1500 \
  --delta-input-tokens 3500 \
  --num-rounds 3 \
  --output-tokens 500 \
  --temperature 0 \
  --timeout 1800 \
  --startup-ramp-seconds 2 \
  --results-dir /workspace/results/baseline_low_load
```

Adjust `--base-url`, `--model`, `--tokenizer`, concurrency/session counts, token sizes, timeout, and `--results-dir` to match the target engine and machine. Use `--dry-run` during workload sizing when the engine is not ready.

## Resource Map

`references/prompts/` contains the staged workflow prompts copied from the original prompt pack.

`references/hooks_specs/` contains hook/checker behavior specs for official docs, source edit guard, log extraction, canonical result uniqueness, process compaction, real execution evidence, and stop review.

`references/matplotlib_paper_style.md` is the integrated plotting guideline provided by the user.

`assets/templates/` contains report, manifest, glossary, workflow config, and project README templates to copy into initialized projects.

`assets/multi-turn.py` is the bundled multi-round Chat Completions workload driver.
