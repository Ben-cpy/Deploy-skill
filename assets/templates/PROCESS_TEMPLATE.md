# PROCESS.md

## 最近经验教训

- [INIT] 不要把 DP aggregate KV capacity 误写成单 session 可用 KV capacity；DP 只增加 aggregate capacity，session 可用容量依赖 routing/session affinity。
- [INIT] prefix cache 未确认命中前，不能评价 LMCache 是否有效。
- [INIT] 失败或无效运行只能留下简短失败摘要和必要 debug 路径，不进入 canonical 和用户主报告。
- [INIT] 每个执行类任务必须有 run_id、command、log extract、metrics 或 figure 作为证据。

## 维护规则

- 每次阶段结束或 commit 追加 1-3 条真正影响后续执行质量的经验。
- 每条最多两行，不写流水账。
- 总条数超过 20 条时，删除最早 10 条。
- stop hook 必须检查本文件是否已更新或确认无需更新。
