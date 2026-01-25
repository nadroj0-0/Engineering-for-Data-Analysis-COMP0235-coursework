#!/usr/bin/env bash
set -euo pipefail


PYTHON_SCRIPT="/shared/almalinux/scripts/celery/lecturer_example_validation.py"
FASTA_FILE="/home/almalinux/pipeline_example/test.fa"
RUN_NAME="lecturer_example"


if [[ ! -f "$PYTHON_SCRIPT" ]]; then
  echo "ERROR: Validation Python script not found:"
  echo "  $PYTHON_SCRIPT"
  exit 1
fi

if [[ ! -f "$FASTA_FILE" ]]; then
  echo "ERROR: Lecturer example FASTA not found:"
  echo "  $FASTA_FILE"
  exit 1
fi

echo "=============================================="
echo "Lecturer example validation run"
echo
echo "FASTA file : $FASTA_FILE"
echo "Run name   : $RUN_NAME"
echo
echo "This will run the pipeline on a single sequence"
echo "and allow comparison with lecturer reference."
echo "=============================================="
echo


exec python3 "$PYTHON_SCRIPT" "$FASTA_FILE" "$RUN_NAME"
