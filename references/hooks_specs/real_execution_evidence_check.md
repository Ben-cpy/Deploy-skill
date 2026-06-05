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

For each completed execution task in `config/workflow_manifest.json`, validate:

```text
status is completed/success/canonical
plan_only is false
run_id is present when the task launches or measures a service
command_file exists when command execution is required
raw_log or dry-run output exists
log_extract exists
metrics json/table exists for benchmark, workload, smoke, or tuning tasks
report md exists
required figure png exists and is referenced from a report
```

## Plan-only Exception

只有用户明确要求 plan-only / prompt-only / discussion-only 时，允许没有真实执行证据。

Plan-only tasks must be marked `plan_only: true` in the workflow manifest and must not be counted as completed execution tasks.
