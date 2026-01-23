# Control Panel

This directory contains scripts for running, inspecting, and managing the pipeline.

All scripts are intended to be run **on the host node**, from within the cluster.


## Core Scripts

### `run_pipeline.sh <run_name>`

Launches the full production pipeline (~6000 sequences).

- Requires an explicit run name and includes a safety countdown.
- Uses predefined experiment ID list (~/data/experiment_ids.txt)
- Includes safety countdown to prevent accidental submission
- Submits all tasks via Celery chord and triggers final aggregation, outputs are stored in MinIO

### `pull_results.sh <run_name>`
Retrieves final aggregated CSV outputs for a given run from MinIO to the host.
- Downloads:
  - `<run_name>_hits_output.csv`
  - `<run_name>_profile_output.csv`
- Stores results locally under:
  ~/results/<run_name>

### `check_worker_logs.sh`
Uses Ansible to fetch and display recent (last 60 mins) worker logs across all nodes.


##Subdirectories:
- `cleaning/` – cleanup and reset scripts
- `testing/` – validation and test run scripts
