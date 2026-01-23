#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <protein_id>"
  exit 1
fi

PROTEIN_ID="$1"
RUN_NAME="lecturer_example_fasta"

PIPELINE_SCRIPT="/shared/almalinux/scripts/celery/run_pipeline_host.py"
TMP_IDS="/tmp/experiment_ids_${RUN_NAME}.txt"

echo "Validating protein exists in database..."

COUNT=$(psql -tA \
  -d pipeline_db \
  -U host \
  -c "SELECT COUNT(*) FROM proteins WHERE id='${PROTEIN_ID}';")

if [[ "$COUNT" != "1" ]]; then
  echo "ERROR: protein ID not found in database:"
  echo "  ${PROTEIN_ID}"
  exit 1
fi

echo "Protein found."
echo "Creating experiment ID file: ${TMP_IDS}"

echo "${PROTEIN_ID}" > "${TMP_IDS}"

echo
echo "Launching lecturer reference validation run"
echo "  Protein ID: ${PROTEIN_ID}"
echo "  Run name:   ${RUN_NAME}"
echo

exec python3 "${PIPELINE_SCRIPT}" "${TMP_IDS}" "${RUN_NAME}"
