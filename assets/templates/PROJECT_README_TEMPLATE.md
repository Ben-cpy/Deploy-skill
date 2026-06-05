# Project README Template

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
reports/final_deployment_card.md
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
