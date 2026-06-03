# Hook Spec: canonical_result_check

## Purpose

保证最终用户只看到唯一有效数据。

## Checks

```text
results/canonical/final_launch_command.sh exists
results/canonical/final_metrics.json or equivalent exists
results/canonical/run_manifest.yaml exists
canonical run_id traces to runs/raw/<run_id>
no failed run referenced in main tables
reports reference canonical paths
```

## Invalid Conditions

```text
serve failed
single request failed
wrong workload
missing logs
missing manifest
prefix cache expected but not hit and unexplained
obvious config error
```

## Failure

不能更新 canonical，结果留在 candidate 或 scratch_failed。
