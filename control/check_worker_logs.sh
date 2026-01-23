#!/usr/bin/env bash
set -euo pipefail

CONTROL_DIR="$(cd "$(dirname "$0")" && pwd)"
INVENTORY="${CONTROL_DIR}/inventory.ini"
KEY="${HOME}/.ssh/id_cluster"

echo "Collecting worker logs (last 60 minutes)"
echo

ansible workers \
  -i "$INVENTORY" \
  --private-key "$KEY" \
  -m shell \
  -a "$(cat <<'EOF'
LOG_DIR="/var/log/protien_analysis_pipeline"
HOSTNAME="$(hostname)"
LOGFILE="${LOG_DIR}/pipeline_${HOSTNAME}.log"

echo "===== ${HOSTNAME} ====="

if [[ ! -f "$LOGFILE" ]]; then
  echo "No log file found at ${LOGFILE}"
  exit 0
fi

SINCE="$(date -d '60 minutes ago' '+%Y-%m-%d %H:%M:%S')"

awk -v since="$SINCE" '
  $0 ~ /^[0-9]{4}-/ && $0 >= since
' "$LOGFILE" | tail -n 200
EOF
)"
