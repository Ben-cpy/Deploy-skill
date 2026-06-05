# Final Report

## 摘要

用中文写一页以内的客观摘要：目标、环境、推荐配置、关键收益、主要风险和证据边界。不要引入没有 canonical 数据支持的结论。

## 1. Official Docs & Scope Lock

引用 `reports/official_docs_lock.md` 和 `reports/scope_lock.md`。说明 engine、backend、model、offload 是否进入 scope，以及启动命令来自官方文档、官方仓库示例还是用户提供命令。

## 2. Environment & Stack Locking

总结硬件、容器、驱动、runtime、模型路径和端口。只放关键表，完整命令和 raw log 用路径引用。

## 3. Engine Smoke Bring-up

说明推荐启动命令是否可稳定启动、单请求是否正确、失败尝试是否被隔离。

## 4. Model Memory & KV Cache Estimate

插入关键 KV capacity 图和表。解释 per-DP KV capacity、aggregate KV capacity、max model length 与 workload pressure 的关系。

## 5. Workload Sizing

列出 low_load、high_load、high_session 的 token/session/concurrency 定义和选择理由。

## 6. Baseline KV Load Test

只引用 canonical baseline 数据。插入 `figures/baseline_latency_summary.png` 等关键图，说明 prefix cache、preemption/recompute、OOM 或 worker crash 证据。

## 7. Parallelism Comparison

若执行，说明最多三组 TP/DP 对比的 keep/drop/uncertain 结论。若跳过，说明跳过原因来自 scope、budget 或用户要求。

## 8. KV Cache Offload Extension

默认只总结单节点 LMCache。Mooncake 只在用户明确启用 multi-node/offload extension 时出现；若失败，给出命令来源、最大尝试次数、失败摘要和降级结论。

## 9. Targeted Parameter Tuning

说明每个保留参数对应的瓶颈、证据和副作用。不要因为平均值改善就忽略 correctness、tail latency、cache hit 或稳定性。

## 10. Final Deployment Recommendation

给出最终启动命令、推荐参数、适用 workload 边界、已知坏配置、风险和下一步建议。所有结论都必须指向 canonical 指标、报告或图。

## Evidence Index

| Item | Path |
|---|---|
| Official docs lock | `reports/official_docs_lock.md` |
| Workflow manifest | `config/workflow_manifest.json` |
| Final launch command | `results/canonical/final_launch_command.sh` |
| Final metrics | `results/canonical/final_metrics.json` |
| Run manifest | `results/canonical/run_manifest.yaml` |

## PDF Rendering

Preferred output: `reports/final_report.pdf`.

If `pandoc`, `typst`, or another configured renderer is unavailable, keep this Markdown report and create `reports/final_report_pdf_dependency_missing.md` with the missing dependency and attempted command.
