# Stage 10：Final Deployment Report

## 目标

生成唯一可信的最终部署卡片、中文长报告和 PDF。用户最终主要阅读 `reports/final_report.md` 和 `reports/final_report.pdf`，必要时再看 `reports/final_deployment_card.md`。

## 必须输出

```text
reports/final_deployment_card.md
reports/final_report.md
reports/final_report.pdf
results/canonical/final_launch_command.sh
results/canonical/final_metrics.json
results/canonical/run_manifest.yaml
figures/final_overview.png
```

如果 PDF 渲染工具缺失，必须保留 `reports/final_report.md`，并创建：

```text
reports/final_report_pdf_dependency_missing.md
```

说明尝试的渲染命令和缺少的依赖。不得因为缺少 PDF 工具而省略长报告内容。

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
usable context tokens / token-equivalent KV capacity as the primary capacity unit
single-request decode speed
low_load result
high_load result
high_session result
prefix cache validation
LMCache decision
known bad configs summary
final recommendation
```

## Final Report 必须包含

```text
中文正文
面向公司老板或业务负责人，语言克制、学术化、简洁、客观中立
按 Stage 1-10 线性组织
关键 png 直接插入 md
关键数据表来自 results/canonical/
最终启动命令
核心结论、适用边界、风险边界
failed/scratch 只作为 known bad 简短摘要
raw log 只给路径，不要求用户阅读
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
是否 config/workflow_manifest.json 中 required/approved 子任务全部 completed 或有明确用户接受的 skipped/blocked 记录
是否 reports/final_report.md 存在且引用 canonical 数据和关键 png
是否 reports/final_report.pdf 存在，或已记录 PDF 渲染依赖缺失
```


## 通用限制

- 不修改推理引擎源码。
- 不把大段 raw log 放进 report。
- 不把失败/无效结果写入 canonical。
- 不用理论分析替代本阶段要求的真实执行证据。
- 超过配置中的最大迭代次数必须停止并总结。

## 报告要求

面向用户的 md 使用中文。图和表使用 academic English。术语首次出现给一句话解释。每个实验写清楚 Question、Bottleneck、Mechanism、Evidence、Contribution、Decision。
