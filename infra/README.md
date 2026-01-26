# Ansible Playbooks

This directory contains the Ansible playbooks and roles used to provision all
nodes in the cluster.

---

### 'full.yaml'

Runs the following playbooks in order:

- `all.yaml`
- `storage.yaml`
- `nfs_clients.yaml`
- `logging.yaml`
- `host.yaml`
- `workers.yaml`

This ordering ensures that shared storage, datasets and logging are configured
before application services are started.

---

### `all.yaml`

Applied to all nodes.

Configures:

- Base operating system packages and updates
- Locale and timezone
- Python 3.12
- OpenMPI
- Prometheus Node Exporter

Node Exporter runs as systemd and is configured to expose both system metrics and custom application
metrics via the textfile collector as `~/home/almalinux/custom_metrics`.

---

### `storage.yaml`

Applied to the storage node (Worker 1) only.

Configures:

- NFS server exporting `/shared`
- Installation of shared resources:
  - pdb70 database (for HHsuite)
  - HHsuite
  - s4pred
  - pipeline scripts
  - run output directory
- Storage log directory and log rotation (weekly, rotate 3)

All downloads, builds and dataset extraction steps are guarded by filesystem
flags to prevent redownloading or rebuilding on re-runs.

---

### `nfs_clients.yaml`

Applied to all but storage node.

Configures:

- NFS client mounts for `/shared`
- Persistent mounting across reboots
- Symlink from `/home/almalinux/shared` to `/shared/almalinux`

This ensures identical paths to datasets, tools and pipeline scripts / outputs on all
nodes.

---

### `logging.yaml`

Applied to all nodes.

Configures:

- Creation of `/var/log/protien_analysis_pipeline`
- Convenience symlinks under `/home/almalinux/logs`:
  - `host` / `worker` to `/var/log/protien_analysis_pipeline `
  - `storage` to `/shared/almalinux/storage_logs`
- Log rotation for pipeline logs (weekly, 3 rotate)

---

### `host.yaml`

Applied to the **host node**.

Configures:

- Python dependencies required for pipeline (biopython, celery[redis], minio)
- Host side files (experiment IDS, pipeline_examples, control panel)
- Redis message broker
  - Disable protected mode
  - Bind to all interfaces
  - Enable systemd service
- PostgreSQL database
  - Initialise PostgreSQL
  - Create database pipeline_db
  - Create proteins table
    ```sql
      CREATE TABLE IF NOT EXISTS proteins (
      id TEXT PRIMARY KEY,
      payload TEXT NOT NULL
      );
  - Create restricted host DB user
  - Configure pg_hba.conf
  - Download UniProt FASTA
  - Populate database using Python script
- MinIO object storage
  - Generate TLS certificates
  - Generate and store root credentials in `~/miniopass`
  - Install MinIO server and client
  - Configure systemd service
  - Expose:
      API on :9000
      Console on :9001
  - Store credentials in `~/shared` for workers
- Prometheus server
- Grafana with pre-provisioned datasource and dashboards

Grafana is configured to use the local Prometheus instance and automatically
loads dashboards from disk at startup.

---

### `workers.yaml`

Applied to worker nodes.

Configures:

- Python dependencies required for pipeline execution
- Celery worker service managed via systemd
- Dynamic Celery configuration pointing to the host Redis broker

Celery Details

  - Broker: Redis on host (redis://host:6379/0)
  - Backend: Redis
  - Concurrency: 1 per worker
  - Logging: `/var/log/protien_analysis_pipeline/celery_<hostname>.log`
  - Restart policy: always

Each worker runs a single Celery worker process and writes logs to the shared
pipeline log directory.

---