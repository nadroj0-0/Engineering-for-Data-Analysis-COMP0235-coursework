COMP0235 – Distributed Protein Analysis Pipeline

UCL Computer Science — Distributed Systems Coursework
Last updated: 19 Dec 2025

This project implements a fully automated, distributed protein-analysis pipeline. Terraform provisions a multi-node cluster on Harvester, Ansible configures the environment, Redis acts as the message broker, and Celery executes a task-based pipeline across five worker machines.

All pipeline code, helper scripts, tools, and datasets are stored on a shared NFS filesystem so every worker executes in an identical environment. The system supports parallel execution, fault isolation, and end-to-end reproducibility.

Project Structure
ansible/                  – Full configuration of host + workers (roles, playbooks)
terraform/build_cluster/  – Terraform VM provisioning + dynamic inventory
shared/
└── almalinux/
    ├── scripts/
    │   ├── celery/        – Celery tasks + run_pipeline_host.py
    │   └── helperScripts/ – results_parser.py, metrics.py, utilities
    ├── src/               – Reference pipeline_example/ and original scripts
    ├── dataset/           – pdb70 database, UniProt subsets
    ├── tools/             – HHsuite, s4pred
    └── runs/              – Auto-generated pipeline output directories
logs/                     – Runtime logs (where applicable)

System Overview
Cluster Build Process

The entire environment is built using:

terraform apply
ansible-playbook full.yaml

Terraform

Provisions 1 host VM and 5 worker VMs

Generates outputs used to create a dynamic Ansible inventory

Ansible

Configures all machines with base dependencies

Sets up NFS (worker-1 as server, others as clients)

Installs Redis, Python dependencies, HHsuite, and s4pred

Deploys Celery workers via systemd

Installs monitoring components (Node Exporter, Prometheus)

Celery workers load their task definitions directly from the shared directory:

/shared/almalinux/scripts/celery


This guarantees identical code and tools on every worker.

Updated NFS Architecture (Dec 2025)

The host VM has a 10 GB disk, which is insufficient for large datasets and toolchains.
The NFS server was therefore migrated to worker-1, which has a 150 GB disk.

Final layout

NFS server: worker-1 exports /shared/almalinux

NFS clients: host + workers 2–5

Celery workers: all five workers (including worker-1)

This provides:

Sufficient storage for pdb70, UniProt, HHsuite, and s4pred

A single shared execution environment

Consistent results across all workers

Pipeline Architecture
Celery Task Pipeline

The original monolithic script was rewritten as isolated Celery tasks located in:

/shared/almalinux/scripts/celery/tasks.py


Each protein sequence is processed via a Celery chain:

make_seq_dir_task
→ write_fasta_task
→ run_s4pred_task
→ read_horiz_task
→ run_hhsearch_task
→ run_parser_task


Each task performs one clearly defined step and passes its output forward.

Path Dictionary (seq_paths)

All tasks pass around a single dictionary containing sequence-specific paths:

seq_id

seq_dir

tmp.fas

tmp.horiz

tmp.a3m

tmp.hhr

parsed_results

This mirrors the behaviour of the original reference pipeline while allowing safe parallel execution without filename collisions.

Filesystem Layout Per Sequence

For each input sequence, the pipeline creates:

runs/<run_name>/<sequence_id>/
├── tmp.fas
├── tmp.horiz
├── tmp.a3m
├── tmp.hhr
└── <sequence_id>_parsed.out


Each sequence is fully isolated, enabling thousands of sequences to run concurrently.

Host-Side Orchestration

The pipeline is launched from the host using:

python3 run_pipeline_host.py <fasta_input> [optional_run_name]


run_pipeline_host.py:

Resides in /shared/almalinux/scripts/celery/

Reads a FASTA input file

Generates a run directory (timestamped if not supplied)

Submits one asynchronous Celery chain per sequence

Example
python3 /shared/almalinux/scripts/celery/run_pipeline_host.py \
    /shared/almalinux/src/pipeline_example/test.fa


If no run name is provided, one is generated automatically:

run_2025-12-05_04-21-08/

Monitoring & Observability (Dec 2025)

Basic observability has been added to track system and pipeline behaviour.

Node Exporter (All Machines)

Installed on host and all workers

Exposes CPU, memory, disk, and custom application metrics

Uses the textfile collector at:

/home/almalinux/custom_metrics

Application Metrics (metrics.py)

A lightweight helper module (metrics.py) exposes pipeline-level metrics:

Task execution counters

Task failure counters

Tasks currently in progress

Pipeline running state

Timestamps for last task and pipeline completion

Metrics are written safely to .prom files and labelled automatically using the machine hostname.
Metrics are actively emitted by all Celery pipeline tasks at runtime and reflect live system state rather than historical logs.

These metrics are called from:

tasks.py

run_pipeline_host.py

Prometheus (Host)

Installed and configured on the host

Scrapes:

Prometheus itself

Node Exporter on all machines

Includes recording rules for:

CPU utilisation

Memory utilisation

Disk growth rates

Ingress labels are configured via Terraform to expose Prometheus and Grafana UIs using unique hostnames.

Role Reorganisation

Key Ansible roles:

storage_configure_nfs — NFS server setup (worker-1)

storage_nfs_populator — installs tools, datasets, and code

client_configure_nfs — mounts /shared on clients

worker_configure_celery — Celery worker configuration

all_node_exporter — Node Exporter on all machines

host_logging — Prometheus (and Grafana readiness)

Celery’s systemd unit explicitly waits for:

network-online.target

remote-fs.target

redis.service

ensuring correct startup ordering.

Dataset Layout
dataset/
├── uniprot/
│   └── uniprot_dataset.fasta.gz
└── pdb70/
    └── (full HHsuite database)


All datasets are downloaded, extracted, and validated idempotently via Ansible.

Current Status (Dec 2025)

Terraform builds a consistent 6-node cluster

Worker-1 exports /shared with sufficient storage

All clients mount /shared correctly

Celery workers run under systemd and load tasks correctly

HHsuite and s4pred installed and verified

End-to-end pipeline validated against reference output

Parallel execution tested across multiple workers

Application-level metrics fully implemented and emitting

Monitoring infrastructure in place and ready for dashboards

Next Steps

Validate Prometheus scraping once Rancher is stable

Build Grafana dashboards:

Per-worker

Storage node

Pipeline-level overview

Add structured, rotated .log file logging (worker, storage, host)

Integrate a PostgreSQL results database for experiment tracking
