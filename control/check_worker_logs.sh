#!/usr/bin/env bash
set -euo pipefail

CONTROL_DIR="$(cd "$(dirname "$0")" && pwd)"
INVENTORY="${CONTROL_DIR}/inventory.ini"
REMOTE_SCRIPT="/home/almalinux/control/check_local_logs.sh"

echo "Collecting worker logs (last 60 minutes)"
echo

ansible workers \
  -i "$INVENTORY" \
  -m shell \
  -a "$REMOTE_SCRIPT"
