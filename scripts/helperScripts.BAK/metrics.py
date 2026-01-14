import os
import time
import shutil
from socket import gethostname

METRICS_DIR = "/home/almalinux/custom_metrics"
HOSTNAME = gethostname()


def _safe_write(filename, content):
    """
    Write a prometheus metric safely:
    write to temp file then move.
    """
    tmp_path = f"{filename}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    shutil.move(tmp_path, filename)


def _metric_path(name):
    os.makedirs(METRICS_DIR, exist_ok=True)
    return os.path.join(METRICS_DIR, f"{name}.prom")


def increment_counter(name, labels, value=1):
    """
    Increment a counter metric.
    """
    label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
    path = _metric_path(name)

    current = 0
    if os.path.exists(path):
        with open(path, "r") as f:
            parts = f.read().strip().split()
            if len(parts) == 2:
                current = int(float(parts[1]))

    new_value = current + value
    line = f'{name}{{{label_str}}} {new_value}\n'
    _safe_write(path, line)


def set_state(name, labels, value):
    """
    Set a state metric to a value.
    """
    label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
    path = _metric_path(name)
    line = f'{name}{{{label_str}}} {value}\n'
    _safe_write(path, line)


def set_timestamp(name, labels=None):
    """
    Set a state metric to the current timestamp.
    """
    if labels is None:
        labels = {}
    now = int(time.time())
    set_state(name, labels, now)


def task_started():
    set_state("tasks_in_progress", {"worker": HOSTNAME}, 1)


def task_finished(task_name):
    increment_counter(
        "task_executions_total",
        {"task": task_name, "worker": HOSTNAME},
    )
    set_state("tasks_in_progress", {"worker": HOSTNAME}, 0)
    set_timestamp("last_task_execution_time", {"worker": HOSTNAME})


def task_failed(task_name):
    increment_counter(
        "task_failures_total",
        {"task": task_name, "worker": HOSTNAME},
    )
    set_state("tasks_in_progress", {"worker": HOSTNAME}, 0)
    set_timestamp("last_task_execution_time", {"worker": HOSTNAME})

def pipeline_started():
    set_state("pipeline_running", {}, 1)


def pipeline_finished():
    increment_counter("pipeline_runs_total", {})
    set_state("pipeline_running", {}, 0)
    set_timestamp("last_pipeline_completion_time")
