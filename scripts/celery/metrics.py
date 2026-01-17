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


#def increment_counter(name, labels, value=1):
#    """
#    Increment a counter metric.
#    """
#    label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
#    path = _metric_path(name)
#
#    current = 0
#    if os.path.exists(path):
#        with open(path, "r") as f:
#            parts = f.read().strip().split()
#            if len(parts) == 2:
#                current = int(float(parts[1]))
#
#    new_value = current + value
#    line = f'{name}{{{label_str}}} {new_value}\n'
#    _safe_write(path, line)
def increment_counter(name, labels, value=1):
    """
    Increment a counter metric.
    """
    label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
    path = _metric_path(name)
    lines = []
    found = False
    if os.path.exists(path):
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.startswith(f'{name}{{{label_str}}}'): #Increment existing
                    parts = line.split()
                    current = float(parts[1])
                    new_value = current + value
                    lines.append(f'{name}{{{label_str}}} {int(new_value)}\n')
                    found = True
                else:
                    lines.append(line + "\n")
    if not found: #Add new line
        lines.append(f'{name}{{{label_str}}} {int(value)}\n')
    _safe_write(path, "".join(lines))



def set_state(name, labels, value):
    """
    Set a state metric to a value.
    """
    label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
    path = _metric_path(name)
    line = f'{name}{{{label_str}}} {value}\n'
    _safe_write(path, line)

def set_gauge(name, labels, value):
    label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
    path = _metric_path(name)
    lines = []
    found = False
    if os.path.exists(path):
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.startswith(f'{name}{{{label_str}}}'):
                    lines.append(f'{name}{{{label_str}}} {value}\n')
                    found = True
                else:
                    lines.append(line + "\n")
    if not found:
        lines.append(f'{name}{{{label_str}}} {value}\n')
    _safe_write(path, "".join(lines))


def set_timestamp(name, labels=None):
    """
    Set a state metric to the current timestamp.
    """
    if labels is None:
        labels = {}
    now = int(time.time())
    set_state(name, labels, now)


#def task_started():
#    set_state("tasks_in_progress", {"worker": HOSTNAME}, 1)
#def task_started(run_id=None):
#    labels = {"worker": HOSTNAME}
#    if run_id is not None:
#        labels["run"] = run_id
#
#    increment_counter(
#        "tasks_in_progress",
#        labels,
#        value=1,
#    )
def task_started(run_id=None):
    set_state("tasks_in_progress", {"worker": HOSTNAME}, 1)
    if run_id is not None:
        increment_counter("tasks_started_total",{"run": run_id},value=1)

#def task_finished(task_name):
#    increment_counter(
#        "task_executions_total",
#        {"task": task_name, "worker": HOSTNAME},
#    )
#    set_state("tasks_in_progress", {"worker": HOSTNAME}, 0)
#    set_timestamp("last_task_execution_time", {"worker": HOSTNAME})
#def task_finished(task_name, run_id=None):
#    base_labels = {"task": task_name,"worker": HOSTNAME}
#    if run_id is not None:
#        base_labels["run"] = run_id
#    increment_counter("task_executions_total",base_labels,value=1)
#    progress_labels = {"worker": HOSTNAME}
#    if run_id is not None:
#        progress_labels["run"] = run_id
#    increment_counter("tasks_in_progress",progress_labels,value=-1)
#    set_timestamp("last_task_execution_time",{"worker": HOSTNAME})
def task_finished(task_name, run_id=None):
    base_labels = {"task": task_name,"worker": HOSTNAME}
    if run_id is not None:
        base_labels["run"] = run_id
    increment_counter("task_executions_total", base_labels, value=1)
    set_state("tasks_in_progress", {"worker": HOSTNAME}, 0)
    set_timestamp("last_task_execution_time", {"worker": HOSTNAME})
    set_timestamp("pipeline_last_task_completion_time",{"run": run_id})

#def task_failed(task_name):
#    increment_counter(
#        "task_failures_total",
#        {"task": task_name, "worker": HOSTNAME},
#    )
#    set_state("tasks_in_progress", {"worker": HOSTNAME}, 0)
#    set_timestamp("last_task_execution_time", {"worker": HOSTNAME})
#def task_failed(task_name, run_id=None):
#    base_labels = {"task": task_name,"worker": HOSTNAME}
#    if run_id is not None:
#        base_labels["run"] = run_id
#    increment_counter("task_failures_total",base_labels,value=1)
#    progress_labels = {"worker": HOSTNAME}
#    if run_id is not None:
#        progress_labels["run"] = run_id
#    increment_counter("tasks_in_progress",progress_labels,value=-1)
#    set_timestamp("last_task_execution_time",{"worker": HOSTNAME})
def task_failed(task_name, run_id=None):
    base_labels = {"task": task_name,"worker": HOSTNAME}
    if run_id is not None:
        base_labels["run"] = run_id
    increment_counter("task_failures_total",base_labels,value=1)
    set_state("tasks_in_progress", {"worker": HOSTNAME}, 0)
    set_timestamp("last_task_execution_time",{"worker": HOSTNAME})
    set_timestamp("pipeline_last_task_completion_time",{"run": run_id})

#def pipeline_started():
#    set_state("pipeline_running", {}, 1)
def pipeline_started(run_id=None):
    labels = {}
    if run_id is not None:
        labels["run"] = run_id
    set_state("pipeline_running", labels, 1)
    now = int(time.time())
    set_gauge("pipeline_run_start_time",{"run": run_id},now)
    if run_id is not None:
        increment_counter("tasks_started_total", {"run": run_id}, value=0)
        increment_counter("task_executions_total", {"run": run_id}, value=0)
        increment_counter("task_failures_total", {"run": run_id}, value=0)

#def pipeline_finished():
#    increment_counter("pipeline_runs_total", {})
#    set_state("pipeline_running", {}, 0)
#    set_timestamp("last_pipeline_completion_time")
def pipeline_finished(run_id=None):
    increment_counter("pipeline_runs_total", {}, value=1)
    labels = {}
    if run_id is not None:
        labels["run"] = run_id
    set_state("pipeline_running", labels, 0)
    set_timestamp("last_pipeline_completion_time", labels)

def pipeline_exp_tasks(run_id, num_seqs):
    tasks_per_seq = 6
    exp_tasks = num_seqs * tasks_per_seq
    set_gauge("pipeline_expected_tasks_total",{"run": run_id},exp_tasks)
