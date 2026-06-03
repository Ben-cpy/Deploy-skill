# Hook Spec: no_source_edit_guard

## Purpose

防止部署任务越界修改推理引擎源码。部署 workflow 只能改启动命令、配置、实验脚本、日志解析、report 和 instrumentation，不做 engine development。

## Blocked Paths

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
site-packages/transformers
site-packages/torch
```

## Allowed Paths

```text
instrumentation/
experiments/
reports/
figures/
runs/
results/
config/
hooks/
templates/
prompts/
```

## Exception

Profiling 需要 hack 时，只能新增 monkey patch 到 `instrumentation/`。monkey patch 必须可开关、可回滚、记录启用方式和风险。不得直接 patch engine source 文件。

## Failure Behavior

发现 blocked path 修改时，立即失败，不能进入 stop success。输出 blocked files 和建议移动到 `instrumentation/` 的替代方式。
