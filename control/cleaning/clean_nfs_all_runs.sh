#!/usr/bin/env bash
set -euo pipefail

echo "DANGER: This will delete ALL pipeline runs."
echo "/shared/almalinux/runs/*"
echo
read -rp "Type 'DELETE ALL RUNS' to continue: " CONFIRM

if [[ "$CONFIRM" != "DELETE ALL RUNS" ]]; then
  echo "Aborted."
  exit 1
fi

rm -rf /shared/almalinux/runs/*
echo "All runs deleted."
