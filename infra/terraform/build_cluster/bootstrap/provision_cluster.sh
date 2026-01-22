#!/usr/bin/env bash
set -e

REPO_URL="https://gitlab2.ds4eng.condenser.arc.ucl.ac.uk/ucabjsy/coursework-comp0235-2025"
BRANCH="main"

INVENTORY_FILE="$HOME/bootstrap/inventory.ini"

if [ ! -f "$INVENTORY_FILE" ]; then
  echo "ERROR: inventory.ini not found at $INVENTORY_FILE"
  exit 1
fi

echo "Patching inventory for local host execution"
awk '
  /^\[host\]/ { in_host=1; print; next }
  /^\[/ { in_host=0; print; next }
  in_host && NF {
    if ($0 !~ /ansible_connection=local/) {
      print $0 " ansible_connection=local"
    } else {
      print
    }
    next
  }
  { print }
' "$INVENTORY_FILE" > "${INVENTORY_FILE}.tmp"

mv "${INVENTORY_FILE}.tmp" "$INVENTORY_FILE"


echo "Installing dependencies"
sudo dnf -y install python3-pip
sudo python3 -m pip install --upgrade pip
sudo python3 -m pip install ansible
sudo dnf -y install git

TMP_DIR=$(mktemp -d)
echo "Using temporary directory: $TMP_DIR"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

echo "Cloning provisioning repository"
git clone --branch "$BRANCH" "$REPO_URL" "$TMP_DIR/repo"


echo "Running Ansible provisioning"
cd "$TMP_DIR/repo/infra/ansible"
ansible-playbook -i "$INVENTORY_FILE" --private-key "$HOME/.ssh/id_cluster" full.yaml

echo "Provisioning complete"
