# COMP0235 Coursework – Distributed Protein Analysis Pipeline

## Introduction

This project implements a distributed protein analysis pipeline deployed across a multi node cluster. The system is designed to process large protein dataset in parallel, with persistent storage of intermediate and final results, and full observability of pipeline progress.

The pipeline is provisioned on a cluster consisting of one host node and 4 worker nodes. All cluster configuration, deployment, execution, and monitoring are automated using Terraform, Ansible, and host side control scripts.


## 1. SSH Key Generation and Bootstrap

This project uses an automated bootstrap to initialise secure access, generate the cluster inventory, and prepare the system for provisioning from within the host. All SSH key management and inventory configuration are handled automatically.

### 1.1 Prerequisites

* Terraform has already been used to create the cluster virtual machines.
* You have access to the pre installed lecturer/admin SSH key provided for the coursework.
* The repository has been cloned locally.

---

### 1.2 Running the Bootstrap Script

From the repository root, run:

```bash
cd infra/terraform/build_cluster/bootstrap
./bootstrap.sh
```

An optional path to the lecturer public key may be supplied:

```bash
./bootstrap.sh /path/to/lecturer_key.pub
```

If no argument is given, the script will attempt to use the default coursework key location.

---

### 1.3 What the Bootstrap Script Does

The bootstrap process performs the following steps automatically:

* Extracts host and worker IP addresses from Terraform outputs.
* Generates a static `inventory.ini` file for Ansible.
* Creates a user SSH key on the local machine for accessing the host.
* Installs the user SSH public key on the host node.
* Generates a cluster SSH key on the host, used for host -> worker communication.
* Distributes the hosts cluster SSH public key to all worker nodes using a one time Ansible playbook.
* Copies the inventory and provisioning script to the host node.

After this step:

* The lecturer/admin key is no longer required.
* Users access the host using the generated user SSH key.
* The host manages all workers using its own cluster SSH key.

---

### 1.4 Logging Into the Host Node

Once `bootstrap.sh` completes, log into the host node using the generated user key:

```bash
ssh -i ~/.ssh/user_key almalinux@<host_external_ip>
```

On the host, a `~/provision/` directory will be present containing:

* `inventory.ini`
* `provision_cluster.sh`

At this point, the host node is intentionally minimal and unconfigured.

---

## 2. Deployment Instructions (Cluster Provisioning)

### 2.1 Starting the Deployment Process

From within the host node, change into the provision directory:

```bash
cd ~/provision
```

Start the deployment process by executing:

```bash
./provision_cluster.sh
```

This script provisions the entire cluster from the host node and requires no additional arguments.

---

### 2.2 Understanding the `provision_cluster.sh` Script

The `provision_cluster.sh` script performs host side self provisioning and triggers the full Ansible cluster setup.

Specifically, it:

* Verifies the presence of the generated `inventory.ini`.
* Modifies the inventory to mark the host as `ansible_connection=local`.
* Installs required system dependencies on the host:

  * Python and pip
  * Ansible
  * Git
* Clones the coursework repository into a temporary directory.
* Executes the main Ansible playbook:

  ```
  infra/ansible/full.yaml
  ```

  using the hosts cluster SSH key (`~/.ssh/id_cluster`) to access all worker nodes.

---

### 2.3 Ansible Provisioning Details (`full.yaml`)

The entire system is provisioned using a single Ansible playbook (`full.yaml`), which imports a sequence of sub playbooks and roles. Each stage configures a distinct layer of the system.

#### Global Node Setup (All Nodes)

Applied uniformly to host, workers, and storage nodes:

* Base system configuration (localisation, timezone, package updates)
* Installation of development tools, compilers, and utilities
* Python environments (including Python 3.12)
* OpenMPI installation and configuration
* Node Exporter deployment with a systemd-managed service
* Creation of a custom metrics directory for Prometheus textfile collectors

This establishes a consistent execution environment across the cluster before role-specific configuration begins.

---

#### Shared Storage Layer (NFS)

Configured before any pipeline services:

* A dedicated storage node exports `/shared` via NFS
* Host and worker nodes mount the export persistently
* User home directories are symlinked into shared storage
* Shared log directories are created and managed via logrotate

The shared filesystem is used for pipeline scripts, datasets, intermediate `.outs` files, and run artefacts, ensuring persistence across worker failures.

---

#### Host Node Services

The host node provisions all central coordination components:

* **Redis**

  * Installed and configured to accept network connections
  * Used as both the Celery broker and result backend

* **MinIO**

  * TLS certificates generated on first run
  * Secure root credentials generated and persisted
  * Configured as an S3-compatible object store
  * Client configuration deployed
  * Credentials copied to shared storage for worker access

MinIO is used only for final result persistence and is not required for task execution.

---

#### PostgreSQL Sequence Database

On the host node:

* PostgreSQL initialised and enabled
* `pipeline_db` database created
* `proteins` table defined for UniProt sequences
* Controlled database user created with read-only access
* UniProt mouse proteome downloaded and populated via a dedicated script

This allows pipeline tasks to retrieve sequences efficiently without repeated FASTA parsing.

---

#### Bioinformatics Toolchain (Shared Storage)

Installed centrally on the storage node:

* UniProt reference proteome
* PDB70 database for HHsearch
* HHsuite compiled from source
* S4Pred installed with pretrained weights

Installation flags ensure idempotency and prevent redundant recompilation.

---

#### Pipeline Code Deployment

The pipeline repository is cloned once and distributed as follows:

* Host node: coordination logic and control scripts
* Shared storage: execution scripts, datasets, and run directories

Workers execute tasks directly from shared storage.

---

#### Distributed Task Execution (Workers)

On each worker node:

* Python dependencies installed (`celery[redis]`, `biopython`, `numpy`, `scipy`, `torch`, `minio`)
* A dynamic `celeryconfig.py` generated using the current host IP
* A systemd-managed Celery worker service deployed and enabled
* Tasks executed independently with controlled concurrency and structured logging

---

#### Monitoring and Logging

Final provisioning stage:

* Prometheus configured to scrape itself and Node Exporter on all nodes
* Recording rules compute aggregate CPU, memory, and disk metrics
* Grafana installed and provisioned declaratively with:

  * Prometheus datasource
  * Predefined dashboards (including the pipeline dashboard)
* Log directories standardised and rotated across host, workers, and storage

---

Once `full.yaml` completes, all services are active, monitoring is live, and the cluster is fully provisioned and ready to execute pipeline runs.

---

## 3. Pipeline Execution and Results

### 3.1 Running the Pipeline

All pipeline runs are launched from the host node using the control scripts located in `~/control`.

To start a full production pipeline run:

```bash
cd ~/control
./run_pipeline.sh <run_name>
```

Where `<run_name>` is a user defined identifier for the run.

Key behaviour:

* The script launches the full analysis (~5999 sequences).
* A 15 second safety countdown is used to prevent accidental submission.
* Input sequences are read from the predefined experiment ID list:

  ```
  ~/data/experiment_ids.txt
  ```
* Tasks are submitted to the Celery workers as a chord.
* Final aggregation is triggered automatically once all tasks complete.
* Intermediate outputs are written to shared storage.
* Final aggregated results are also persisted to MinIO.

---

### 3.2 Results Collection and Control Scripts

Once a pipeline run has completed, final aggregated results can be retrieved from MinIO to the host node using the provided control script.

To pull results for a completed run:

```bash
cd ~/control
./pull_results.sh <run_name>
```

This script downloads the following files from MinIO:

* `<run_name>_hits_output.csv`
* `<run_name>_profile_output.csv`

Results are stored locally on the host under:

```
~/results/<run_name>/
```

To transfer results to a local machine, use `scp` from your local system, for example:

```bash
scp -i ~/.ssh/user_key -r almalinux@<host_external_ip>:~/results/<run_name> /path/to/local/directory
```

Additional control scripts are available for inspecting logs, sanity checking progress, cleanup, and testing the pipeline. These are documented in:

```
~/control/README.md
```

Refer to that file for detailed usage instructions.

---

## 4. Monitoring and Observability

The pipeline includes built in monitoring using Prometheus, Node Exporter, and Grafana. All monitoring services are automatically configured during provisioning.

* Node Exporter runs on all nodes to collect system metrics.
* Prometheus runs on the host node and scrapes metrics from all nodes.
* Grafana provides a pre provisioned dashboard for cluster and pipeline monitoring.

Access the monitoring tools via your local machines web browser:

* **Prometheus:**
  `http://<host_node_external_ip>:9090`

* **Grafana:**
  `http://<host_node_external_ip>:3000`

The Grafana dashboard displays cluster health, resource utilisation, and pipeline execution progress in real time.

---