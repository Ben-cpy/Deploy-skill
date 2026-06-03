# Run Manifest Template

run_id: "YYYYMMDD_HHMMSS_stage_config"
stage: ""
config_name: ""
command_file: "runs/raw/<run_id>/command.sh"
serve_log: "runs/raw/<run_id>/serve.log"
client_log: "runs/raw/<run_id>/client.log"
log_extract: "runs/raw/<run_id>/log_extract.txt"
metrics_raw: "runs/raw/<run_id>/metrics_raw.json"
status: "attempt | success | failed | invalid | candidate | canonical"
validity_reason: ""
question: ""
bottleneck: ""
mechanism: ""
evidence_paths: []
notes: ""
