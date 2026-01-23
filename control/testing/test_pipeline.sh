#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "usage: $0 <num_sequences> [run_name]"
  exit 1
fi

NUM="$1"
RUN_NAME="${2:-}"

PIPELINE_SCRIPT="/shared/almalinux/scripts/celery/test_run_pipeline.py"

if [[ -n "$RUN_NAME" ]]; then
  exec python3 "$PIPELINE_SCRIPT" "$NUM" "$RUN_NAME"
else
  exec python3 "$PIPELINE_SCRIPT" "$NUM"
fi
