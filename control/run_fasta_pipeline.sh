#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: ./run_fasta.sh <fasta_file> [run_name]"
  exit 1
fi

FASTA_FILE="$1"
RUN_NAME="${2:-}"

EXTRACT_SCRIPT="/shared/almalinux/scripts/extract_ids_from_fasta.py"
PIPELINE_SCRIPT="/shared/almalinux/scripts/celery/run_pipeline_host.py"

if [[ ! -f "$FASTA_FILE" ]]; then
  echo "ERROR: FASTA file not found: $FASTA_FILE"
  exit 1
fi

echo "Extracting experiment IDs from FASTA..."
IDS_FILE=$(python3 "$EXTRACT_SCRIPT" "$FASTA_FILE")

echo "Generated experiment ID file:"
echo "  $IDS_FILE"

cmd=(python3 "$PIPELINE_SCRIPT" "$IDS_FILE")
[[ -n "$RUN_NAME" ]] && cmd+=("$RUN_NAME")

echo "Launching pipeline:"
echo "  ${cmd[*]}"

exec "${cmd[@]}"
