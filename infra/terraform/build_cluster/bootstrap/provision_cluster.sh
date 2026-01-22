#!/usr/bin/env bash
set -e

REPO_URL="https://gitlab2.ds4eng.condenser.arc.ucl.ac.uk/ucabjsy/coursework-comp0235-2025"
BRANCH="main"

INVENTORY_FILE="$HOME/bootstrap/inventory.ini"

if [ ! -f "$INVENTORY_FILE" ]; then
  echo "ERROR: inventory.ini not found at $INVENTORY_FILE"
  exit 1
fi

echo "Installing dependencies"
sudo dnf -y install python3-pip
sudo python3 -m pip install --upgrade pip
sudo python3 -m pip install ansible
sudo dnf -y install git

SSH_KEY="$HOME/.ssh/id_cluster"

if [ ! -f "$SSH_KEY" ]; then
  echo "Creating cluster SSH key at $SSH_KEY"
  mkdir -p "$HOME/.ssh"
  chmod 700 "$HOME/.ssh"
  ssh-keygen -t ed25519 -f "$SSH_KEY" -N ""
else
  echo "Cluster SSH key already exists, skipping generation"
fi

TMP_DIR=$(mktemp -d)
echo "Using temporary directory: $TMP_DIR"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

echo "Cloning provisioning repository"
git clone --branch "$BRANCH" "$REPO_URL" "$TMP_DIR/repo"

LECTURER_KEY="$HOME/.ssh/lecturer_key"

if [ -f "$LECTURER_KEY" ]; then
  echo "Lecturer key found – using it for bootstrap SSH"
  BOOTSTRAP_SSH_ARGS="-i $LECTURER_KEY"
else
  echo "Lecturer key not found – using default SSH identities"
  BOOTSTRAP_SSH_ARGS=""
fi


echo "Distributing cluster ssh keys"
cd "$TMP_DIR/repo/infra/ansible"
ANSIBLE_HOST_KEY_CHECKING=False
if [ -n "$BOOTSTRAP_SSH_ARGS" ]; then
  ansible-playbook -i "$INVENTORY_FILE" -e "ansible_ssh_common_args=$BOOTSTRAP_SSH_ARGS" \
  bootstrap_ssh.yaml
else
  ansible-playbook -i "$INVENTORY_FILE" bootstrap_ssh.yaml
fi

echo "Running Ansible provisioning"
cd "$TMP_DIR/repo/infra/ansible"
ansible-playbook -i "$INVENTORY_FILE" --private-key "$HOME/.ssh/id_cluster" full.yaml


echo "Provisioning complete"
