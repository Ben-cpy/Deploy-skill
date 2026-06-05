# Stage 1：Official Docs & Scope Lock

## 目标

确认当前任务的推理引擎、后端、模型和 offload 工具的官方依据。之后的部署、调参、日志解释必须以官方文档为第一依赖。

## 输入

```text
engine: vLLM / SGLang / others
backend: CUDA / CANN / ROCm / others
model name or path
container version
base launch command if provided
optional: LMCache / Mooncake / other offload tool
```

## 必须联网检索

强制阅读对应官方文档或官方仓库：

```text
engine official docs
engine official GitHub README / examples
backend official integration docs, e.g. vLLM-Ascend / CUDA / CANN / NCCL / HCCL
model official card / repo / deployment notes
LMCache official docs if single-node offload is planned
Mooncake official docs only if multi-node extension is explicitly requested
```

社区博客、issue、个人经验只能作为辅助，不能覆盖官方文档。

## 必须产出

```text
reports/official_docs_lock.md
reports/scope_lock.md
```

`official_docs_lock.md` 必须包含：

```text
doc title
source type: official docs / official repo / model card / auxiliary
URL or local path
version / commit / date if available
official launch command or official example
project launch command
difference / reason / accepted risk
用于本 workflow 的具体规则
不确定点
```

必须覆盖：

```text
engine: 优先官方文档和官方 repo examples
backend: CUDA/CANN/ROCm/vLLM-Ascend 等官方文档或官方 repo
model: model card 或官方 repo 中的部署说明
offload: 启用 LMCache 时锁定 LMCache 官方文档；只有用户明确启用 Mooncake/multi-node 时才锁定 Mooncake 官方文档
```

Stage 3/8/9 的启动命令和调参命令必须引用本文件中的对应条目。如果用户提供命令与官方示例不同，记录差异和风险，不要静默改写成未经验证的命令。

## Mooncake Scope

默认主流程是单节点 LMCache/offload 诊断。Mooncake 不是默认必做项。只有用户明确要求 multi-node、Mooncake 或特定 offload extension 时，才进入 scope；进入后必须记录官方文档来源、命令来源、最大尝试次数、失败摘要和降级策略。

## 完成条件

只有当官方文档来源被记录、engine/backend/model/offload 范围被锁定后，才能进入 Stage 2。


## 通用限制

- 不修改推理引擎源码。
- 不把大段 raw log 放进 report。
- 不把失败/无效结果写入 canonical。
- 不用理论分析替代本阶段要求的真实执行证据。
- 超过配置中的最大迭代次数必须停止并总结。

## 报告要求

面向用户的 md 使用中文。图和表使用 academic English。术语首次出现给一句话解释。每个实验写清楚 Question、Bottleneck、Mechanism、Evidence、Contribution、Decision。
