# Stage 4：Model Memory & KV Cache Estimate

## 目标

通过官方/可信模型结构信息、固定脚本静态 KV 估算和 runtime log 校准，得到系统 KV cache 容量和 per-DP/aggregate capacity。此阶段替代独立 KV capacity characterization，不做大规模容量扫描。

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

## 必须使用固定脚本计算

不要只依赖 agent 领域知识手算。vLLM 路径必须先使用 Stage 3 生成的日志抽取 JSON，再调用确定性容量计算脚本：

```bash
python instrumentation/kv_capacity_calculator.py \
  --model-config <model_path>/config.json \
  --log-extract-json runs/raw/<run_id>/vllm_kv_log_extract.json \
  --out runs/raw/<run_id>/kv_capacity_estimate.json
```

如果 Stage 3 的成功运行仍在 `runs/attempts/<run_id>/`，可以先以 attempts 路径运行；晋级 raw 时必须同步 JSON。缺少 runtime log 时可以用 `--kv-cache-memory-bytes` 或 `--kv-cache-memory-gib` 做静态 dry-run，但不能把执行类 Stage 4 标记完成。

脚本输出必须进入报告证据：

```text
runs/raw/<run_id>/vllm_kv_log_extract.json
runs/raw/<run_id>/kv_capacity_estimate.json
runs/raw/<run_id>/log_extract.txt
```

## 公式要求

普通 MHA/GQA/MQA 可使用近似公式：

```text
KV/token ≈ num_layers × 2 × num_kv_heads × head_dim × dtype_bytes
KV_budget ≈ available_HBM - weight_memory - runtime_reserved - scratch
max_KV_tokens ≈ KV_budget / KV_bytes_per_token
```

脚本必须显式报告：

```text
logical KV bytes/token
resident KV bytes/token per TP rank
TP replication/padding/waste factor
per-DP usable context tokens / token-equivalent KV capacity
aggregate usable context tokens = per-DP usable context tokens × DP
runtime reported KV capacity if present
runtime/formula calibration ratio
```

如果模型使用 MLA/DSA、SWA 或 hybrid attention，不能套用普通 GQA 公式后结束。必须让脚本使用对应 profile 或显式覆盖项：

```bash
--model-profile auto|standard|mla|glm_dsa
--kv-tp-policy auto|shard_heads|replicate_latent|replicate|none
--dcp-kv-policy auto|none|shard_context
--tp-padding-multiple <N>
--mla-tp-waste-factor <float>
```

MLA/DSA 的 TP 影响必须作为独立项报告：某些 engine/kernel 会复制 latent KV 或按 TP rank padding，导致 TP 不一定线性降低 per-rank resident KV。普通 MHA/GQA/MQA 也必须报告 KV heads 不能被 TP 整除时的 per-rank padding/waste。PP 必须按每个 pipeline rank 承载的 layer 数影响 per-rank resident KV；DCP 默认不能假设会切分 KV，除非 engine log 或官方文档证明可用 `--dcp-kv-policy shard_context`。DP 只增加 aggregate serving capacity，不增加单 session 可共享 KV 池。SWA/hybrid attention 必须用 runtime log 的 token capacity 校准。

## 必须抽取 runtime log

动态抽取：

```text
Available KV cache memory
GPU/NPU KV cache size
cache blocks
max_model_len
DP / TP / EP rank info
preemption / recompute warnings
attention backend
quantization backend
```

vLLM 日志抽取必须来自 `instrumentation/vllm_kv_log_extract.py` 的 JSON/TXT 产物；报告中只引用关键行和路径。

## DP 注意事项

可以报告：

```text
per-DP KV capacity
aggregate KV capacity = per-DP KV capacity × DP
```

主报告必须只写“可用 context tokens / token-equivalent KV capacity”，例如 `usable context ~= 85K tokens` 或 `usable context ~= 1.47M tokens`。不要把 `Maximum concurrency for <N> tokens` 或任何并发折算写入容量结论，避免把容量单位误读成请求数。必须注明：aggregate capacity 不是单 session 可共享 KV 池。单个 session 能用多少 KV 取决于所在 DP replica、routing 和 session affinity。

## 必须产出

```text
reports/model_structure.md
reports/memory_estimate.md
reports/runtime_kv_log_parse.md
reports/kv_estimate_vs_runtime.md
reports/basic-info.md
runs/raw/<run_id>/vllm_kv_log_extract.json
runs/raw/<run_id>/kv_capacity_estimate.json
figures/kv_capacity_breakdown.png if useful
```

`basic-info.md` 至少包含：system aggregate usable context tokens、per-DP usable context tokens、single-request decode speed、关键启动日志片段。不要写并发折算。

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
