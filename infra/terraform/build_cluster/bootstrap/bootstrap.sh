#!/usr/bin/env bash
set -e

DEFAULT_LECTURER_KEY="../../../../keys/lecturer_key.pub"

if [ $# -eq 1 ]; then
  LECTURER_KEY="$1"
elif [ $# -eq 0 ] && [ -f "$DEFAULT_LECTURER_KEY" ]; then
  echo "No lecturer key argument supplied, using default:"
  echo "  $DEFAULT_LECTURER_KEY"
  LECTURER_KEY="$DEFAULT_LECTURER_KEY"
else
  echo "Usage: $0 /path/to/lecturer_key.pub"
  echo
  echo "Tried default path but did not find lecturer key:"
  echo "  $DEFAULT_LECTURER_KEY"
  exit 1
fi

if [ ! -f "$LECTURER_KEY" ]; then
  echo "ERROR: lecturer key not found at $LECTURER_KEY"
  exit 1
fi


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

USER_KEY="$HOME/.ssh/user_key"

if [ ! -f "$USER_KEY" ]; then
  echo "Creating user ssh key at $USER_KEY"
  mkdir -p "$HOME/.ssh"
  chmod 700 "$HOME/.ssh"
  ssh-keygen -t ed25519 -f "$USER_KEY" -N ""
else
  echo "User ssh key already exists"
fi

SSH_OPTS="-i $LECTURER_KEY -o IdentitiesOnly=no"

echo "Ensuring .ssh directory exists on host"
ssh $SSH_OPTS ${USER}@${HOST_IP} \
  "mkdir -p ~/.ssh && chmod 700 ~/.ssh"

echo "Copying user ssh key to host"
scp $SSH_OPTS ${USER_KEY}.pub ${USER}@${HOST_IP}:~/.ssh/user_key.pub

ssh $SSH_OPTS ${USER}@${HOST_IP} \
  "cat ~/.ssh/user_key.pub >> ~/.ssh/authorized_keys"



USER_SSH="-i $USER_KEY -o IdentitiesOnly=yes"

ssh $USER_SSH ${USER}@${HOST_IP} '
  set -e
  if [ ! -f ~/.ssh/id_cluster ]; then
    echo "Creating cluster SSH key at $SSH_KEY"
    mkdir -p ~/.ssh 
    chmod 700 ~/.ssh
    ssh-keygen -t ed25519 -f ~/.ssh/id_cluster -N ""
  else
    echo "Cluster SSH key already exists, skipping generation"
  fi
'

echo "Distributing cluster ssh keys"
ANSIBLE_HOST_KEY_CHECKING=False \
ANSIBLE_SSH_ARGS="-o IdentitiesOnly=no" \
ansible-playbook -i "$INVENTORY" bootstrap_ssh.yaml



echo "Creating bootstrap directory on host"
ssh $SSH_OPTS ${USER}@${HOST_IP} "mkdir -p ~/bootstrap"

echo "Copying inventory.ini"
scp $SSH_OPTS "$INVENTORY" ${USER}@${HOST_IP}:~/bootstrap/inventory.ini

echo "Copying provision_cluster.sh"
scp $SSH_OPTS "$PROVISION" ${USER}@${HOST_IP}:~/bootstrap/provision_cluster.sh
ssh $SSH_OPTS ${USER}@${HOST_IP} "chmod +x ~/bootstrap/provision_cluster.sh"

echo "Bootstrap complete"
echo "Log into the host VM with:"
echo "ssh -i ~/.ssh/user_key ${USER}@${HOST_IP} and follow: ~/bootstrap/README.md"
