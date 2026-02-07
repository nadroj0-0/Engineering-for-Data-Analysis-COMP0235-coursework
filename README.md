# Engineering for Data Analysis COMP0235 Coursework – Distributed Protein Analysis Pipeline

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

### 2.3 Ansible Provisioning Summary (`full.yaml`)

The entire system is provisioned using a single Ansible playbook (`full.yaml`), which imports and executes a sequence of playbooks and roles. Each playbook configures a specific layer of the system.

* **`all.yaml`**

  * Applies baseline configuration to all nodes
  * Installs common system packages and Python dependencies
  * Deploys Node Exporter on all nodes for system metrics collection

* **`storage.yaml`**

  * Configures the designated storage node
  * Sets up NFS export directories under `/shared`
  * Prepares and populates shared storage with datasets, tools, pipeline scripts, and outputs

* **`nfs_clients.yaml`**

  * Mounts the shared NFS filesystem on the host and worker nodes
  * Ensures consistent paths for code, data, and run artefacts across all machines

* **`logging.yaml`**

  * Creates standardised log directories
  * Configures log rotation and shared logging paths
  * Prepares the system for pipeline and worker level logging

* **`host.yaml`**

  * Installs host specific Python dependencies
  * Configures all host side services:

    * Redis for Celery task coordination
    * MinIO for final result storage
      (Access at : https://ucabjsy-cons.comp0235.condenser.arc.ucl.ac.uk)
    * Prometheus and Grafana for monitoring
    * PostgreSQL for persistent protein sequence storage
  * Deploys host side pipeline scripts and configuration files

* **`workers.yaml`**

  * Installs worker specific Python dependencies
  * Configures Celery workers
  * Deploys and enables systemd managed worker services

Once `full.yaml` completes, shared storage is mounted, core services are running, workers are active, and the cluster is ready to execute pipeline runs.

A detailed breakdown of individual roles, tasks, and configuration settings is provided in:

```
infra/ansible/README.md
```

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

For more indepth implementation details refer to 
```
scripts/celery/README.md
```
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

Refer to that file for detailed usage instructions, including how to test the pipeline using a FASTA file.

---

## 4. Monitoring and Observability

The pipeline includes built in monitoring using Prometheus, Node Exporter, and Grafana. All monitoring services are automatically configured during provisioning.

* Node Exporter runs on all nodes to collect system metrics.
* Prometheus runs on the host node and scrapes metrics from all nodes.
* Grafana provides a pre provisioned dashboard for cluster and pipeline monitoring.

Access the monitoring tools via the web browser:

* **Prometheus:**
  https://prometheus-ucabjsy.comp0235.condenser.arc.ucl.ac.uk

* **Grafana:**
  https://grafana-ucabjsy.comp0235.condenser.arc.ucl.ac.uk

To access the main pipeline dashboard:
- Open the Grafana menu  
- Navigate to **Dashboards -> Pipeline -> Pipeline Monitoring Overview**


The Grafana dashboard displays cluster health, resource utilisation, and pipeline execution progress in real time.

---
