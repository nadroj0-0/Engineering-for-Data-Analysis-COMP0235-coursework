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

Node Exporter is configured to expose both system metrics and custom application
metrics via the textfile collector.

---

### `storage.yaml`

Applied to the **storage node** only.

Configures:

- NFS server exporting `/shared`
- Shared directory structure under `/shared/almalinux`
- Installation of all large, shared resources:
  - UniProt reference proteome
  - pdb70 database (for HHsearch)
  - HHsuite
  - s4pred
- Storage-side log directory and log rotation

All downloads, builds, and dataset extraction steps are guarded by filesystem
flags to prevent re-downloading or rebuilding on re-runs.

---

### `nfs_clients.yaml`

Applied to **host and worker nodes**.

Configures:

- NFS client mounts for `/shared`
- Persistent mounting across reboots
- Symlink from `/home/almalinux/shared` to `/shared/almalinux`

This ensures identical paths to datasets, tools, and pipeline outputs on all
nodes.

---

### `logging.yaml`

Applied to **all nodes**.

Configures:

- Creation of `/var/log/protien_analysis_pipeline`
- Per-node log directories owned by `almalinux`
- Log rotation for pipeline and storage logs
- Convenience symlinks under `/home/almalinux/logs`:
  - `host`
  - `worker`
  - `storage`

This provides a consistent operational view of logs across the cluster.

---

### `host.yaml`

Applied to the **host node**.

Configures:

- Python dependencies required for orchestration and metrics
- Redis message broker
- PostgreSQL database
- MinIO object storage
- Prometheus server
- Grafana with pre-provisioned datasource and dashboards

Grafana is configured to use the local Prometheus instance and automatically
loads dashboards from disk at startup.

---

### `workers.yaml`

Applied to **worker nodes**.

Configures:

- Python dependencies required for pipeline execution
- Celery worker service managed via systemd
- Dynamic Celery configuration pointing to the host Redis broker

Each worker runs a single Celery worker process and writes logs to the shared
pipeline log directory.

---

### PostgreSQL Database

The host provisions a local PostgreSQL database used to store protein sequences.

The following table is created:

```sql
CREATE TABLE IF NOT EXISTS proteins (
    id TEXT PRIMARY KEY,
    payload TEXT NOT NULL
);
