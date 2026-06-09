# Stage 3：Engine Smoke Bring-up

## 目标

基于用户提供的基础 serve 命令，以保守方式启动服务，并用单请求验证 correctness。此阶段不追求性能。

## 必须执行

1. 将用户的基础启动命令保存为 `experiments/base_launch_command.sh`。
2. 启动服务，所有日志写入 `runs/attempts/<run_id>/serve.log`。
3. 如果启动失败，在最大尝试次数内只修改必要参数。
4. 启动成功后跑 single-request correctness test。
5. single-request 通过后粗略计算 decode speed。
6. 如果 engine 是 vLLM，立即对成功运行的 `serve.log` 执行固定日志抽取脚本，不要等到 Stage 4 临时生成解析逻辑：

```bash
python instrumentation/vllm_kv_log_extract.py \
  --log runs/attempts/<run_id>/serve.log \
  --out runs/attempts/<run_id>/vllm_kv_log_extract.json \
  --text-out runs/attempts/<run_id>/log_extract.txt
```

如果运行已晋级到 `runs/raw/<run_id>/`，必须同步保留 `vllm_kv_log_extract.json` 和 `log_extract.txt`。

## 最大迭代次数

```text
smoke_launch_max_attempts: 3
single_request_max_attempts: 3
```

超过上限停止，不继续盲试。

## 必须记录

```text
run_id
launch command
serve log path
client request
client response
log_extract.txt
vllm_kv_log_extract.json
single-request wall time
generated tokens
rough decode speed = max_tokens / wall_time
failure summary if failed
```

## 有效性规则

只有同时满足以下条件，才能把该运行从 `runs/attempts/` 晋级到 `runs/raw/`：

```text
server started
single request returned normally
output not乱码
no obvious tokenizer/chat template/parser error
log can be traced
```

失败运行默认只保留失败摘要和必要关键日志片段到 `runs/scratch_failed/`，不进入 canonical。

## 必须产出

```text
reports/smoke_check.md
reports/basic-info.md 中的 single-request decode speed 字段
```

## 完成条件

服务可启动，单请求正确，decode speed 有粗略记录，失败尝试没有污染 canonical。


## 通用限制

- 不修改推理引擎源码。
- 不把大段 raw log 放进 report。
- 不把失败/无效结果写入 canonical。
- 不用理论分析替代本阶段要求的真实执行证据。
- 超过配置中的最大迭代次数必须停止并总结。

## 报告要求

面向用户的 md 使用中文。图和表使用 academic English。术语首次出现给一句话解释。每个实验写清楚 Question、Bottleneck、Mechanism、Evidence、Contribution、Decision。
