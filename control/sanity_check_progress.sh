#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <run_name>"
  exit 1
fi

RUN_NAME="$1"
PROM_URL="http://localhost:9090"

QUERY="sum(task_executions_total{run=\"${RUN_NAME}\"})"

PROM_COUNT=$(curl -s "${PROM_URL}/api/v1/query" \
  --data-urlencode "query=${QUERY}" \
  | jq -r '.data.result[0].value[1] // "N/A"')

MINIO_COUNT=$(mc ls --recursive local/protein-pipeline/"${RUN_NAME}" | wc -l)

echo "Run                  : ${RUN_NAME}"
echo "Prometheus tasks     : ${PROM_COUNT}"
echo "MinIO objects stored : ${MINIO_COUNT}"
