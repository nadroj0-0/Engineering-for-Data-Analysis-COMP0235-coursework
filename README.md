##COMP0235 – Distributed Protein Analysis Pipeline

UCL Computer Science — Distributed Systems Coursework
Last updated: 25 Nov 2025

This project implements a fully automated distributed protein-processing pipeline. Terraform provisions the Harvester VMs, Ansible configures the environment, Redis acts as the message broker, and Celery executes distributed tasks across five worker machines. All code, task files, and datasets are stored on an NFS share so every worker runs in an identical environment.

##Project Structure

ansible/ Ansible configuration (all.yaml, host.yaml, workers.yaml)
build_cluster/ Terraform VM provisioning and dynamic inventory generation
shared/ (NFS) Code, Celery tasks, datasets, experiment IDs
celery/ Local Celery task definitions (synced to shared storage)
pipeline_script.py Distributed pipeline controller
logs/ Worker and pipeline runtime logs

##System Overview

The entire cluster can be built and configured using:

terraform apply
ansible-playbook full.yaml

Workflow:

1. Terraform creates the host and worker virtual machines.

2. generate_inventory.py reads Terraform outputs and generates a dynamic Ansible inventory.

3. Ansible configures all machines, mounts the NFS share, installs required software, deploys Celery, and downloads the dataset.

4. Celery workers start under systemd and automatically load task definitions from the shared NFS directory.

This creates a fully reproducible distributed system.

##Ansible Configuration
#GitLab Integration

The host clones the coursework Git repository using three variables defined in group_vars/all.yaml:

gitrepourl
gituser
gittoken

This enables HTTPS-based cloning without distributing SSH keys and ensures fully reproducible pulls from GitLab.

#Shared NFS Directory

The host exports the directory:

/shared/almalinux

Workers mount this directory so all machines share the same:

scripts/
src/
data/
dataset/

This guarantees that every Celery worker uses the exact same code and dataset.

#Idempotent Dataset Download

The required UniProt dataset (UP000000589_10090.fasta.gz) is downloaded automatically by Ansible, but only if it does not already exist on the NFS share.

The playbook:

-checks whether the dataset exists
-if not, creates a temporary directory
-downloads the file safely
-copies it to the shared dataset directory
-deletes the temporary directory

This ensures the download never repeats unnecessarily and avoids corrupt partial downloads.

#Dynamic Celery Configuration

Celery configuration (celeryconfig.py) is generated from a Jinja2 template.
The Redis host is automatically set based on the machines inside the dynamic inventory:

groups["host"][0]

This means if the cluster is ever destroyed and recreated with different IP addresses, Celery will still correctly connect to Redis without manual editing.

All Celery workers use a systemd service (celery-daemon.service) deployed by Ansible, and are restarted automatically when their configuration changes.

##Current Status (as of 25 Nov 2025)

-Terraform cluster builds successfully using patched files from the lecturer.
-Dynamic inventory works reliably.
-Ansible now pulls the coursework GitLab repository using HTTPS credentials stored as variables.
-NFS host and mounts are fully idempotent and consistent across all workers.
-The UniProt dataset is downloaded automatically and safely, only once.
-Celery workers run under systemd with correct global installation of Celery.
-Celery loads all tasks from the shared directory on every worker.
-Celery configuration is now fully dynamic and follows IP changes after cluster rebuilds.
-Test tasks execute correctly on all workers, returning correct results through Redis as the result backend.

##Summary

The cluster is now fully automated, fully idempotent, and fully reproducible. Terraform provisions the machines, Ansible configures everything including GitLab cloning and dataset management, and Celery workers dynamically discover Redis and run distributed tasks reliably across the entire system.
