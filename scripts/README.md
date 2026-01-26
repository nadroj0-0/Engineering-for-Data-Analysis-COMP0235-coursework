## Pipeline Architecture

This document describes the execution flow, task ordering, and filesystem
layout of the distributed protein-analysis pipeline.

---

## Celery Task Pipeline

Pipeline execution logic is implemented in:

```

/shared/almalinux/scripts/celery/tasks.py

```

Each protein sequence is processed independently using the following
fixed execution order:

```

make_seq_dir
→ write_fasta
→ run_s4pred
→ read_horiz
→ run_hhsearch
→ run_parser
→ upload_parsed_output

```

Each step performs exactly one operation and passes a sequence-specific
path dictionary to the next step.

---

## Sequence Path Dictionary (`seq_paths`)

All pipeline steps share a single dictionary containing per-sequence paths:

```

run_id
seq_id
seq_dir
tmp_fas
tmp_horiz
tmp_a3m
tmp_hhr
parsed_results

```

This mirrors the reference pipeline while allowing safe parallel execution
without filename collisions.

---

## Filesystem Layout

### Per-Run

```

/shared/almalinux/runs/<run_id>/

```

### Per-Sequence

```

runs/<run_id>/<sequence_id>/
├── tmp.fas
├── tmp.horiz
├── tmp.a3m
├── tmp.hhr
└── <sequence_id>_parsed.out

```

Each sequence is fully isolated and may run concurrently on different workers.

### Aggregated Outputs

```

runs/<run_id>/output/
├── <run_id>_hits_output.csv
└── <run_id>_profile_output.csv

```

Aggregated outputs are also uploaded to MinIO.

---

## Host-Side Orchestration

Pipeline runs are launched from the host using:

```

python3 run_pipeline_host.py <experiment_ids_file> [run_name]

```

If no run name is provided, one is generated automatically:

```

run_YYYY-MM-DD_HH-MM-SS

````

### Database-Driven Execution

- Experiment IDs are read from file
- Sequences are fetched from PostgreSQL
- One Celery task is submitted per sequence
- A Celery **chord** triggers aggregation after all tasks complete

No large FASTA files are staged on the host.

---

## UniProt Database

Protein sequences are stored persistently in PostgreSQL:

```sql
CREATE TABLE proteins (
    id TEXT PRIMARY KEY,
    payload TEXT NOT NULL
);
````

* `id` is the UniProt identifier
* `payload` stores the full FASTA entry verbatim

The database is populated automatically via Ansible and is idempotent.

---

## Testing and Experiment Selection

Random experiment IDs can be generated using:

```
python3 select_ids.py <input.fasta> <num_ids>
```

A wrapper script combines selection and execution:

```
python3 test_run_pipeline.py <num_ids> [run_name]
```

This enables small, repeatable smoke tests.

---

## Monitoring and Logging

### Metrics

Node Exporter runs on all nodes and exposes system and application metrics
via the textfile collector:

```
/home/almalinux/custom_metrics
```

Pipeline metrics include task counts, failures, pipeline state, and timestamps.
Metrics are emitted by Celery tasks and host orchestration scripts and scraped
by Prometheus.

### Logs

Celery workers run under systemd and write per-worker logs to:

```
/var/log/protien_analysis_pipeline/
└── pipeline_<hostname>.log
```

Logs include task start, completion, failure, and retry events.

An Ansible helper script allows recent logs to be retrieved from all workers.

```

---

This is now **exactly** what you were aiming for:  
high-density, diagram-heavy, prose-light, and completely viva-safe.  
You can paste this in and move on — this part is done.
```
