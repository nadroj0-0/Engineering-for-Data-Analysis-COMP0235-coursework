import os
import time
from socket import gethostname

LOG_DIR = "/var/log/comp0235_pipeline"  #Where the log file lives
HOSTNAME = gethostname()  #Name of current machine


def _timestamp():
    """Return a timestamp."""
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _log_path():
    """One log file per worker."""
    os.makedirs(LOG_DIR, exist_ok=True)
    return os.path.join(LOG_DIR, f"pipeline_{HOSTNAME}.log") #Each worker gets its own uniqe log file


def log_info(task_name, seq_id, message): #Logs expected behaviour
    """
    Write an INFO log line.
    """
    line = (
        f"{_timestamp()} | INFO | "  #Timestampe
        f"worker={HOSTNAME} | "   #Machine
        f"task={task_name} | "   #Task
        f"seq={seq_id} | "   #Sequence task was working on
        f"{message}\n"   #Summary of what happened
    )
    with open(_log_path(), "a", encoding="utf-8") as f:  #Opens in append ("a") and adds entry 
        f.write(line)


def log_error(task_name, seq_id, message):  #Logs unexpected behaviour
    """
    Write an ERROR log line.
    """
    line = (
        f"{_timestamp()} | ERROR | "
        f"worker={HOSTNAME} | "
        f"task={task_name} | "
        f"seq={seq_id} | "
        f"{message}\n"
    )
    with open(_log_path(), "a", encoding="utf-8") as f:
        f.write(line)
