# Stage 2：Environment & Stack Locking

## 目标

在用户指定容器内部锁定当前可见环境，确认后续实验的解释边界。这里不做泛化硬件巡检，只记录当前容器看到的事实。

## 输入

```text
container image/version
base launch command
model path
engine/backend choice
skip flags from config/workflow.yaml
```

## 必须执行

用真实命令收集：

```text
CPU model
OS / kernel
Python version
PyTorch version
CUDA / CANN / ROCm version
GPU / NPU model
visible device count
per-device HBM
NCCL / HCCL availability
engine version
model path existence
disk / memory availability
```

## 必须产出

```text
reports/environment_fingerprint.md
reports/software_stack.md
runs/raw/<run_id>/environment_commands.sh
runs/raw/<run_id>/environment_stdout.log
```

## 完成条件

报告必须能说明：当前容器、engine、backend、model 是否一致；如果用户已经安装好 vLLM/CANN/model，必须标记相关安装步骤为 skipped，而不是重复执行。


## 通用限制

- 不修改推理引擎源码。
- 不把大段 raw log 放进 report。
- 不把失败/无效结果写入 canonical。
- 不用理论分析替代本阶段要求的真实执行证据。
- 超过配置中的最大迭代次数必须停止并总结。

## 报告要求

面向用户的 md 使用中文。图和表使用 academic English。术语首次出现给一句话解释。每个实验写清楚 Question、Bottleneck、Mechanism、Evidence、Contribution、Decision。
