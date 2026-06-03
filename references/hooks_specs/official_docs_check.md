# Hook Spec: official_docs_check

## Purpose

确保官方文档是第一依赖规范。

## Required File

```text
reports/official_docs_lock.md
```

## Required Fields

```text
engine official docs or repo
backend official docs
model card or official repo
offload tool docs if used
version / commit / date if available
rules extracted for this workflow
uncertainties
```

## Trigger

进入 Stage 2 之后的部署、offload、参数调优前检查。若不存在，阻塞执行。
