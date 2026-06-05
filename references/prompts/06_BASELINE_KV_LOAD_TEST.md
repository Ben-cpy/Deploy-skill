# Stage 6：Baseline KV-oriented Load Test

## 目标

在不开外部 offload 的情况下，用 fixed workload 验证 engine 原生 KV 行为：容量以内是否稳定、KV 超压如何退化、多 session 驻留时 cache 是否保得住。

## 必须运行

```text
low_load
high_load
high_session
```

默认可开启 engine 原生 prefix cache，但不接入 LMCache/Mooncake。

## 串行执行规则

所有 workload 必须串行运行。每次运行前确认没有其他 active run 正在使用同一服务端口、同一 GPU/Ascend 设备、同一模型服务或同一输出目录。不要并发运行 low_load、high_load、high_session；并发会污染 TTFT、ITL/TPOT、throughput、cache hit 和 HBM/CPU memory 指标。

只有用户明确要求叠加压力测试时才允许并发运行，并且必须标记为 `non_standard_stacked_load`，不得与标准串行 baseline 混入同一主表。

## 必须记录

```text
success rate
TTFT p50/p95/p99
ITL or TPOT p50/p95/p99
E2E latency
request throughput
output token throughput
prefix cache hit log
preemption / recompute log
OOM / worker crash
HBM usage
CPU memory usage
cache block allocation behavior
```

## Prefix cache validation

必须确认：

```text
shared prefix actually hit
warm request TTFT improves or reason explained
cache hit appears in log/metrics
HBM growth matches expectation
no unexpected full-prefill repetition
```

如果 prefix cache 未命中，不能进入 LMCache 收益评价，只能进入 debug。

## 必须产出

```text
reports/baseline_low_load.md
reports/baseline_high_load.md
reports/baseline_high_session.md
reports/prefix_cache_validation.md
reports/baseline_kv_behavior.md
figures/baseline_latency_summary.png
figures/prefix_cache_effect.png if available
```

## 完成条件

每个 workload 有真实运行证据、关键日志抽取、指标表和至少一个 summary figure。失败/无效运行不得进入 canonical。


## 通用限制

- 不修改推理引擎源码。
- 不把大段 raw log 放进 report。
- 不把失败/无效结果写入 canonical。
- 不用理论分析替代本阶段要求的真实执行证据。
- 超过配置中的最大迭代次数必须停止并总结。

## 报告要求

面向用户的 md 使用中文。图和表使用 academic English。术语首次出现给一句话解释。每个实验写清楚 Question、Bottleneck、Mechanism、Evidence、Contribution、Decision。
