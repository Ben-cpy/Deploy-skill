# 横向规范：真实执行证据，避免虚空任务

## 目标

防止子任务只做理论分析、没有真实执行，却被标记为完成。除非任务明确声明 plan-only，否则每个阶段必须有可追溯执行证据。

## 执行类任务完成证据

至少包含：

```text
run_id
command.sh
raw log path 或 dry-run output path
log_extract.txt
metrics table 或 parsed json
report md
figure png if visualization is required
```

## 分析类任务完成证据

如果任务确实是分析类，例如模型结构检索，也必须包含：

```text
official docs source
model structure table
assumption list
calculation formula
runtime log calibration if available
uncertainty statement
```

## 不允许的完成方式

```text
只写“理论上应该可以”
只写“建议跑某命令”但没有执行证据
只写“可能是 KV cache 问题”但没有日志抽取
只写“LMCache 有收益”但没有 baseline A/B
只写“参数调优有效”但没有同负载对比
```

## 每个实验卡片必须包含

```text
Question
Bottleneck
Mechanism
Evidence
Contribution
Decision
```
