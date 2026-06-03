# Stage 10：Final Deployment Report

## 目标

生成唯一可信的最终部署卡片。用户最终只需要阅读 md 和其中插入的 png，即可知道推荐配置、证据路径、已知坏配置和风险。

## 必须输出

```text
reports/final_deployment_card.md
results/canonical/final_launch_command.sh
results/canonical/final_metrics.json
results/canonical/run_manifest.yaml
figures/final_overview.png
```

## Final Deployment Card 必须包含

```text
hardware
container
engine/backend
model
official docs lock
recommended launch command
recommended TP/DP/EP
whether PP is needed
max_model_len
max_num_seqs
max_num_batched_tokens
gpu_memory_utilization
per-DP KV capacity
aggregate KV capacity
single-request decode speed
low_load result
high_load result
high_session result
prefix cache validation
LMCache decision
known bad configs summary
final recommendation
```

## 可读性要求

每个结论必须说明：

```text
结论是什么
由哪个实验支持
关键指标是什么
对应瓶颈是什么
下一步风险是什么
```

术语首次出现给一句话解释。

## 数据唯一性要求

最终报告只能引用 `results/canonical/` 的数据。失败、错误、无效、明显低质量结果只能作为 known bad configs 简短摘要出现，不进入主表。

## 完成条件

完成前必须运行 stop review check：

```text
是否遵守官方文档优先
是否修改了源码
是否所有关键输出存在
是否 raw log 与 report 分离
是否 canonical 只有唯一有效结果
是否 PROCESS.md 已更新并压缩
是否图已插入 md
是否术语首次出现已解释
```


## 通用限制

- 不修改推理引擎源码。
- 不把大段 raw log 放进 report。
- 不把失败/无效结果写入 canonical。
- 不用理论分析替代本阶段要求的真实执行证据。
- 超过配置中的最大迭代次数必须停止并总结。

## 报告要求

面向用户的 md 使用中文。图和表使用 academic English。术语首次出现给一句话解释。每个实验写清楚 Question、Bottleneck、Mechanism、Evidence、Contribution、Decision。
