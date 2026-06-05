# AGENTS.md Template

## 一句话目标

执行单节点 LLM serving / KV cache 诊断 workflow：基于官方文档、真实运行日志、KV pressure workload 和 canonical 数据，给出可复现部署结论。

## 当前阶段读取规则

只读取当前阶段 prompt 与必要横向规范。不要一次性加载所有 prompt。

必读：

```text
README.md
PROCESS.md
00_WORKFLOW_MAP.md
00_ROLE_AND_RESEARCH_TASTE.md
12_GUARDRAILS_HOOKS_AND_BUDGETS.md
config/workflow_manifest.json
当前阶段 prompt
```

按需读：

```text
11_LOG_EXTRACTION_AND_PERSISTENCE.md
13_INTERACTION_READABILITY_AND_TERMS.md
14_DATA_UNIQUENESS_AND_CANONICALIZATION.md
15_STOP_HOOK_AND_COMMIT_CHECKS.md
16_REAL_EXECUTION_EVIDENCE.md
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

如果当前任务是执行阶段，且修改了 `experiments/`、`runs/`、`results/`、`reports/`、`figures/` 任一目录，必须执行 stop review check。纯讨论、纯规划、只编辑 prompt 文档时不触发。

Stop 前必须读取 `config/workflow_manifest.json`。如果 required/approved 子任务仍未完成，或 completed execution task 缺少 command、run_id、log extract、metrics、report、必要 figure，继续补跑或补产物，不要 final。

## 最终交付

用户主要阅读：

```text
reports/final_report.md
reports/final_report.pdf
reports/final_deployment_card.md
```

如果 PDF renderer 缺失，保留 `reports/final_report.md`，并写 `reports/final_report_pdf_dependency_missing.md`。
