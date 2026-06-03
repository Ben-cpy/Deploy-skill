# Hook Spec: stop_review_check

## Trigger

只在真实执行阶段触发：workflow stage >= 2，且修改了 experiments/runs/results/reports/figures，或用户 review 后要求修改实验/结果。

不因纯讨论、纯规划、只编辑 prompt 文档而触发。

## Checks

```text
official docs lock exists
no forbidden source changes
raw logs saved or failed logs summarized
log extracts generated
canonical uniqueness holds
reports reference figures if figures exist
PROCESS.md <= 20 bullets or compacted
terms explained in user-facing md
real execution evidence exists
hard budgets not exceeded
```

## Failure

输出 blocking items，不能标记任务完成。
