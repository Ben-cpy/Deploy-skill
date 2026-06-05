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
official launch command or official example
project launch command
command difference / reason / accepted risk
uncertainties
```

Source type must be one of:

```text
official docs
official repo
model card
user provided
auxiliary
```

Engine, backend, and model entries must not all be auxiliary/community sources. Stage 3, Stage 8, and Stage 9 reports must cite the corresponding `official_docs_lock.md` command alignment entry or explain why the user-provided command differs from the official example.

## Trigger

进入 Stage 2 之后的部署、offload、参数调优前检查。若不存在，阻塞执行。
