#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "usage: $0 <run_id> [--dry-run]"
  exit 1
fi

RUN_ID="$1"
DRY_RUN="${2:-}"

METRICS_DIR="/home/almalinux/custom_metrics"

if [[ ! -d "$METRICS_DIR" ]]; then
  echo "Metrics directory not found, nothing to clean."
  exit 0
fi

echo "Cleaning metrics for run:"
echo "  run=${RUN_ID}"
echo

for file in "$METRICS_DIR"/*.prom; do
  [[ -e "$file" ]] || continue

  if grep -q "run=\"${RUN_ID}\"" "$file"; then
    if [[ "$DRY_RUN" == "--dry-run" ]]; then
      echo "[DRY RUN] Would clean ${file}"
    else
      grep -v "run=\"${RUN_ID}\"" "$file" > "${file}.tmp"
      mv "${file}.tmp" "$file"
      echo "Cleaned ${file}"
    fi
  fi
done
