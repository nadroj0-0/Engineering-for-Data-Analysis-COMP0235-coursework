# Control Panel

This directory contains scripts for running, inspecting, and managing the pipeline.

All scripts are intended to be run **on the host node**, from within the cluster.

## Descriptions

- `run_pipeline.sh <run_name>`
  Launches the full production pipeline (~6000 sequences).
  Requires an explicit run name and includes a safety countdown.

- `pull_results.sh <run_name>`
  Retrieves final aggregated CSV outputs for a given run from MinIO to the host.

- `check_worker_logs.sh`
  Uses Ansible to fetch and display recent worker logs across all nodes.

Subdirectories:
- `cleaning/` – cleanup and reset scripts
- `testing/` – validation and test run scripts
