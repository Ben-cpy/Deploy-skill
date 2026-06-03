# Hook Spec: process_compaction_check

## Purpose

维护 PROCESS.md，避免经验教训膨胀。

## Rule

```text
每次 commit 或阶段结束追加 1-3 条重要经验
每条不超过两行
总条数超过 20 条时删除最早 10 条
```

## Failure

PROCESS.md 过长或未维护时，stop review check 应提示但不自动改写用户内容，除非任务要求修改。
