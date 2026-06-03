# Project README Template

## 当前目标

单节点 LLM serving / KV cache 诊断。

## 如何运行

1. 填写 `config/workflow.yaml`。
2. 运行 Stage 1 锁定官方文档和 scope。
3. 按 `00_WORKFLOW_MAP.md` 顺序执行。
4. 每阶段只读当前阶段 prompt 和必要横向规范。
5. 用户只 review `reports/` 和嵌入的 `figures/`。

## 用户主要查看

```text
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

## 原始数据

raw log 在 `runs/raw/`，失败/无效运行的必要摘要在 `runs/scratch_failed/`，最终有效结果在 `results/canonical/`。
