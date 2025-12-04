COMP0235 – Distributed Protein Analysis Pipeline

UCL Computer Science — Distributed Systems Coursework
Last updated: 04 Dec 2025

This project implements a fully automated distributed protein-processing pipeline. Terraform provisions the Harvester VMs, Ansible configures the environment, Redis acts as the message broker, and Celery executes distributed tasks across five worker machines. All code, task files, helper scripts, and datasets are stored on a shared NFS directory so every worker runs in an identical environment.

Project Structure

ansible/ — Ansible configuration (full.yaml, storage.yaml, nfs_clients.yaml, host.yaml, workers.yaml, roles/)
build_cluster/ — Terraform VM provisioning and dynamic inventory generation
shared/ (NFS) — Code, Celery tasks, helper scripts, datasets, experiment IDs
scripts/ — Celery task package plus helperScripts/
pipeline/ — Distributed pipeline controller (now integrated into tasks.py)
logs/ — Worker and pipeline runtime logs

System Overview

The entire cluster can be built and configured using:

terraform apply
ansible-playbook full.yaml


Workflow:

Terraform creates the host and five worker VMs.

generate_inventory.py reads Terraform outputs and builds the dynamic Ansible inventory.

Ansible configures all machines, sets up NFS, installs system dependencies, deploys Celery, and populates the shared directory.

Celery workers start under systemd and automatically load task definitions from the shared NFS directory.

The result is a fully reproducible, uniform distributed processing environment.

Updated NFS Architecture (Dec 2025)

The original design exported /shared from the host VM.
This was changed because the host VM has only a 10 GB disk, which is too small for:

HHsuite build artifacts

s4pred weights

pdb70 database

UniProt proteome

GitLab code clone

The NFS server is now worker-1, which has a 150 GB disk and also functions as a normal Celery worker.

New layout:

storage node → worker-1 (exports /shared)

nfs clients → host + workers 2–5 (mount /shared)

workers → all 5 workers (including the storage node)

This ensures all machines access the same code and datasets, while giving the NFS server enough space for the full pipeline.

Shared NFS Directory

worker-1 exports:

/shared/almalinux


All other machines mount this via:

<worker-1-ip>:/shared


The shared directory contains:

scripts/
 celery/ (Celery tasks)
 helperScripts/ (results_parser.py, select_ids.py)
src/
data/
dataset/uniprot/
dataset/pdb70/
tools/ (HHsuite, s4pred)

Every worker runs the pipeline using these shared files, guaranteeing consistency.

Role Reorganisation (Dec 2025)

NFS roles were updated for the new layout:

storage_configure_nfs – configures NFS server on worker-1

storage_nfs_populator – clones GitLab repo, installs tools, populates datasets

client_configure_nfs – mounts /shared on host + workers 2–5

Celery and Python roles remain unchanged, but Celery's systemd unit now includes:

After=network-online.target remote-fs.target redis.service


so Celery only starts after NFS is mounted and Redis is reachable.

Dataset Layout

Datasets are placed into named subdirectories:

dataset/uniprot/uniprot_dataset.fasta.gz
dataset/pdb70/  (full extracted database)


Playbook behaviour:

checks for existing files

downloads only if missing

uses temporary directories

extracts automatically

cleans up temporary files

idempotent across re-runs

Dynamic Celery Configuration

Celery config uses a Jinja2 template that injects the current Redis IP:

redis://{{ groups["host"][0] }}:6379/0


This ensures the workers always point at the correct broker even after Terraform rebuilds.

Systemd runs Celery directly from /shared/almalinux/scripts/celery.

Current Status (as of 04 Dec 2025)

Terraform cluster builds cleanly with consistent VM provisioning.

Worker-1 successfully exports /shared over NFS.

Host and workers 2–5 mount the share correctly.

All Celery workers start under systemd across five nodes.

All machines load the exact same task list from the shared folder.

s4pred and HHsuite fully installed on the storage node.

GitLab cloning and file population fully automated.

UniProt and pdb70 datasets integrated into the shared layout.

Cluster-wide inspection confirms identical environment across all workers.
