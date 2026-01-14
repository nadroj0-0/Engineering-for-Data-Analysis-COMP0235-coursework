COMP0235 – Distributed Protein Analysis Pipeline

UCL Computer Science — Distributed Systems Coursework
Last updated: 27 Dec 2025

This project implements a fully automated, distributed protein-analysis pipeline.
Terraform provisions a multi-node cluster on Harvester, Ansible configures the
environment, PostgreSQL provides persistent biological data storage, Redis acts
as the message broker, and Celery executes a task-based pipeline across five
worker machines.

The system is designed for parallel execution, reproducibility, and operational
clarity. All workers execute identical code against a shared execution
environment, while orchestration and data selection are handled centrally on the
host.

-------------------------------------------------------------------------------

Project Structure

ansible/                  – Full configuration of host + workers (roles, playbooks)
terraform/build_cluster/  – Terraform VM provisioning + dynamic inventory

shared/
└── almalinux/
    ├── scripts/
    │   └── celery/        – Celery tasks, host launcher, DB logic, metrics, parsers
    ├── src/               – Reference pipeline_example/ and original scripts
    ├── dataset/           – Symlinked access to UniProt + pdb70 datasets
    ├── tools/             – HHsuite, s4pred
    └── runs/              – Auto-generated pipeline output directories

/var/log/protien_analysis_pipeline/
                          – Per-worker application logs (systemd-managed)

All pipeline logic, metrics, and parsing utilities are colocated in the
`celery/` directory to guarantee identical execution environments across workers.

-------------------------------------------------------------------------------

System Overview

Cluster Build Process

The entire environment is built using:

    terraform apply
    ansible-playbook full.yaml

Terraform
- Provisions 1 host VM and 5 worker VMs
- Generates outputs used to create a dynamic Ansible inventory

Ansible
- Configures all machines with base dependencies
- Sets up NFS (worker-1 as server, others as clients)
- Installs Redis, PostgreSQL, Python dependencies, HHsuite, and s4pred
- Deploys Celery workers via systemd
- Downloads and validates large biological datasets
- Installs monitoring components (Node Exporter, Prometheus)

-------------------------------------------------------------------------------

Updated NFS Architecture (Dec 2025)

The host VM has a limited disk (10 GB), which is insufficient for large datasets.
The NFS server was therefore migrated to worker-1, which has a 150 GB disk.

Final layout:
- NFS server: worker-1 exports /shared/almalinux
- NFS clients: host + workers 2–5
- Celery workers: all five workers (including worker-1)

This provides:
- Sufficient storage for pdb70, UniProt, HHsuite, and s4pred
- A single shared execution environment
- Identical paths and behaviour across all workers

-------------------------------------------------------------------------------

Pipeline Architecture

Celery Task Pipeline

The original monolithic script was refactored into isolated Celery tasks located
in:

    /shared/almalinux/scripts/celery/tasks.py

Each protein sequence is processed via a Celery chain:

    make_seq_dir_task
      → write_fasta_task
      → run_s4pred_task
      → read_horiz_task
      → run_hhsearch_task
      → run_parser_task

Each task performs exactly one step and passes a sequence-specific path
dictionary forward.

Path Dictionary (seq_paths)

All tasks pass a single dictionary containing sequence-specific paths, including:

- seq_id
- seq_dir
- tmp.fas
- tmp.horiz
- tmp.a3m
- tmp.hhr
- parsed_results

This mirrors the original reference pipeline while allowing safe parallel
execution without filename collisions.

Filesystem Layout Per Sequence

For each input sequence, the pipeline creates:

    runs/<run_name>/<sequence_id>/
    ├── tmp.fas
    ├── tmp.horiz
    ├── tmp.a3m
    ├── tmp.hhr
    └── <sequence_id>_parsed.out

Each sequence is fully isolated, enabling many sequences to run concurrently.

-------------------------------------------------------------------------------

Host-Side Orchestration

The pipeline is launched from the host using:

    python3 run_pipeline_host.py <experiment_id_file> [optional_run_name]

Key design change (Dec 2025):

The pipeline is now database-driven. The host no longer stages large FASTA files.
Instead:

1. A list of experiment IDs is read.
2. Protein sequences are fetched from PostgreSQL.
3. One Celery chain is submitted per sequence.

This removes repeated FASTA parsing and cleanly separates storage, orchestration,
and computation.

If no run name is provided, one is generated automatically:

    run_2025-12-26_01-14-37/

-------------------------------------------------------------------------------

UniProt Database Integration

A persistent PostgreSQL database stores the full UniProt mouse reference
proteome.

Canonical data location:
    /srv/uniprot/uniprot_dataset.fasta
Owned by: postgres

A compatibility symlink is provided:
    /home/almalinux/dataset/uniprot → /srv/uniprot

Database schema:

    CREATE TABLE proteins (
        id TEXT PRIMARY KEY,
        payload TEXT NOT NULL
    );

- `id` is the UniProt identifier
- `payload` stores the complete FASTA entry verbatim
- Data is lossless and byte-correct relative to the original dataset

The database is populated automatically via Ansible using a custom ingestion
script. Population is idempotent and skips duplicates.

-------------------------------------------------------------------------------

Testing & Experiment Selection

A helper script (`select_ids.py`) is provided to randomly sample protein IDs from
the full UniProt FASTA. This is intended for testing and demonstration.

A wrapper script (`test_run_pipeline.py`) combines selection and execution:

- Randomly selects N protein IDs
- Writes them to a temporary experiment file
- Launches the pipeline using database-backed execution

Example:

    python3 test_run_pipeline.py 40 test_smoke_run

This enables repeatable smoke tests and parallel demonstrations without
modifying core pipeline logic.

-------------------------------------------------------------------------------

Monitoring & Observability

Metrics (System State)

Node Exporter (All Machines)
- Installed on host and all workers
- Exposes CPU, memory, disk, and application metrics
- Uses the textfile collector at:
      /home/almalinux/custom_metrics

Application Metrics (metrics.py)
- Task execution counters
- Task failure counters
- Tasks in progress
- Pipeline running state
- Timestamps for pipeline start and completion

Metrics are emitted live by:
- Celery tasks
- run_pipeline_host.py

Prometheus (Host)
- Scrapes Node Exporter on all machines
- Includes basic recording rules
- Ready for dashboard visualisation

-------------------------------------------------------------------------------

Logging (Operational Trace)

Application-Level Logging

All Celery tasks emit structured log messages recording:
- Task start
- Task completion
- Task failure
- Retry events (logged at WARNING level)

Each log entry includes timestamps, task name, sequence ID, and worker hostname.

Celery Worker Logs

Celery workers run under systemd and write per-worker logs to:

    /var/log/protien_analysis_pipeline/
    └── pipeline_<hostname>.log

This provides clean, collision-free execution traces.

Operational Access

Each worker exposes an ops directory for inspection:

    /home/almalinux/ops/
    └── logs → /var/log/protien_analysis_pipeline

An Ansible helper script allows recent logs to be retrieved from all workers
simultaneously for rapid debugging and viva demonstrations.

-------------------------------------------------------------------------------

Fault Tolerance & Retry Semantics (Dec 2025)

Selected failure-prone tasks use Celery’s built-in retry mechanism to handle
transient errors.

Key properties:

- Retries are task-local and explicitly bounded
- Failed tasks are returned to the queue and may execute on any worker
- Downstream tasks in a chain remain pending until the retried task completes
- Retry delays provide backoff for transient issues (e.g. NFS latency or tool
  startup timing)

Retries are applied only where semantically safe (e.g. external tool execution
and parsing). Deterministic setup tasks are not retried.

Retry attempts are logged as WARNING events. Tasks that exceed retry limits are
logged as ERRORs, ensuring visibility without masking genuine failures.

-------------------------------------------------------------------------------

Current Status (Dec 2025)

- Terraform builds a consistent 6-node cluster
- Worker-1 exports /shared with sufficient storage
- All nodes mount NFS correctly
- Celery workers run persistently under systemd
- HHsuite and s4pred installed and verified
- UniProt database populated and validated
- Database-driven orchestration implemented
- Parallel execution validated with up to 40 sequences
- Bounded task retries implemented for transient failures
- Structured logging and failure visibility in place
- Metrics emitted for system and pipeline state
- System behaviour validated under normal and stress workloads

-------------------------------------------------------------------------------

Next Steps

- Finalise Grafana dashboards
- Add log rotation
- Add minimal host and storage-node logging
- Create a small host-side control panel (helper scripts)
- Clean and polish repository
- Write deployment and viva walkthrough documentation
- Optional: add one well-scoped extension feature
