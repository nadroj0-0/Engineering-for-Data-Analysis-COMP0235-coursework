##COMP0235 – Distributed Protein Analysis Pipeline

UCL Computer Science — Distributed Systems Coursework
Last updated: 01 Dec 2025

This project implements a fully automated distributed protein-processing pipeline. Terraform provisions the Harvester VMs, Ansible configures the environment, Redis acts as the message broker, and Celery executes distributed tasks across five worker machines. All code, task files, and datasets are stored on an NFS share so every worker runs in an identical environment.

##Project Structure

ansible/ Ansible configuration (all.yaml, host.yaml, workers.yaml)
build_cluster/ Terraform VM provisioning and dynamic inventory generation
shared/ (NFS) Code, Celery tasks, helper scripts, datasets, experiment IDs
scripts/ Celery tasks + helperScripts containing non-Celery utilities
pipeline/ Distributed pipeline controller (now integrated into tasks.py)
logs/ Worker and pipeline runtime logs

##System Overview

The entire cluster can be built and configured using:

terraform apply
ansible-playbook full.yaml

Workflow:

Terraform creates the host and worker virtual machines.

generate_inventory.py reads Terraform outputs and generates a dynamic Ansible inventory.

Ansible configures all machines, mounts the NFS share, installs required software, deploys Celery, and downloads the dataset.

Celery workers start under systemd and automatically load task definitions from the shared NFS directory.

This creates a fully reproducible distributed system.

##Ansible Configuration

###GitLab Integration

The host clones the coursework Git repository using three variables defined in group_vars/all.yaml:

gitrepourl
gituser
gittoken

This enables HTTPS-based cloning without distributing SSH keys, and ensures fully reproducible pulls from GitLab.

###Shared NFS Directory

The host exports the directory:

/shared/almalinux

Workers mount this directory so all machines share the same:

scripts/
celery/ (all Celery tasks)
helperScripts/ (non-Celery utilities: results_parser.py, select_ids.py)
src/
data/
dataset/

This guarantees that every Celery worker uses the exact same code and dataset.

###Code Synchronisation

To ensure the shared NFS directory always matches the GitLab repository, the Ansible host role now removes the old src/, scripts/, and data/ directories before copying new versions from the temporary Git clone. This prevents stale files from persisting after refactors.

A future improvement will replace this with ansible.posix.synchronize(delete=yes) to mirror the directories more efficiently and maintain idempotence.

###Idempotent Dataset Download

The required UniProt dataset (UP000000589_10090.fasta.gz) is downloaded automatically by Ansible, but only if it does not already exist on the NFS share.

The playbook:

-checks whether the dataset exists
-if not, creates a temporary directory
-downloads the file safely
-copies it to the shared dataset directory
-deletes the temporary directory

This ensures that downloads never repeat unnecessarily and avoids partial or corrupt files.

###Dynamic Celery Configuration

Celery configuration (celeryconfig.py) is generated from a Jinja2 template.
The Redis host is automatically set based on the dynamic inventory:

groups["host"][0]

This means if the cluster is ever destroyed and recreated with different IP addresses, Celery will still correctly connect to Redis without manual editing.

All Celery workers use a systemd service (celery-daemon.service) deployed via Ansible, and are restarted automatically when their configuration changes.

##Current Status (as of 01 Dec 2025)

-Terraform cluster builds successfully using patched files from the lecturer.
-Dynamic inventory works reliably.
-Ansible now pulls the coursework GitLab repository using HTTPS credentials stored as variables.
-NFS host and mounts are fully idempotent and consistent across all workers.
-The UniProt dataset is downloaded automatically and safely, only once.
-Celery workers run under systemd with correct global installation of Celery.
-All pipeline stages from pipeline_script.py have now been rewritten as Celery tasks inside tasks.py.
-Non-Celery utilities (results_parser.py, select_ids.py) are stored cleanly under helperScripts/.
-The shared NFS code layout now updates correctly on every Ansible run and removes outdated files.
-Clustering tests confirm every worker loads an identical task list from the shared directory.
-Test tasks and pipeline tasks load correctly on all workers, confirmed through distributed checks.

##Summary

The cluster is now fully automated, fully reproducible, and very close to end-to-end pipeline execution. Terraform provisions the machines, Ansible configures everything including GitLab cloning and dataset management, and Celery dynamically discovers Redis and executes distributed tasks reliably across all workers.
