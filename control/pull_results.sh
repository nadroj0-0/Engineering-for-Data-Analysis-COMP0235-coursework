#!/bin/bash
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "usage: ./pull_results.sh <run_id>"
  exit 1
fi

RUN_ID="$1"

python3 ~/shared/scripts/pull_results.py "$RUN_ID"
