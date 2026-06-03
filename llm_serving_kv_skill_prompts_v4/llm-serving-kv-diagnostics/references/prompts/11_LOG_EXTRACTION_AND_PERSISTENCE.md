# 横向规范：日志抽取与持久化

## 目标

支持长时间、多次 vLLM/SGLang 启动和负载实验，同时避免 raw log 进入上下文和用户报告。

## 运行状态机

每次运行先进入：

```text
runs/attempts/<run_id>/
```

运行完成后：

```text
valid success -> runs/raw/<run_id>/
invalid or failed -> runs/scratch_failed/<run_id>/ 只保留失败摘要和必要关键日志片段
best valid result -> results/canonical/
```

这样同时满足两点：raw 成功数据可追溯，失败/无效数据不会污染用户 review。

## 每次运行必须保存

```text
command.sh
serve.log
client.log
run_manifest.yaml
metrics_raw.json if available
log_extract.txt
```

## 动态抽取关键日志

必须使用 grep/rg/awk/python parser 等命令抽取关键行，报告中只展示抽取结果。

重点抽取：

```text
Available KV cache memory
GPU/NPU KV cache size
Maximum concurrency
cache block
prefix cache hit/miss
preemption
recompute
OOM
worker crash
NCCL / HCCL error
LMCache save/load/hit/miss
CPU backend
latency summary
success rate
```

## 报告写法

md 中只写：

```text
key extracted lines
metric table
short interpretation
path to raw log
```

不要粘贴超过 40 行连续日志。

## 完成条件

每个阶段报告必须能追溯到 run_id 和 raw log path，但用户不需要打开 raw log 就能理解结论。
