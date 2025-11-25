---
# COMP0235 Distributed Protein Pipeline

Project setup completed on Sat 15 Nov 02:47:28 GMT 2025

## Project Structure

ansible/          : cluster configuration (all.yaml, host.yaml, workers.yaml)
celery/           : worker task definitions (now copied to shared storage)
pipeline_script.py: core pipeline controller
build_cluster/    : terraform VM setup and inventory generation
logs/             : runtime logs and worker output

## Details

ansible/: holds all Ansible playbooks and roles for configuring the cluster.
`all.yaml` applies common roles to every VM. `host.yaml` configures the host,
including the NFS export. `workers.yaml` applies all worker-only roles,
including NFS mounting, Python installation and Celery setup.
`full.yaml` runs the entire configuration end-to-end.

All pipeline code and Celery task files are located under:
`/shared/almalinux/{scripts,src,data}`. This directory is exported by the host
and mounted on every worker, ensuring a consistent codebase.

build_cluster/: contains all Terraform configuration for creating the Harvester
VMs. The `generate_inventory.py` script reads Terraform outputs and produces a
dynamic inventory for Ansible. This is now the preferred workflow for building
the cluster.

celery/: contains the Celery task definitions and configuration. These files
are copied into the shared NFS directory, allowing all workers to load the same
tasks when their Celery daemon starts.

pipeline_script.py: the main controller script for the distributed protein
analysis pipeline. It coordinates Celery task submission, result handling, and
shared-storage interactions.

logs/: contains runtime logs from Celery workers, the pipeline script and other
components involved in the distributed workflow.
