# 横向规范：Guardrails, Hooks, Hard Budgets

## 硬约束优先

优先使用 hook、脚本、目录权限、检查器实现约束。prompt 只作为第二层约束。关键安全和流程规则不能只写进 AGENTS.md。

## 禁止修改源码

禁止修改：

```text
vllm/
sglang/
lmcache/
mooncake/
transformers/
torch/
flashinfer/
site-packages/vllm
site-packages/sglang
site-packages/lmcache
vendor runtime source
```

允许：

```text
新增实验脚本
新增配置文件
新增 launch command
新增 instrumentation/ 下 monkey patch
新增 log parser
新增 report / figures
```

Monkey patch 限制：

```text
必须在 instrumentation/
必须可开关
必须记录启用方式
必须说明风险
不得成为最终部署默认依赖，除非用户明确接受
```

## 最大迭代次数

```text
smoke_launch_max_attempts: 3
single_request_max_attempts: 3
parallelism_configs_max: 3
lmcache_bringup_max_attempts: 3
mooncake_bringup_max_attempts: 3
parameter_trial_max: 6
single_bottleneck_trial_max: 3
```

超过上限必须停止并总结，不继续盲试。

## Stop hook 触发范围

只在真实执行任务阶段触发：

```text
stage >= 2
且产生或修改 experiments/、runs/、results/、reports/、figures/ 中任一文件
或用户 review 后要求修改实验/结果文件
```

不在以下情况触发：

```text
纯讨论
纯阅读
纯规划且未修改实验文件
只修改 prompt 文档
尚未进入执行阶段
```

## 串行 Benchmark 规则

所有 benchmark/workload/trial 默认串行运行。运行前确认没有其他 active run 使用同一服务端口、同一 GPU/Ascend 设备、同一模型服务或同一输出目录。若 `.codex_runtime/active_benchmark_run.json` 存在且未释放，不能启动或 finalize 可比实验结果。

并发只允许在用户明确要求 stacked-load / 叠加压力测试时使用，并且必须标记为非标准数据，不得进入标准主比较表。

## Manifest 规则

执行阶段必须维护 `config/workflow_manifest.json`：

```text
required/approved 子任务未完成 -> 不得 final
completed execution task 缺 command/run_id/log_extract/metrics/report/figure -> 不得 final
plan_only 必须由用户明确要求，且不能算作真实执行完成
blocked/skipped 必须写 blocked_reason 或用户接受原因
```

## PROCESS.md 规则

每个 commit 或阶段结束时更新 PROCESS.md。总条数超过 20 条时，删除最早 10 条。

## 完成前硬检查

```text
official docs locked?
no source edit?
logs persisted?
log extraction done?
canonical result unique?
figures embedded?
terms explained?
PROCESS.md updated and compacted?
real execution evidence exists?
workflow manifest complete?
benchmark serial execution respected?
final_report.md and PDF or dependency note exist?
stop hook condition matched?
```
