# 初始化 Prompt：安装 Skill 后的项目设置

## 目标

在项目顶层创建一个轻量但硬约束明确的 LLM serving KV 诊断工作区。初始化阶段只做目录、模板、hook 规范、README、AGENTS、PROCESS，不执行部署实验。

## 必须创建的顶层文件

```text
README.md
AGENTS.md
PROCESS.md
config/workflow.yaml
```

README.md 面向用户，说明整体流程、如何操作、最终看哪些报告。AGENTS.md 面向 agent，只保留压缩版规则、当前阶段入口和 stop 前检查要求。PROCESS.md 记录经验教训和反复犯错点。config/workflow.yaml 控制 engine、backend、model、container、跳过项、最大迭代次数、输出目录。

## 必须创建的目录

```text
prompts/
hooks/
templates/
experiments/
instrumentation/
runs/attempts/
runs/raw/
runs/scratch_failed/
results/canonical/
reports/
figures/
config/
```

目录含义：

- `prompts/`：按阶段存放 prompt，按需读取。
- `hooks/`：放硬约束检查脚本或 hook 配置。
- `templates/`：放 report、manifest、experiment card、deployment card 模板。
- `experiments/`：放实验配置，不放 raw log。
- `instrumentation/`：放 monkey patch 或 profiling hack；不得修改 engine 源码。
- `runs/attempts/`：运行中的临时结果。
- `runs/raw/`：通过有效性检查的成功运行原始材料。
- `runs/scratch_failed/`：失败/无效运行的隔离区。默认只保留必要失败摘要和关键日志片段，避免长期堆积垃圾数据。
- `results/canonical/`：只放唯一有效结果。
- `reports/`：放用户阅读的中文 md。
- `figures/`：放英文标签 matplotlib png，并在 md 中引用。

## 必须创建的 hook 或等价检查器

优先使用硬机制，不要只依赖 prompt。

```text
hooks/no_source_edit_guard
hooks/official_docs_check
hooks/log_extraction_check
hooks/canonical_result_check
hooks/process_compaction_check
hooks/stop_review_check
hooks/plot_report_check
hooks/real_execution_evidence_check
```

最低行为：

- `no_source_edit_guard`：禁止修改 vLLM、SGLang、LMCache、Mooncake、Transformers、Torch、FlashInfer 等源码目录。允许新增 `instrumentation/` 下可开关 monkey patch。
- `official_docs_check`：进入部署、调参、offload 前检查是否存在 `reports/official_docs_lock.md`。
- `log_extraction_check`：禁止 report 中粘贴长日志，必须生成关键日志抽取文件。
- `canonical_result_check`：只有通过有效性检查的结果才能进入 `results/canonical/`。
- `process_compaction_check`：PROCESS.md 超过 20 条时删除最早 10 条。
- `stop_review_check`：只在真实执行阶段触发，触发条件见 `15_STOP_HOOK_AND_COMMIT_CHECKS.md`。
- `plot_report_check`：检查 png 是否插入对应 md，图表是否使用英文。
- `real_execution_evidence_check`：执行类任务没有 command、run_id、log extract、metrics/figure 时不得完成。

## AGENTS.md 内容边界

AGENTS.md 不要复制所有阶段 prompt，只保留：

```text
1. 当前 workflow 的一句话目标
2. 必须遵守的硬约束
3. 当前阶段应该读取哪个 prompt 文件
4. 禁止修改推理引擎源码
5. 输出目录规则
6. stop 前检查触发条件
```

详细阶段说明按需读取，避免上下文膨胀。

## 初始化完成条件

必须创建所有顶层文件、目录、模板和 hook 规范。初始化阶段不能启动 vLLM/SGLang，不能跑 benchmark，不能修改推理引擎源码。
