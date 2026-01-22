#!/usr/bin/env bash
set -e

USER="almalinux"
INVENTORY="inventory.ini"
PROVISION="provision_cluster.sh"
GEN_SCRIPT="../generate_inventory.py"

if [ ! -f "$GEN_SCRIPT" ]; then
  echo "ERROR: generate_inventory.py not found at $GEN_SCRIPT"
  exit 1
fi

echo "Generating inventory.ini from Terraform outputs"
python3 "$GEN_SCRIPT" --write-ini "$INVENTORY"

if [ ! -f "$INVENTORY" ]; then
  echo "ERROR: inventory.ini was not generated"
  exit 1
fi

HOST_IP=$(awk '
  /^\[host\]/ {found=1; next}
  /^\[/ {found=0}
  found && NF {print; exit}
' "$INVENTORY")

if [ -z "$HOST_IP" ]; then
  echo "ERROR: could not determine host IP from inventory.ini"
  exit 1
fi

echo "Host IP: $HOST_IP"

echo "Creating bootstrap directory on host"
ssh ${USER}@${HOST_IP} "mkdir -p ~/bootstrap"

echo "Copying inventory.ini"
scp "$INVENTORY" ${USER}@${HOST_IP}:~/bootstrap/inventory.ini

echo "Copying provision_cluster.sh"
scp "$PROVISION" ${USER}@${HOST_IP}:~/bootstrap/provision_cluster.sh
ssh ${USER}@${HOST_IP} "chmod +x ~/bootstrap/provision_cluster.sh"

echo "Bootstrap complete"
echo "Log into the host VM and follow: ~/bootstrap/README.md"
