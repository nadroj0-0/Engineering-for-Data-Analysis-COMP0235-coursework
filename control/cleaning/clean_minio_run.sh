#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "usage: $0 <run_id> [--dry-run]"
  exit 1
fi

RUN_ID="$1"
DRY_RUN="${2:-}"

ALIAS="local"
BUCKET="protein-pipeline"

echo "Cleaning MinIO objects:"
echo "  ${BUCKET}/${RUN_ID}/"
echo

if [[ "$DRY_RUN" == "--dry-run" ]]; then
  mc ls "${ALIAS}/${BUCKET}/${RUN_ID}/" || true
else
  mc rm --recursive --force "${ALIAS}/${BUCKET}/${RUN_ID}/"
  echo "MinIO objects deleted."
fi
