# 横向规范：绘图与可视化报告

## 目标

用户最终只需要阅读 md 和其中插入的 png。raw data 和 raw log 保存用于追溯，但不作为主阅读入口。

## 绘图规范来源

如果项目根目录存在用户提供的：

```text
PLOT_STYLE.md
```

必须优先读取并遵守。当前文件只提供默认占位规范。

## 默认规范

```text
use matplotlib
save as png
no Chinese characters in figures
title / axis / legend / table header use academic English
one figure answers one question
avoid decorative plots
insert png directly into corresponding md
```

## 每阶段建议图

```text
Stage 4: kv_capacity_breakdown.png
Stage 5: workload_kv_pressure.png
Stage 6: baseline_latency_summary.png, prefix_cache_effect.png
Stage 7: parallelism_tradeoff.png
Stage 8: offload_ablation.png
Stage 9: parameter_tradeoff.png
Stage 10: final_overview.png
```

## 完成条件

如果阶段产生指标表，应尽量产生一个 summary png 并插入 md。图不存在时必须说明原因，例如数据不足、阶段为 plan-only、该指标不适合绘图。
