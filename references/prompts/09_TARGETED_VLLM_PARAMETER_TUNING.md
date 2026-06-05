# Stage 9：Targeted vLLM/SGLang Parameter Tuning

## 目标

在 bottleneck 已明确后做少量 targeted parameter trials。不是 full sweep，也不是为了生成大量表格。

## 默认候选参数

vLLM 单机场景优先：

```text
--max-num-seqs
--max-num-batched-tokens
--gpu-memory-utilization
--enable-prefix-caching
--enable-chunked-prefill
scheduler / async scheduling
compilation / graph mode
attention backend
```

SGLang 或其他 engine 必须先查官方文档，映射到等价参数，不得直接套 vLLM 参数名。

Stage 9 的命令必须引用 `reports/official_docs_lock.md` 中的 engine/backend/model 参数来源。若使用用户提供命令或本地经验参数，必须记录它与官方示例的差异和风险。

## 最大 trial 数

```text
parameter_trial_max: 6
single_bottleneck_trial_max: 3
```

超过上限停止。

## 参数到瓶颈映射

```text
KV capacity 不够:
increase gpu_memory_utilization / reduce max_model_len / change TP-DP / enable LMCache

preemption or recompute 多:
reduce max_num_seqs / reduce max_num_batched_tokens / increase KV budget / use offload

TTFT 高:
validate prefix cache / chunked prefill if suitable / LMCache only if reuse exists

ITL or TPOT 差:
check batching pressure / TP communication / max_num_seqs / attention backend

tail latency 爆炸:
reduce max_num_batched_tokens / reduce concurrency / scheduler configs
```

## 每个 trial 必须记录

```text
changed parameter
hypothesis
expected bottleneck movement
command
run_id
workload used
metrics
log evidence
keep/drop/uncertain
serial execution confirmed
```

## 串行执行规则

trial 必须串行运行。每次运行前确认没有其他 active run 占用同一服务端口、同一 GPU/Ascend 设备、同一模型服务或同一输出目录。禁止并发跑多个参数 trial 后直接比较指标；并发叠加压力数据只能在用户明确要求时生成，并单独标记为非标准。

## 必须产出

```text
experiments/parameter_trials.yaml
reports/parameter_trials.md
reports/parameter_decision.md
figures/parameter_tradeoff.png
results/canonical/final_launch_command.sh if improved
```

## 完成条件

每个 trial 有真实运行证据和 keep/drop/uncertain 结论。不能因为某个平均指标变好就直接替换 canonical，必须检查 correctness、tail latency、cache hit、稳定性。


## 通用限制

- 不修改推理引擎源码。
- 不把大段 raw log 放进 report。
- 不把失败/无效结果写入 canonical。
- 不用理论分析替代本阶段要求的真实执行证据。
- 超过配置中的最大迭代次数必须停止并总结。

## 报告要求

面向用户的 md 使用中文。图和表使用 academic English。术语首次出现给一句话解释。每个实验写清楚 Question、Bottleneck、Mechanism、Evidence、Contribution、Decision。
