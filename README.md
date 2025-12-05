COMP0235 – Distributed Protein Analysis Pipeline

UCL Computer Science — Distributed Systems Coursework
Last updated: 05 Dec 2025

This project implements a fully automated distributed protein-processing pipeline. Terraform provisions the Harvester VMs, Ansible configures the environment, Redis acts as the message broker, and Celery executes distributed tasks across five worker machines. All code, task files, helper scripts, and datasets are stored in a shared NFS directory so every worker runs in an identical environment.

Project Structure
ansible/           – Full configuration of host + workers (roles, playbooks)
build_cluster/     – Terraform VM provisioning + dynamic inventory generation
shared/
   └── almalinux/
        scripts/
            celery/        – Celery tasks + run_pipeline_host.py (pipeline entrypoint)
            helperScripts/ – results_parser.py, select_ids.py
        src/               – Reference pipeline_example/ and original scripts
        dataset/           – pdb70 database, UniProt subsets
        tools/             – HHsuite, s4pred
        runs/              – Auto-generated pipeline output directories
logs/              – Worker and pipeline runtime logs

System Overview
Cluster Build Process

The entire distributed environment is built using:

terraform apply
ansible-playbook full.yaml


Terraform provisions the host VM and five worker VMs.

generate_inventory.py collects outputs and builds the dynamic Ansible inventory.

Ansible:

configures all nodes

installs Python, Redis bindings, BioPython

configures NFS (worker-1 as server, host + workers 2–5 as clients)

installs HHsuite and s4pred

deploys Celery

populates the shared directory

Celery workers start via systemd and load their task definitions directly from the shared /shared/almalinux/scripts/celery directory.

The result is a reproducible, uniform distributed compute environment.

Updated NFS Architecture (Dec 2025)

Originally, the host exported /shared, but its 10 GB disk was too small for toolchains and datasets.
The NFS server is now worker-1, which has a 150 GB disk.

Final layout

NFS server → worker-1 exports /shared/almalinux

NFS clients → host + workers 2–5 mount /shared

Celery workers → all five workers (including worker-1)

This guarantees:

all machines share the same tools, databases, scripts

sufficient disk space for pdb70, HHsuite builds, UniProt datasets

consistent execution across the cluster

Pipeline Architecture (Dec 2025)
Celery Task Pipeline

The original monolithic script was rewritten into isolated Celery tasks stored in:

/shared/almalinux/scripts/celery/tasks.py


Each sequence is processed via a chain of tasks:

make_seq_dir_task
→ write_fasta_task
→ run_s4pred_task
→ read_horiz_task
→ run_hhsearch_task
→ run_parser_task

Path Dictionary (seq_paths)

All tasks pass around a single dictionary containing:

seq_id
seq_dir
tmp.fas
tmp.horiz
tmp.a3m
tmp.hhr
parsed_results


This mirrors the behaviour of the professor’s original script while enabling safe distributed execution.

Filesystem Layout Per Sequence

For each input sequence, Celery creates:

runs/<run_name>/<sequence_id>/
    tmp.fas
    tmp.horiz
    tmp.a3m
    tmp.hhr
    <sequence_id>_parsed.out


This separates outputs cleanly and avoids filename conflicts when thousands of sequences run in parallel.

Host-Side Orchestration (run_pipeline_host.py)

The pipeline is now invoked via:

python3 run_pipeline_host.py <fasta_input> [optional_run_name]


run_pipeline_host.py:

resides in /shared/almalinux/scripts/celery/

reads the FASTA input

generates a run directory (auto-timestamped if no name is supplied)

dispatches one Celery chain per sequence

Example:

python3 /shared/almalinux/scripts/celery/run_pipeline_host.py \
    /shared/almalinux/src/pipeline_example/test.fa


If a run name is not supplied, a timestamped name is generated automatically:

run_2025-12-05_04-21-08/

Role Reorganisation

The following roles manage NFS and dataset/tool deployment:

storage_configure_nfs — sets up NFS server on worker-1

storage_nfs_populator — installs HHsuite and s4pred, clones GitLab repo, populates datasets

client_configure_nfs — mounts /shared on host and workers 2–5

Celery’s systemd unit includes:

After=network-online.target remote-fs.target redis.service


ensuring Celery starts only after NFS and Redis are available.

Dataset Layout
dataset/
    uniprot/uniprot_dataset.fasta.gz
    pdb70/  (full database)


Datasets are downloaded, extracted, and validated idempotently.

Current Status (as of 05 Dec 2025)

Terraform builds a consistent 6-node cluster.

Worker-1 exports /shared via NFS with sufficient storage.

Host + workers 2–5 mount the shared directory correctly.

All Celery workers run under systemd and correctly load tasks.

HHsuite and s4pred installed and verified.

End-to-end pipeline runs successfully on the provided test sequence.

Automatic run directory generation fully operational.

Task parallelisation validated: multiple runs executed simultaneously across workers.

The distributed pipeline is now functional, modular, and ready for multi-sequence and large-scale runs.
