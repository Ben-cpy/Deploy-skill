# config/workflow.yaml template

engine: vllm
backend: cuda_or_cann
container: ""
model_path: ""
model_alias: ""
base_url: "http://127.0.0.1:8000/v1"
base_launch_command: ""

skip:
  engine_acquisition: true
  model_download: true
  lmcache: false
  parallelism_comparison: false

docs:
  require_official_docs_lock: true

budgets:
  smoke_launch_max_attempts: 3
  single_request_max_attempts: 3
  parallelism_configs_max: 3
  lmcache_bringup_max_attempts: 3
  parameter_trial_max: 6
  single_bottleneck_trial_max: 3

paths:
  multi_turn_py: "/workspace/multi-turn.py"
  reports_dir: "reports"
  figures_dir: "figures"
  attempts_dir: "runs/attempts"
  raw_runs_dir: "runs/raw"
  failed_runs_dir: "runs/scratch_failed"
  canonical_dir: "results/canonical"
  plot_style: "PLOT_STYLE.md"
