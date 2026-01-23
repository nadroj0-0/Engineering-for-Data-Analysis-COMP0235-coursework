#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "usage: $0 <run_id> [--dry-run]"
  exit 1
fi

RUN_ID="$1"
DRY_RUN="${2:-}"

RUN_DIR="/shared/almalinux/runs/${RUN_ID}"

if [[ ! -d "$RUN_DIR" ]]; then
  echo "ERROR: run directory not found:"
  echo "  $RUN_DIR"
  exit 1
fi

echo "Cleaning run directory:"
echo "  $RUN_DIR"
echo

if [[ "$DRY_RUN" == "--dry-run" ]]; then
  echo "[DRY RUN] Would remove:"
  find "$RUN_DIR"
else
  rm -rf "$RUN_DIR"
  echo "Run directory deleted."
fi
