# LLM Serving KV Diagnostics

这个仓库现在只保留一个 skill：`llm-serving-kv-diagnostics`。

它用于执行单节点 LLM serving / KV cache 诊断 workflow。目标不是做通用 benchmark harness，而是用可复现的证据链回答：当前 engine、model、hardware、container/runtime 组合能否稳定启动，KV cache 容量是否匹配目标 workload，prefix cache 是否真实命中，offload 是否有收益，以及少量参数调优是否值得保留。

## 流程是什么

主流程分 10 个阶段：

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

核心证据链是：

```text
官方文档锁定
-> 环境锁定
-> smoke correctness
-> 模型内存与 KV 估算
-> workload KV pressure sizing
-> low/high/high_session baseline
-> prefix cache validation
-> parallelism comparison
-> LMCache/offload A/B
-> targeted parameter decisions
-> final deployment report
```

## 如何使用

把这个仓库作为 skill 暴露给 Codex，使 Codex 可以加载根目录的 `SKILL.md`。初始化目标项目时，在本仓库根目录运行：

```bash
python scripts/init_project.py --project <target_project_root>
```

只有在明确允许覆盖 managed files 时才使用 `--force`。默认情况下，已有文件会先写入 `.bak.<timestamp>` 备份。

初始化会在目标项目中创建或更新：

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
runs/
results/
reports/
figures/
.codex/hooks.json
.codex/hooks/stop_kv_check.py
multi-turn.py
```

初始化完成后，在目标项目里运行 `/hooks`，检查并信任项目 Stop hook。初始化阶段不要启动 vLLM、不要跑 benchmark、不要修改 engine 源码。

## 重点查看哪些文件

理解这个 skill 本身时，先看：

```text
SKILL.md
README.md
```

在已经初始化的目标项目里，不要一次性读取所有 prompt。每个阶段只读当前需要的文件，默认从这些开始：

```text
prompts/README.md
AGENTS.md
PROCESS.md
prompts/00_WORKFLOW_MAP.md
prompts/00_ROLE_AND_RESEARCH_TASTE.md
prompts/12_GUARDRAILS_HOOKS_AND_BUDGETS.md
当前阶段 prompt
```

按需再读横向规范：

```text
prompts/11_LOG_EXTRACTION_AND_PERSISTENCE.md
prompts/13_INTERACTION_READABILITY_AND_TERMS.md
prompts/14_DATA_UNIQUENESS_AND_CANONICALIZATION.md
prompts/15_STOP_HOOK_AND_COMMIT_CHECKS.md
prompts/16_REAL_EXECUTION_EVIDENCE.md
hooks/*
PLOT_STYLE.md
```

## 仓库结构

```text
SKILL.md                  skill 入口与核心操作规则
scripts/init_project.py   目标项目初始化脚本
references/prompts/       分阶段 workflow prompts
references/hooks_specs/   hook 和 evidence checker 规范
references/matplotlib_paper_style.md
assets/multi-turn.py      默认 multi-round Chat Completions workload driver
assets/templates/         report、manifest、config、project 模板
assets/project_hooks/     复制到目标项目的 hook 实现
agents/openai.yaml        skill UI 元数据
```

## 强约束

- 不修改 vLLM、SGLang、LMCache、Mooncake、Transformers、Torch、FlashInfer、site-packages engine code 或 vendor runtime source。
- 所有服务日志必须落盘，报告引用抽取后的指标和 raw log 路径，不粘贴大段日志。
- 只有验证成功的运行可以进入 `results/canonical/`。
- 失败或无效运行放入 `runs/scratch_failed/` 或候选目录。
- 面向用户的 Markdown 使用中文。
- matplotlib 图、表头、坐标轴、标题、legend 和文件名尽量使用英文。
- 每个实验报告必须写清 `Question`、`Bottleneck`、`Mechanism`、`Evidence`、`Contribution`、`Decision`。

