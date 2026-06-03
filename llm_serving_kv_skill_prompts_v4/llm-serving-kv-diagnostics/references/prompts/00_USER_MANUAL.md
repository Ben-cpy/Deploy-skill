# 用户手册：如何运行这个 Workflow

## 这个 workflow 解决什么问题

它用于单节点场景下的 LLM serving 部署诊断：确认模型能否启动、KV cache 容量是否够、multi-turn agent 负载是否能稳定运行、LMCache 是否有收益，以及 vLLM/SGLang 参数是否值得调整。

## 用户需要提供什么

最少提供：

```text
基础 serve 启动命令
容器版本
推理引擎类型：vLLM / SGLang / others
后端类型：CUDA / CANN / ROCm / others
模型路径或模型名
端口和 model alias
multi-turn.py 路径，后续提供即可
```

如果已经安装好 vLLM、CANN、CUDA、模型，则在 `config/workflow.yaml` 中设置跳过安装或 acquisition 阶段。

## 用户主要看哪些文件

通常只看：

```text
README.md
reports/official_docs_lock.md
reports/basic-info.md
reports/workload_sizing.md
reports/baseline_kv_behavior.md
reports/parallelism_decision.md
reports/offload_decision.md
reports/parameter_decision.md
reports/final_deployment_card.md
PROCESS.md
```

一般不需要主动阅读：

```text
runs/raw/*.log
runs/attempts/*
runs/scratch_failed/*
中间命令 stdout 全量输出
```

raw log 会被保存或抽取，但报告中只展示关键指标、关键日志片段和图。

## 如何给修改意见

修改意见优先指向具体文件：

```text
修改 workload 配置 -> experiments/workload_*.yaml
修改启动参数 -> experiments/launch_*.sh 或 config/workflow.yaml
修改最终结论 -> reports/final_deployment_card.md
修改经验规则 -> PROCESS.md
```

如果修改涉及 `experiments/`、`runs/`、`results/`、`reports/`、`figures/`，完成时会触发 stop review check。

## 图和表

md 正文中文；图和表使用英文。所有 png 应直接插入 md，因此最终 review 时只看 md 即可。
