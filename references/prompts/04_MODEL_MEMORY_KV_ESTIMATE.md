# Stage 4：Model Memory & KV Cache Estimate

## 目标

通过官方/可信模型结构信息、静态 KV 估算和 runtime log 校准，得到系统 KV cache 容量和 per-DP/aggregate capacity。此阶段替代独立 KV capacity characterization，不做大规模容量扫描。

## 必须联网检索

优先官方模型卡、官方 repo、官方部署文档。必须记录：

```text
dense or MoE
number of layers
hidden size
num attention heads
num KV heads
head dim
MHA / GQA / MQA / MLA
SWA / full attention / hybrid attention
context length
dtype / quantization format
expert count / active experts if MoE
recommended TP / EP setting if available
```

## 必须计算

普通 MHA/GQA/MQA 可使用近似公式：

```text
KV/token ≈ num_layers × 2 × num_kv_heads × head_dim × dtype_bytes
KV_budget ≈ available_HBM - weight_memory - runtime_reserved - scratch
max_KV_tokens ≈ KV_budget / KV_bytes_per_token
```

如果模型使用 MLA、SWA 或 hybrid attention，必须明确说明普通公式的适用性限制，并用 runtime log 校准。

## 必须抽取 runtime log

动态抽取：

```text
Available KV cache memory
GPU/NPU KV cache size
Maximum concurrency
cache blocks
max_model_len
DP / TP / EP rank info
preemption / recompute warnings
attention backend
quantization backend
```

## DP 注意事项

可以报告：

```text
per-DP KV capacity
aggregate KV capacity = per-DP KV capacity × DP
```

但必须注明：aggregate capacity 不是单 session 可共享 KV 池。单个 session 能用多少 KV 取决于所在 DP replica、routing 和 session affinity。

## 必须产出

```text
reports/model_structure.md
reports/memory_estimate.md
reports/runtime_kv_log_parse.md
reports/kv_estimate_vs_runtime.md
reports/basic-info.md
figures/kv_capacity_breakdown.png if useful
```

`basic-info.md` 至少包含：system aggregate KV cache capacity、per-DP KV cache capacity、single-request decode speed、关键启动日志片段。

## 完成条件

理论估算、runtime log、basic-info 三者一致或差异被解释；不能只做理论分析后标记完成。


## 通用限制

- 不修改推理引擎源码。
- 不把大段 raw log 放进 report。
- 不把失败/无效结果写入 canonical。
- 不用理论分析替代本阶段要求的真实执行证据。
- 超过配置中的最大迭代次数必须停止并总结。

## 报告要求

面向用户的 md 使用中文。图和表使用 academic English。术语首次出现给一句话解释。每个实验写清楚 Question、Bottleneck、Mechanism、Evidence、Contribution、Decision。
