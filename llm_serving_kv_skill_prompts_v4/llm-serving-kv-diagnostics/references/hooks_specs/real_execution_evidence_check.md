# Hook Spec: real_execution_evidence_check

## Purpose

防止执行类子任务没有真实证据却被标记完成。

## Required Evidence

```text
run_id
command.sh
log_extract.txt
metrics table or parsed json
report md
figure png if required
```

## Plan-only Exception

只有用户明确要求 plan-only / prompt-only / discussion-only 时，允许没有真实执行证据。
