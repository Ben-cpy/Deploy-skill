# 横向规范：交互可读性、术语解释与论文主线贡献

## 目标

降低用户阅读 AI 文档和反复追问术语的成本。所有面向用户的 md 必须中文清晰、结论前置、证据明确。图和表使用学术英文。

## 术语首次出现规则

每个术语首次出现时给一句话解释。例如：

```text
TTFT（Time To First Token）：从请求发出到首个 token 返回的时间，主要反映 prefill 和调度开销。
ITL（Inter-token Latency）：相邻输出 token 之间的延迟，主要反映 decode 阶段速度。
KV cache：Transformer decode 时保存历史 key/value 的缓存，长上下文和多轮会显著消耗显存。
Preemption：KV cache 不足时，系统暂停或重算部分请求，通常导致 tail latency 变差。
```

解释应短，不写百科。

## 每个实验必须说明

```text
Question: 这个实验回答什么问题
Bottleneck: 对应具体瓶颈
Mechanism: 为什么这个实验能暴露瓶颈
Evidence: 看哪些命令、日志、指标、图
Contribution: 它对论文/项目主线的贡献
Decision: 继续、丢弃、重跑还是作为最终配置
```

## 论文主线贡献写法

不要写“该实验验证性能”。必须具体：

```text
该实验验证 high_session 场景下 CPU KV offload 是否能缓解 HBM KV residency 压力。
证据路径是：prefix hit log + CPU memory growth + preemption reduction + TTFT/ITL change。
如果 LMCache 只降低 OOM 但显著恶化 ITL，则说明 capacity 扩展和 decode latency 存在 tradeoff。
```

## 报告结构

每个阶段报告尽量使用：

```text
1. 一句话结论
2. 本阶段回答的问题
3. 关键结果表
4. 关键图
5. 证据路径
6. 决策
7. 下一步
```

## 图表规则

- md 正文中文。
- matplotlib 图中的 title、axis、legend、table header 使用英文。
- png 必须插入 md。
- 如果项目根目录存在 `PLOT_STYLE.md`，必须优先遵守。
- 如果没有，使用简洁学术风格，不使用中文字符。
