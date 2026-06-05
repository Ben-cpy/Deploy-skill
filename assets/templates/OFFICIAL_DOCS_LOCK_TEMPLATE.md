# Official Docs Lock Template

## Scope

| Item | Value |
|---|---|
| Engine |  |
| Backend |  |
| Model |  |
| Offload Tool |  |
| Container |  |

## Sources

| Component | Source | Type | URL or Local Path | Version/Commit/Date | Used For | Uncertainty |
|---|---|---|---|---|---|---|
| Engine |  | official docs |  |  | launch command, serving flags, logging behavior |  |
| Backend |  | official docs |  |  | CUDA/CANN/ROCm integration and runtime limits |  |
| Model |  | model card |  |  | model-specific deployment notes and tokenizer/path assumptions |  |
| LMCache |  | official docs |  |  | single-node offload command and connector behavior, if enabled |  |
| Mooncake |  | official docs |  |  | only when user explicitly enables Mooncake/multi-node extension |  |

Allowed source types: `official docs`, `official repo`, `model card`, `user provided`, `auxiliary`. At least engine, backend, and model must not all be auxiliary.

## Launch Command Alignment

| Component | Official Command or Example | Project Command | Difference / Reason | Accepted Risk |
|---|---|---|---|---|
| Engine |  |  |  |  |
| Backend |  |  |  |  |
| Model |  |  |  |  |
| Offload |  |  |  |  |

## Extracted Rules

- 

## Mooncake Scope

Mooncake is out of the default single-node workflow. Only fill this section when the user explicitly enables Mooncake or a multi-node/offload extension.

```text
enabled: false
official_docs_entry:
command_source:
max_attempts:
failure_summary:
fallback_decision:
```

## Search Boundary

后续检索优先在上述官方来源和对应官方仓库内进行。社区内容只能辅助解释，不作为第一依据。
