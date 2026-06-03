# Integrity Check for v4 Prompt Pack

## 检查结论

v4 已覆盖用户两批约束，并修复 v3 的结构性缺口。核心修复包括：顶层 `PROCESS.md`、更硬的 hook spec、官方文档锁模板、真实执行证据规范、数据状态机、figure/report 检查和按需读取策略。

## 文件完整性

必须存在：

```text
README.md
AGENTS_TEMPLATE.md
PROCESS.md
00_INIT_SKILL_SETUP.md
00_ROLE_AND_RESEARCH_TASTE.md
00_USER_MANUAL.md
00_WORKFLOW_MAP.md
01_OFFICIAL_DOCS_AND_SCOPE_LOCK.md
02_ENVIRONMENT_STACK_LOCKING.md
03_ENGINE_SMOKE_BRINGUP.md
04_MODEL_MEMORY_KV_ESTIMATE.md
05_WORKLOAD_SIZING_MULTITURN.md
06_BASELINE_KV_LOAD_TEST.md
07_PARALLELISM_COMPARISON.md
08_LMCACHE_OFFLOAD_EXTENSION.md
09_TARGETED_VLLM_PARAMETER_TUNING.md
10_FINAL_DEPLOYMENT_REPORT.md
11_LOG_EXTRACTION_AND_PERSISTENCE.md
12_GUARDRAILS_HOOKS_AND_BUDGETS.md
13_INTERACTION_READABILITY_AND_TERMS.md
14_DATA_UNIQUENESS_AND_CANONICALIZATION.md
15_STOP_HOOK_AND_COMMIT_CHECKS.md
16_REAL_EXECUTION_EVIDENCE.md
17_PLOT_AND_VISUAL_REPORTING.md
hooks_specs/
templates/
checklists/
```

## 无冲突规则

- official docs 优先不等于禁止社区信息；社区信息只能作为辅助。
- 不保存失败数据不等于完全丢失 debug 线索；scratch_failed 只保留必要失败摘要和关键日志片段。
- canonical 唯一不等于 raw 数据唯一；raw 可以多次，canonical 只能一份有效结果。
- hook 优先不等于 prompt 无效；prompt 负责语义指导，hook 负责硬检查。
- stop hook 不在所有回复触发，只在真实执行阶段和相关目录修改时触发。
