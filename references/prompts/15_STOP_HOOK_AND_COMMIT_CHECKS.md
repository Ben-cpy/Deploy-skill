# 横向规范：Stop Hook 与 Commit Check

## 目标

防止长时间执行后，agent 在 context 压缩或多轮修改中遗忘规范。每次执行任务结束、准备 stop 前，强制检查输入要求、AGENTS.md、输出目录和结果完整性。

## 触发条件

Stop hook 只在特定行为触发：

```text
触发：
- workflow 已过 Stage 1
- 正在执行真实任务，而不是纯讨论
- 修改了 experiments/、runs/、results/、reports/、figures/ 任一目录
- 用户 review 后要求修改实验文件或结果文件

不触发：
- 纯概念讨论
- 纯计划讨论
- 只编辑 prompt 文档
- 尚未进入执行阶段
```

## Stop 前检查

必须检查：

```text
1. 是否读取了当前阶段 prompt 和必要横向规范
2. 是否遵守官方文档优先
3. 是否修改了推理引擎源码
4. 是否 raw log 已保存
5. 是否从大日志中抽取关键指标
6. 是否 report 中文、图表英文
7. 是否图已插入 md
8. 是否 canonical 只有唯一有效结果
9. 是否失败数据隔离到 scratch_failed 且未进入主报告
10. 是否 PROCESS.md 已更新并压缩
11. 是否每个实验回答了具体问题
12. 是否每个任务有真实执行证据
13. 是否遵守最大迭代次数
14. 是否 `config/workflow_manifest.json` 中 required/approved 子任务已完成，或明确 skipped/blocked
15. 是否所有 benchmark/workload/trial 按串行假设运行；非标准并发数据是否隔离标注
16. 是否最终交付物包含 `reports/final_report.md` 和 `reports/final_report.pdf` 或 PDF 依赖缺失说明
```

## PROCESS.md 压缩规则

每次 commit 或阶段结束：

```text
新增 1-3 条最重要经验
每条不超过两行
总条数 <= 20 时保留
总条数 > 20 时删除最早 10 条
```

PROCESS.md 不写流水账，只写会影响后续执行质量的经验。

## 输出

如果检查通过，写入：

```text
reports/stop_check_summary.md
```

如果检查失败，不能宣称任务完成，必须列出 blocking items。

## Manifest 阻断规则

执行阶段 stop 前必须读取 `config/workflow_manifest.json`。当 required/approved 子任务仍为 `pending`、`in_progress`、`attempt`、`failed` 或缺少 required artifact/evidence 时，Stop hook 必须阻断 final response，并输出 remaining tasks、missing artifacts 和 recommended next action。

纯讨论、纯规划、只编辑 prompt 文档、尚未进入执行阶段时可以跳过重型 manifest 检查。
