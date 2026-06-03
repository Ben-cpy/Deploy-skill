# Workflow Map：只读宏观流程

## 一句话目标

用单节点、KV pressure-driven 的方法，把新硬件/新模型/新推理引擎的部署过程变成可复现、可解释、可停止的实验流程。

## 主流程

```text
1. Official Docs & Scope Lock
2. Environment & Stack Locking
3. Engine Smoke Bring-up
4. Model Memory & KV Cache Estimate
5. Workload Sizing with multi-turn.py
6. Baseline KV-oriented Load Test
7. Parallelism Comparison
8. KV Cache Offload Extension
9. Targeted vLLM Parameter Tuning
10. Final Deployment Report
```

## 核心证据链

```text
官方文档锁定 -> 环境锁定 -> smoke 正确性 -> 模型结构/KV 估算 -> runtime KV 日志校准 -> multi-turn dry-run KV pressure -> low/high/high_session 真实负载 -> baseline 退化模式 -> parallelism 对比 -> LMCache A/B -> 参数保留/丢弃 -> final deployment card
```

## 不做什么

- 不做多节点主流程；Mooncake 只留未来扩展。
- 不修改推理引擎源码。
- 不做无脑全排列 sweep。
- 不在 smoke 未通过时跑负载。
- 不在 prefix cache 未确认命中时评价 LMCache。
- 不把失败/无效数据放进最终主报告。

## 关键思想

实验不围绕“画性能曲线”展开，而围绕 KV pressure 展开。先建立系统 KV capacity 和 workload peak KV pressure 的对应关系，再判断 baseline、parallelism、offload、参数是否改变了真实瓶颈。
