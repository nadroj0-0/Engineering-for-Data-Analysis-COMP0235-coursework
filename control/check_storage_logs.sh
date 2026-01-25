#!/usr/bin/env bash
set -euo pipefail

# Defaults
LOOKBACK_MINUTES=60
USE_TAIL=1
TAIL_LINES=150

LOGFILE="$HOME/logs/storage/storage.log"

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

echo "Collecting storage logs"
echo "Lookback: ${LOOKBACK_MINUTES} minutes"
echo "Tail    : $([[ $USE_TAIL -eq 1 ]] && echo enabled || echo disabled)"
echo

if [[ ! -f "$LOGFILE" ]]; then
  echo "ERROR: storage log not found at:"
  echo "  $LOGFILE"
  exit 1
fi

SINCE="$(date -d "${LOOKBACK_MINUTES} minutes ago" '+%Y-%m-%d %H:%M:%S')"

if [[ $USE_TAIL -eq 1 ]]; then
  awk -v since="$SINCE" '
    $0 ~ /^[0-9]{4}-/ && $0 >= since
  ' "$LOGFILE" | tail -n ${TAIL_LINES}
else
  awk -v since="$SINCE" '
    $0 ~ /^[0-9]{4}-/ && $0 >= since
  ' "$LOGFILE"
fi
