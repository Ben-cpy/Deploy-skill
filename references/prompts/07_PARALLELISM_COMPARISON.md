# Stage 7：Parallelism Comparison

## 目标

最多比较 3 组并行策略，使用相同 workload 判断 TP/DP 是否真正改善 KV capacity、吞吐和稳定性，而不是把瓶颈搬到通信或 routing。

## 候选规则

```text
PP: 只有模型放不下时才考虑
EP: MoE 模型通常默认打开，不作为主要 sweep 变量
TP: 影响 weight sharding、per-replica KV、communication
DP: 影响 aggregate throughput / aggregate KV，但依赖 routing/session affinity
```

最多 3 组。例如：

```text
Config A: TP=8, DP=1
Config B: TP=4, DP=2
Config C: TP=2, DP=4
```

如果模型在某些 TP 下放不下，不硬测，改为只比较可启动配置或少量关键参数变体。

## 必须使用相同负载

每组配置跑同一批：

```text
low_load
high_load
high_session
```

不要根据每个配置重新生成不同 workload，否则不可比较。

## 串行执行规则

每个配置、每个 workload 都必须串行运行。禁止同时启动多个配置或多个 workload 共享同一服务端口、GPU/Ascend 设备、模型服务或输出目录。并行比较只能比较配置结果，不能并发采集结果。若用户明确要求叠加压力测试，结果必须单独标记为非标准数据，不得用于 TP/DP 主结论表。

## 必须回答

```text
TP 增大是否换来更大可用 KV，还是 decode communication 变差？
DP 增大是否真的提升 aggregate serving，还是破坏 prefix locality？
MoE + EP 是否引入 routing/grouped GEMM/communication bottleneck？
同一 workload 下哪个配置的 KV behavior 最稳？
```

## 必须产出

```text
experiments/parallelism_candidates.yaml
reports/parallelism_comparison.md
reports/parallelism_decision.md
figures/parallelism_tradeoff.png
```

## 完成条件

最多 3 个配置；每个配置有相同 workload 证据；结论必须 keep/drop/uncertain。不能用不同负载下的数字做横向结论。


## 通用限制

- 不修改推理引擎源码。
- 不把大段 raw log 放进 report。
- 不把失败/无效结果写入 canonical。
- 不用理论分析替代本阶段要求的真实执行证据。
- 超过配置中的最大迭代次数必须停止并总结。

## 报告要求

面向用户的 md 使用中文。图和表使用 academic English。术语首次出现给一句话解释。每个实验写清楚 Question、Bottleneck、Mechanism、Evidence、Contribution、Decision。
