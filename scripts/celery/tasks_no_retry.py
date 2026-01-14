from celery import Celery

#app = Celery('tasks', broker = 'redis://localhost:6379/0', backend='redis://localhost:6379')
app = Celery('tasks')
app.config_from_object('celeryconfig')


#pipeline_script_tasks imports
import sys
from subprocess import Popen, PIPE
from Bio import SeqIO
import shutil
import os

#metrics imports
from metrics import (
    task_started,
    task_finished,
    task_failed,
)

#logging imports
from pipeline_logging import (
    log_info,
    log_error,
    log_warning,
    log_storage,
    log_storage_error
)

########### Toy tasks
@app.task
def add(x, y):
    return x + y

@app.task
def divide(x, y):
    return x / y

@app.task
def multiply(x, y):
    return x*y

@app.task
def subtract(x, y):
    return x-y

@app.task
def power(x, y):
    return [x ** y]

@app.task
def mean(x):
    return sum(x)/len(x)

@app.task
def diff_vect(y, x):
    diffs = []
    for value in x:
        diffs.append(value-y)
    return diffs

@app.task
def sq_vect(x):
    sqs = []
    for value in x:
        sqs.append(value ** 2)
    return sqs



########## Pipeline_scripts_tasks

"""
usage: python pipeline_script.py INPUT.fasta
approx 5min per analysis
"""

@app.task
def make_seq_dir_task(run_dir, seq_id):
    """
    Create a run directory and a sequence directory so organising the files during the pipeline
    """
    task_name = "make_seq_dir_task"
    task_started()
    log_info(task_name, seq_id, "Task started")
    success = False
    try:
        seq_dir = os.path.join(run_dir, seq_id)
        os.makedirs(seq_dir, exist_ok=True)
        log_storage(seq_id, f"Sequence directory created at {seq_dir}") #Log creation of dir
        tmp_fas_path = os.path.join(seq_dir, "tmp.fas")
        tmp_horiz_path = os.path.join(seq_dir, "tmp.horiz")
        tmp_a3m_path = os.path.join(seq_dir, "tmp.a3m")
        tmp_hhr_path = os.path.join(seq_dir, "tmp.hhr")
        hhr_parsed_path = os.path.join(seq_dir, "hhr_parse.out")
        results_parsed_path =os.path.join(seq_dir, f"{seq_id}_parsed.out")
        seq_paths = {"seq_id": seq_id, "seq_dir": seq_dir, "tmp_fas": tmp_fas_path, "tmp_horiz": tmp_horiz_path, "tmp_a3m": tmp_a3m_path, "tmp_hhr": tmp_hhr_path, "hhr_parsed": hhr_parsed_path, "parsed_results": results_parsed_path}
        success = True
        log_info(task_name, seq_id, "Task completed successfully")
        return seq_paths
    except Exception as e:
        log_storage_error(seq_id,f"Failed to create sequence directory at {seq_dir} | {type(e).__name__}: {e}")
        log_error(task_name, seq_id, f"Task failed: {str(e)}")
        task_failed(task_name)
        raise
    finally:
        if success == True:
            task_finished(task_name)

@app.task
def write_fasta_task(seq_paths, sequence):
    """
    Write the fasta sequence inot tmp.fas in the specific seq folder
    """
    task_name = "write_fasta_task"
    seq_id = seq_paths["seq_id"]
    task_started()
    log_info(task_name, seq_id, "Task started")
    success = False
    try:
        fas_file = seq_paths['tmp_fas']
        seq_id = seq_paths['seq_id']
        with open(fas_file, 'w') as fh_out:
            fh_out.write(f">{seq_id}\n{sequence}\n")
        success = True
        log_info(task_name, seq_id, "Task completed successfully")
        return seq_paths
    except Exception as e:
        log_error(task_name, seq_id, f"Task failed: {str(e)}")
        task_failed(task_name)
        raise
    finally:
        if success == True:
            task_finished(task_name)

@app.task
#def run_parser_task(hhr_file):
def run_parser_task(seq_paths):
    """
    Run the results_parser.py over the hhr file to produce the output summary
    """
    task_name = "run_parser_task"
    seq_id = seq_paths["seq_id"]
    task_started()
    log_info(task_name, seq_id, "Task started")
    success = False
    try:
        hhr_file = seq_paths['tmp_hhr']
        out_file = seq_paths['parsed_results']
#        cmd = ['python', './results_parser.py', hhr_file]
        cmd	= ['python3', '/shared/almalinux/scripts/celery/results_parser.py',
                hhr_file, seq_paths["hhr_parsed"] ]
        #path to results_parser.py file
        print(f'STEP 4: RUNNING PARSER: {" ".join(cmd)}')
        p = Popen(cmd, stdin=PIPE,stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        log_info(task_name, seq_id, f"Parser stdout:\n{out.decode()}")
        if err:
#            log_error(task_name, seq_id, f"Parser stderr:\n{err.decode()}")
             log_warning(task_name, seq_id, f"Parser warnings (non-fatal):\n{err.decode()}")
        if p.returncode != 0:
            raise RuntimeError(f"results_parser.py failed with code {p.returncode}")
        with open(out_file, 'w') as fh_out:
            fh_out.write(out.decode('utf-8'))
        success = True
        log_storage(seq_id, f"Final output written: {out_file}")
        log_info(task_name, seq_id, "Task completed successfully")
        return seq_paths
#        return out.decode("utf-8")
    except Exception as e:
        log_storage_error(seq_id,f"Failed to write final output {out_file} | {type(e).__name__}: {str(e)}")
        log_error(task_name, seq_id, f"Task failed: {str(e)}")
        task_failed(task_name)
        raise
    finally:
        if success == True:
            task_finished(task_name)

@app.task
#def run_hhsearch_task(a3m_file):
def run_hhsearch_task(seq_paths):
    """
    Run HHSearch to produce the hhr file
    """
    task_name = "run_hhsearch_task"
    seq_id = seq_paths["seq_id"]
    task_started()
    log_info(task_name, seq_id, "Task started")
    success = False
    try:
        a3m_file = seq_paths['tmp_a3m']
        hhr_file = seq_paths['tmp_hhr']
        cmd = ['/shared/almalinux/tools/hhsuite/build/src/hhsearch',
               '-i', a3m_file, '-cpu', '1', '-d',
               '/shared/almalinux/dataset/pdb70/pdb70', '-o', hhr_file]
        print(f'STEP 3: RUNNING HHSEARCH: {" ".join(cmd)}')
        p = Popen(cmd, stdin=PIPE,stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()

        if p.returncode != 0:
            raise RuntimeError(f"HHsearch failed:\n{err.decode()}")

        if not os.path.exists(hhr_file):
            raise RuntimeError("HHsearch completed but tmp.hhr was not created")

        if os.path.getsize(hhr_file) == 0:
            raise RuntimeError("HHsearch produced empty tmp.hhr")

        success = True
        log_info(task_name, seq_id, "Task completed successfully")
        return seq_paths
    except Exception as e:
        log_error(task_name, seq_id, f"Task failed: {str(e)}")
        task_failed(task_name)
        raise
    finally:
        if success == True:
            task_finished(task_name)

@app.task
#def read_horiz_task(tmp_file, horiz_file, a3m_file):
def read_horiz_task(seq_paths):
    """
    Parse horiz file and concatenate the information to a new tmp a3m file
    """
    task_name = "read_horiz_task"
    seq_id = seq_paths["seq_id"]
    task_started()
    log_info(task_name, seq_id, "Task started")
    success = False
    try:
        tmp_file = seq_paths['tmp_fas']
        horiz_file = seq_paths['tmp_horiz']
        a3m_file = seq_paths['tmp_a3m']
        pred = ''
        conf = ''
        print("STEP 2: REWRITING INPUT FILE TO A3M")
        with open(horiz_file) as fh_in:
            for line in fh_in:
                if line.startswith('Conf: '):
                    conf += line[6:].rstrip()
                if line.startswith('Pred: '):
                    pred += line[6:].rstrip()
        with open(tmp_file) as fh_in:
            contents = fh_in.read()
        with open(a3m_file, "w") as fh_out:
            fh_out.write(f">ss_pred\n{pred}\n>ss_conf\n{conf}\n")
            fh_out.write(contents)
        #return a3m_file
        success = True
        log_info(task_name, seq_id, "Task completed successfully")
        return seq_paths
    except Exception as e:
        log_error(task_name, seq_id, f"Task failed: {str(e)}")
        task_failed(task_name)
        raise
    finally:
        if success == True:
            task_finished(task_name)


@app.task
#def run_s4pred_task(input_file, out_file):
def run_s4pred_task(seq_paths):
    """
    Runs the s4pred secondary structure predictor to produce the horiz file
    """
    task_name = "run_s4pred_task"
    seq_id = seq_paths["seq_id"]
    task_started()
    log_info(task_name, seq_id, "Task started")
    success = False
    try:
        input_file = seq_paths['tmp_fas']
        out_file = seq_paths['tmp_horiz']
        cmd = ['python3', '/shared/almalinux/tools/s4pred/run_model.py',
               '-t', 'horiz', '-T', '1', input_file]
        print(f'STEP 1: RUNNING S4PRED: {" ".join(cmd)}')
        p = Popen(cmd, stdin=PIPE,stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        with open(out_file, "w") as fh_out:
            fh_out.write(out.decode("utf-8"))
        #return out_file
        success = True
        log_info(task_name, seq_id, "Task completed successfully")
        return seq_paths
    except Exception as e:
        log_error(task_name, seq_id, f"Task failed: {str(e)}")
        task_failed(task_name)
        raise
    finally:
        if success == True:
            task_finished(task_name)


@app.task
def read_input_task(file):
    """
    Function reads a fasta formatted file of protein sequences
    """
    task_name = "read_input_task"
    task_started()
    #Use the file path as the seq_id as its more informative than leaving blank
    log_info(task_name, file, "Task started") 
    success = False
    try:
        print("READING FASTA FILES")
        sequences = {}
        ids = []
        for record in SeqIO.parse(file, "fasta"):
            sequences[record.id] = record.seq
            ids.append(record.id)
        success = True
        log_info(task_name, file, "Task completed successfully")
        return(sequences)
    except Exception as e:
        log_error(task_name, file, f"Task failed: {str(e)}")
        task_failed(task_name)
        raise
    finally:
        if success == True:
            task_finished(task_name)

#if __name__ == "__main__":
#
#    sequences = read_input(sys.argv[1])
#    tmp_file = "tmp.fas"
#    horiz_file = "tmp.horiz"
#    a3m_file = "tmp.a3m"
#    hhr_file = "tmp.hhr"
#    for k, v in sequences.items():
#        print(f'Now analysing input: {k}')
#        with open(tmp_file, "w") as fh_out:
#            fh_out.write(f">{k}\n")
#            fh_out.write(f"{v}\n")
#        run_s4pred(tmp_file, horiz_file)
#        read_horiz(tmp_file, horiz_file, a3m_file)
#        run_hhsearch(a3m_file)
#        run_parser(hhr_file)
#        shutil.move("hhr_parse.out", f'{k}_parse.out')
