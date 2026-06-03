# Stage 5：Workload Sizing with multi-turn.py

## 目标

用 `multi-turn.py --dry-run` 将 agent-style multi-turn workload 转成 KV pressure model，然后生成 low_load、high_load、high_session 三类负载配置。

## 输入

```text
/workspace/multi-turn.py 或用户指定路径
reports/basic-info.md 中的 KV capacity
model tokenizer path
base url / model alias
```

`multi-turn.py` 的具体内容由用户后续提供。本阶段只要求 workflow 预留接口。

## 必须执行

只使用 `--dry-run`，不发送真实 benchmark 请求。

重点读取最后一轮：

```text
prompt_tokens
reusable_tokens
nominal_hit_rate
peak_kv/request
peak_kv@req_conc
peak_kv@active_sess
cold-start upper bound
steady-state upper bound
```

## 生成三类负载

```text
low_load:
request_concurrency == active_sessions == num_sessions
peak_kv@req_conc ≈ 80% × system_KV_capacity

high_load:
request_concurrency == active_sessions == num_sessions
peak_kv@req_conc ≈ 150% × system_KV_capacity

high_session:
active_sessions == num_sessions > request_concurrency
active_sessions 通常取 request_concurrency 的 3 倍
在 high_load 基础上提高 active_sessions / num_sessions
```

## 每个负载必须说明

```text
Question: 这个负载回答什么问题
Bottleneck: KV capacity / residency / prefix reuse 哪个瓶颈
Mechanism: 为什么该负载能暴露瓶颈
Evidence: dry-run 输出中的哪几列支持
Contribution: 对论文/项目主线贡献什么证据
```

## 必须产出

```text
experiments/workload_low_load.yaml
experiments/workload_high_load.yaml
experiments/workload_high_session.yaml
reports/workload_sizing.md
figures/workload_kv_pressure.png
```

## 完成条件

三类 workload 配置生成，且每个配置都有 dry-run 证据、KV pressure 解释和目标问题。没有 `multi-turn.py` 时，只能产出待填模板，不能假装已完成 sizing。


## 通用限制

- 不修改推理引擎源码。
- 不把大段 raw log 放进 report。
- 不把失败/无效结果写入 canonical。
- 不用理论分析替代本阶段要求的真实执行证据。
- 超过配置中的最大迭代次数必须停止并总结。

## 报告要求

面向用户的 md 使用中文。图和表使用 academic English。术语首次出现给一句话解释。每个实验写清楚 Question、Bottleneck、Mechanism、Evidence、Contribution、Decision。
