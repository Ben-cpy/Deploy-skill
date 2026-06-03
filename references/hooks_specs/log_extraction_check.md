# Hook Spec: log_extraction_check

## Purpose

防止大日志进入上下文和用户报告，强制抽取关键指标。

## Required For Each Run

```text
serve.log
client.log
log_extract.txt
run_manifest.yaml
```

## Required Extract Patterns

```text
Available KV cache memory
GPU/NPU KV cache size
Maximum concurrency
prefix cache
preemption
recompute
OOM
NCCL/HCCL
LMCache save/load/hit/miss
latency summary
success rate
```

## Report Rule

用户报告不得粘贴超过 40 行连续日志，只引用抽取结果和 raw log path。
