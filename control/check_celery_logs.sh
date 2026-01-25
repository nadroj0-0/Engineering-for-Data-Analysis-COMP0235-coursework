#!/usr/bin/env bash
set -euo pipefail

CONTROL_DIR="$(cd "$(dirname "$0")" && pwd)"
INVENTORY="${CONTROL_DIR}/inventory.ini"
KEY="${HOME}/.ssh/id_cluster"

# Defaults
LOOKBACK_MINUTES=""
USE_TAIL=1
TAIL_LINES=150

# Argument parsing
while [[ $# -gt 0 ]]; do
  case "$1" in
    --since)
      LOOKBACK_MINUTES="$2"
      shift 2
      ;;
    --full)
      USE_TAIL=0
      shift
      ;;
    *)
      echo "Usage: $0 [--since MINUTES] [--full]"
      exit 1
      ;;
  esac
done

echo "Collecting worker celery logs"
if [[ -n "$LOOKBACK_MINUTES" ]]; then
  echo "Mode    : time-filtered"
  echo "Lookback: ${LOOKBACK_MINUTES} minutes"
else
  echo "Mode    : recent activity"
fi
echo "Tail    : $([[ $USE_TAIL -eq 1 ]] && echo enabled || echo disabled)"
echo

ansible workers \
  -i "$INVENTORY" \
  --private-key "$KEY" \
  -m shell \
  -a "$(cat <<EOF
LOG_DIR="/var/log/protien_analysis_pipeline"
HOSTNAME="\$(hostname)"
LOGFILE="\${LOG_DIR}/celery_\${HOSTNAME}.log"

echo "===== \${HOSTNAME} ====="

if [[ ! -f "\$LOGFILE" ]]; then
  echo "No log file found at \${LOGFILE}"
  exit 0
fi

if [[ -n "${LOOKBACK_MINUTES}" ]]; then
  SINCE="\$(date -d '${LOOKBACK_MINUTES} minutes ago' '+%Y-%m-%d %H:%M:%S')"
  awk -v since="\$SINCE" '
    \$0 ~ /^[0-9]{4}-/ && \$0 >= since
  ' "\$LOGFILE" $( [[ $USE_TAIL -eq 1 ]] && echo "| tail -n ${TAIL_LINES}" )
else
  grep -E "task=|Sequence completed|aggregate_results" "\$LOGFILE" | tail -n ${TAIL_LINES}
fi
EOF
)"
