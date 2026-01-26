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
Uses Ansible to fetch and display recent (default : last 60 mins, tail 150) worker logs across all nodes.

Usage:
  ./check_worker_logs.sh [--since MINUTES] [--full]

Examples:
  ./check_worker_logs.sh
  ./check_worker_logs.sh --since 120
  ./check_worker_logs.sh --full
  ./check_worker_logs.sh --since 480 --full

### `check_celery_logs.sh`
Uses Ansible to fetch and display recent (default : tail 150) Celery worker logs across all nodes.

Usage:
  ./check_celery_logs.sh [--since MINUTES] [--full]

Examples:
  ./check_celery_logs.sh
  ./check_celery_logs.sh --since 120
  ./check_celery_logs.sh --full
  ./check_celery_logs.sh --since 480 --full

### `check_storage_logs.sh`
Displays recent (default : last 60 mins, tail 150) storage logs (NFS / MinIO write activity).

Usage:
  ./check_storage_logs.sh [--since MINUTES] [--full]

Examples:
  ./check_storage_logs.sh
  ./check_storage_logs.sh --since 120
  ./check_storage_logs.sh --full
  ./check_storage_logs.sh --since 480 --full


### sanity_check_progress.sh
Sanity check to compare Prometheus task completion count with MinIO object count for a run.

Usage:
  ./sanity_check_progress.sh <run_name>


### run_fasta_pipeline.sh
Runs the pipeline on sequences defined in a FASTA file by extracting sequence IDs and executing the standard database backed pipeline.

Usage:
  ./run_fasta_pipeline.sh <fasta_file> [run_name]


##Subdirectories:
- `cleaning/` – cleanup and reset scripts
- `testing/` – validation and test run scripts
