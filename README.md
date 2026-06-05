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

## 三类对外行为

### Initialize

当用户要求初始化、bootstrap、安装 workflow 到目标项目时，运行 `scripts/init_project.py`。初始化只创建规范、目录、manifest、模板、hook 和入口文件，不执行真实 vLLM/LMCache/Mooncake benchmark。

初始化后的目标项目包含：

```text
config/workflow.yaml
config/workflow_manifest.json
.codex/hooks/stop_kv_check.py
templates/FINAL_REPORT_TEMPLATE.md
reports/
figures/
```

### Continue / Execute

当 Stage 1 已经产生计划，或用户要求继续执行剩余任务时，Codex 必须读取 `config/workflow_manifest.json`，按 Stage 1-10 串行推进 required/approved 子任务。执行类任务不能只做 2-3 项就停止汇报；准备停止前必须检查 manifest 中剩余任务，并在环境允许时继续执行。

每个真实执行任务都要写入 run evidence：`run_id`、启动命令文件、raw log 或 dry-run output、log extract、metrics、报告、必要 png。只有用户明确要求 plan-only 时，才能把任务标为 plan-only。

所有 benchmark/workload/trial 默认串行运行。运行前确认没有其他 workload 占用同一服务端口、同一 GPU/Ascend 设备或同一模型服务。只有用户明确要求叠加压力测试时才允许并发，并且结果不得与标准串行结果混入同一主表。

### Validate / Final Check

当用户要求检查是否完成、生成最终结论或进入 Stage 10 时，在目标项目运行：

```bash
python .codex/hooks/stop_kv_check.py
```

最终检查覆盖 Stage 1-10 的官方文档锁、启动命令对齐、manifest 完成度、真实执行证据、canonical 数据、png 引用、最终 Markdown/PDF 交付物。发现缺口时应回到对应阶段补跑或补产物，而不是只用文字解释。

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

## 最终交付物

初始化后的目标项目应把下面文件作为用户主要阅读入口：

```text
reports/final_report.md
reports/final_report.pdf
reports/final_deployment_card.md
```

`final_report.md` 是中文、克制、学术化、面向业务阅读者的长报告，按 Stage 1-10 线性组织，只引用 canonical 数据、关键表和关键 png。若环境缺少 PDF 渲染工具，应保留 Markdown，并写明缺少的 PDF 依赖，不得编造数据或省略证据缺口。

## 强约束

- 不修改 vLLM、SGLang、LMCache、Mooncake、Transformers、Torch、FlashInfer、site-packages engine code 或 vendor runtime source。
- 所有服务日志必须落盘，报告引用抽取后的指标和 raw log 路径，不粘贴大段日志。
- 只有验证成功的运行可以进入 `results/canonical/`。
- 失败或无效运行放入 `runs/scratch_failed/` 或候选目录。
- 面向用户的 Markdown 使用中文。
- matplotlib 图、表头、坐标轴、标题、legend 和文件名尽量使用英文。
- 每个实验报告必须写清 `Question`、`Bottleneck`、`Mechanism`、`Evidence`、`Contribution`、`Decision`。
- 默认主流程是单节点 LMCache/offload 诊断；Mooncake 只在用户明确启用 multi-node/offload extension 时进入 scope，并必须记录官方文档、命令来源、最大尝试次数、失败摘要和降级策略。
