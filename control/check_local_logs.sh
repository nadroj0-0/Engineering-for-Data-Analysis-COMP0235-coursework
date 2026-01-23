#!/usr/bin/env bash
set -euo pipefail

HOSTNAME="$(hostname)"
LOG_DIR="/var/log/protien_analysis_pipeline"
LOGFILE="${LOG_DIR}/pipeline_${HOSTNAME}.log"

echo "===== ${HOSTNAME} ====="

if [[ ! -f "$LOGFILE" ]]; then
    echo "No log file found at ${LOGFILE}"
    exit 0
fi

echo "Latest log: ${LOGFILE}"
echo "---- last 60 minutes ----"

# ISO timestamp from 20 minutes ago
SINCE="$(date -d '60 minutes ago' '+%Y-%m-%d %H:%M:%S')"

# Print only relevant lines, cap output to avoid terminal spam
awk -v since="$SINCE" '
    $0 ~ /^[0-9]{4}-[0-9]{2}-[0-9]{2}/ && $0 >= since
' "$LOGFILE" | tail -n 200

echo
