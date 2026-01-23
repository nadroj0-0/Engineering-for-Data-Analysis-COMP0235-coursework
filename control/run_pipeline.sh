#!/usr/bin/env bash
set -euo pipefail

echo "WARNING: This deploys the full analysis (~6000 tasks)."
echo "Analysis will start in 15 seconds"
echo "Press Ctrl+C now if this was not intentional."
sleep 15


if [[ $# -ne 1 ]]; then
  echo "usage: $0 <run_name>"
  echo "ERROR: run_name is mandatory for full pipeline runs"
  exit 1
fi

RUN_NAME="$1"

EXPERIMENT_IDS="/home/almalinux/data/experiment_ids.txt"
PIPELINE_SCRIPT="/shared/almalinux/scripts/celery/run_pipeline_host.py"

if [[ ! -f "$EXPERIMENT_IDS" ]]; then
  echo "ERROR: experiment ID file not found:"
  echo "  $EXPERIMENT_IDS"
  exit 1
fi

echo "Launching FULL pipeline run"
echo "Run name:      $RUN_NAME"
echo "Experiment IDs: $EXPERIMENT_IDS"
echo

exec python3 "$PIPELINE_SCRIPT" "$EXPERIMENT_IDS" "$RUN_NAME"
