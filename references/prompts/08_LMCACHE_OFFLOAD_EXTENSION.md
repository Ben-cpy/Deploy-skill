# Stage 8：KV Cache Offload Extension

## 目标

单节点默认评估 LMCache。判断外部 KV offload 是否能在 high_load / high_session 场景下扩大有效 KV capacity 或减少 recompute/preemption，同时不显著恶化 ITL/TPOT。

Mooncake 不是默认主流程。只有用户明确启用 Mooncake、multi-node 或指定 offload extension 时，才把 Mooncake 纳入本阶段；纳入后必须先完成官方文档锁、启动命令来源、最大尝试次数、失败摘要和降级策略记录。

## 前置条件

必须满足：

```text
baseline can run
prefix cache behavior understood
low/high/high_session configs fixed
reports/basic-info.md exists
server logs persisted and extractable
```

如果 prefix cache 未确认命中，不能评价 LMCache 收益。

## LMCache Bring-up

检查：

```text
LMCache connector loads
local CPU backend works
KV save/load log appears
cache hit/miss log available
CPU memory grows as expected
HBM pressure changes
no severe transfer/serialization failure
```

最大尝试次数：

```text
lmcache_bringup_max_attempts: 3
```

## A/B Test

固定 workload：

```text
baseline: engine native prefix cache, no external offload
LMCache: engine + LMCache CPU offload
```

运行：

```text
low_load
high_load
high_session
```

所有 A/B workload 必须串行运行。不要让 baseline 与 LMCache 同时打到同一服务、设备或模型。并发只允许用于用户明确要求的叠加压力实验，并且不得进入标准 A/B 主表。

## 判断标准

```text
low_load: LMCache 不应明显拖慢；拖慢说明 overhead 太大
high_load: LMCache 应提高成功率或减少 preemption/recompute
high_session: LMCache 应改善 session residency；否则 workload reuse 或 eviction 策略不匹配
```

核心判断：LMCache 的价值不是“能把 KV 放到 CPU”，而是 saved prefill / avoided recompute 大于 KV transfer overhead。

## 必须产出

```text
reports/lmcache_launch.md
reports/lmcache_low_load.md
reports/lmcache_high_load.md
reports/lmcache_high_session.md
reports/offload_decision.md
figures/offload_ablation.png
```

## 完成条件

LMCache A/B 使用同一 workload；报告包含 capacity、TTFT、ITL/TPOT、E2E、success rate、CPU memory、HBM pressure、load/store evidence。不能只因 LMCache 能启动就说有效。


## 通用限制

- 不修改推理引擎源码。
- 不把大段 raw log 放进 report。
- 不把失败/无效结果写入 canonical。
- 不用理论分析替代本阶段要求的真实执行证据。
- 超过配置中的最大迭代次数必须停止并总结。

## 报告要求

面向用户的 md 使用中文。图和表使用 academic English。术语首次出现给一句话解释。每个实验写清楚 Question、Bottleneck、Mechanism、Evidence、Contribution、Decision。
