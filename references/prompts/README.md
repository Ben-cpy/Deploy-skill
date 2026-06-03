# LLM Serving KV Skill Prompts v4

这个文件夹用于把“单节点 LLM Serving / KV Cache 诊断流程”转成可审阅、可迁移的 skill prompt。核心目标不是写一个通用 benchmark harness，而是在不同单节点硬件、容器、推理引擎和模型组合下，快速回答：能否稳定启动、KV cache 容量是否匹配 workload、prefix cache 是否真实命中、LMCache 是否带来容量/延迟收益、TP/DP/参数调整是否值得保留。

## 按需读取策略

Agent 不应一次性读取所有阶段细节，避免上下文膨胀。默认只读取：

```text
README.md
AGENTS_TEMPLATE.md 或项目根目录 AGENTS.md
PROCESS.md
00_WORKFLOW_MAP.md
00_ROLE_AND_RESEARCH_TASTE.md
12_GUARDRAILS_HOOKS_AND_BUDGETS.md
当前阶段对应的 md
```

需要时再读取：

```text
11_LOG_EXTRACTION_AND_PERSISTENCE.md
13_INTERACTION_READABILITY_AND_TERMS.md
14_DATA_UNIQUENESS_AND_CANONICALIZATION.md
15_STOP_HOOK_AND_COMMIT_CHECKS.md
16_REAL_EXECUTION_EVIDENCE.md
templates/*
hooks_specs/*
```

## 主流程

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

## 顶层强约束

- 官方文档是第一依赖规范；社区经验和博客只能作为辅助证据。
- 不修改 vLLM、SGLang、LMCache、Mooncake、Transformers、Torch 等推理引擎源码。
- profile 需要 hack 时，只能新增 `instrumentation/` 下可开关、可回滚的 monkey patch。
- 优先使用 hook、脚本、检查器等硬机制；prompt 只是第二层保护。
- 所有服务启动日志必须输出到文件；报告只写抽取后的关键指标和 raw log 路径。
- 面向用户的交互文档使用中文；matplotlib 图、表头、axis、legend 使用学术英文。
- 每个术语首次出现必须给一句话解释。
- 每个实验必须说明 Question、Bottleneck、Mechanism、Evidence、Contribution、Decision。
- 子任务不能只做理论分析就标记完成，除非任务明确声明为 plan-only。
- 最终给用户 review 的只有 `results/canonical/` 中唯一有效数据；失败/无效结果不进入主报告。
- 项目根目录应有 `PROCESS.md`，每次阶段结束或 commit 更新，并控制最多 20 条。

## 推荐项目目录

```text
AGENTS.md
README.md
PROCESS.md
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
```

用户主要阅读 `reports/*.md` 和其中插入的 `figures/*.png`。raw log 保存用于追溯，默认不要求用户主动查看。
