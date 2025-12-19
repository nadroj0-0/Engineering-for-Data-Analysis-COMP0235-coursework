##Prometheus (self-monitoring)

Prometheus process up/down

Prometheus scrape success / failure

Prometheus HTTP request rate

Prometheus memory usage

##Node Exporter — availability

Node exporter up/down per machine

##Node Exporter — CPU

Total CPU usage per node

CPU usage per core

CPU time split (user / system)

Load average (1m, 5m, 15m)

##Node Exporter — Memory

Total memory usage

Available memory

Swap usage (if present)

##Node Exporter — Disk

Disk usage per filesystem

Free disk space

Disk read throughput

Disk write throughput

##Node Exporter — Network

Network receive throughput

Network transmit throughput

##Derived / Aggregated Metrics (Prometheus rules)

Average CPU usage per worker

Peak CPU usage during pipeline runs

Average memory usage per worker

Disk usage growth over time

##Application-level (textfile collector)

Total tasks executed per worker

Task execution count per pipeline stage

Task failure count per stage

Pipeline run completion count

Pipeline currently running indicator (gauge)
