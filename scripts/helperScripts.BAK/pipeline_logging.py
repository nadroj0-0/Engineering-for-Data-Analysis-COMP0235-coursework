import os
import time
import logging
from socket import gethostname

LOG_DIR = "/var/log/protien_analysis_pipeline"  #Where the log file lives
HOSTNAME = gethostname()  #Name of current machine
STORAGE_LOG_PATH = "/shared/almalinux/storage_logs/storage.log" #Where on NFS storage log lives


def _timestamp():
    """Return a timestamp."""
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _log_path():
    """One log file per worker."""
    os.makedirs(LOG_DIR, exist_ok=True)
    return os.path.join(LOG_DIR, f"pipeline_{HOSTNAME}.log") #Each worker gets its own uniqe log file


logger = logging.getLogger("pipeline_logger")  #Make logging object
if not logger.handlers:  #Only add one handler
    logger.setLevel(logging.INFO)  # Logger taeks INFO and ERROR messages
    file_handler = logging.FileHandler(_log_path())  #Log as a file at the log path
    file_handler.setLevel(logging.INFO)  #handler writes INFO and ERROR messages to file
    formatter = logging.Formatter("%(message)s")   #Define structure of entry
    file_handler.setFormatter(formatter)   #Tells handler structure we just defined
    logger.addHandler(file_handler)   #Attach handler to logger object so logs acc get written


def log_info(task_name, seq_id, message): #Logs expected behaviour
    """
    Write an INFO log line.
    """
    #INFO log message
    line = (
        f"{_timestamp()} | INFO | "  #Timestampe
        f"worker={HOSTNAME} | "   #Machine
        f"task={task_name} | "   #Task
        f"seq={seq_id} | "   #Sequence task was working on
        f"{message}\n"   #Summary of what happened
    )
    logger.info(line) #Send log message to logger

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
    logger.error(line)

storage_logger = logging.getLogger("storage_logger")
if not storage_logger.handlers:
    storage_logger.setLevel(logging.INFO)
    os.makedirs(os.path.dirname(STORAGE_LOG_PATH), exist_ok=True)
    handler = logging.FileHandler(STORAGE_LOG_PATH)
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    storage_logger.addHandler(handler)

def log_storage(seq_id, message):
    """
    Log a storage event to the storage node log.
    """
    line = (
        f"{_timestamp()} | STORAGE | "
        f"seq={seq_id} | "
        f"{message}\n"
    )
    storage_logger.info(line)

def log_storage_error(seq_id, message):
    """
    Log a storage-related error event to the storage log.
    """
    line = (
        f"{_timestamp()} | STORAGE_ERROR | "
        f"seq={seq_id} | "
        f"{message}\n"
    )
    storage_logger.error(line)
