from celery import Celery
from celery import shared_task
from minio import Minio
import io
from minio.error import S3Error
import subprocess

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
    pipeline_finished
)

#logging imports
from pipeline_logging import (
    log_info,
    log_error,
    log_warning,
    log_storage,
    log_storage_error
)


########## Pipeline_scripts_tasks

"""
usage: python pipeline_script.py INPUT.fasta
approx 5min per analysis
"""

def make_seq_dir(run_id, run_dir, seq_id):
    """
    Create a run directory and a sequence directory so organising the files during the pipeline
    """
    task_name = "make_seq_dir"
    log_info(task_name, seq_id, "Started")
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
        seq_paths = {"run_id": run_id, "seq_id": seq_id, "seq_dir": seq_dir, "tmp_fas": tmp_fas_path, "tmp_horiz": tmp_horiz_path, "tmp_a3m": tmp_a3m_path, "tmp_hhr": tmp_hhr_path, "hhr_parsed": hhr_parsed_path, "parsed_results": results_parsed_path}
        log_info(task_name, seq_id, "Completed")
        return seq_paths
    except Exception as e:
        log_storage_error(seq_id,f"Failed to create sequence directory at {seq_dir} | {type(e).__name__}: {e}")
        log_error(task_name, seq_id, f"Failed: {str(e)}")
        raise

def write_fasta(seq_paths, sequence):
    """
    Write the fasta sequence inot tmp.fas in the specific seq folder
    """
    task_name = "write_fasta"
    seq_id = seq_paths["seq_id"]
    run_id = seq_paths["run_id"]
    log_info(task_name, seq_id, "Started")
    try:

        if not sequence or str(sequence).strip() == "":
            raise RuntimeError("Sequence is empty or missing")

        fas_file = seq_paths['tmp_fas']
        seq_id = seq_paths['seq_id']
        with open(fas_file, 'w') as fh_out:
            fh_out.write(f">{seq_id}\n{sequence}\n")

        if not os.path.exists(fas_file):
            raise RuntimeError("tmp.fas was not created")
        if os.path.getsize(fas_file) == 0:
            raise RuntimeError("tmp.fas is empty after write")

        log_info(task_name, seq_id, "Completed")
        return seq_paths
    except Exception as e:
        log_error(task_name, seq_id, f"Failed: {str(e)}")
        raise


#def run_parser_task(hhr_file):
def run_parser(seq_paths):
    """
    Run the results_parser.py over the hhr file to produce the output summary
    """
    task_name = "run_parser"
    seq_id = seq_paths["seq_id"]
    run_id = seq_paths["run_id"]
    log_info(task_name, seq_id, "Started")
    try:
        hhr_file = seq_paths['tmp_hhr']
        out_file = seq_paths['parsed_results']

        if not os.path.exists(hhr_file) or os.path.getsize(hhr_file) == 0:
            raise RuntimeError("tmp.hhr missing/empty (HHsearch output not ready)")

        cmd	= ['python3', '/shared/almalinux/scripts/celery/results_parser.py',
                hhr_file, seq_paths["hhr_parsed"] ]
        print(f'STEP 4: RUNNING PARSER: {" ".join(cmd)}')
        p = Popen(cmd, stdin=PIPE,stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        log_info(task_name, seq_id, f"Parser stdout:\n{out.decode()}")
        if err:
             log_warning(task_name, seq_id, f"Parser warnings (non-fatal):\n{err.decode()}")
        if p.returncode != 0:
            raise RuntimeError(f"results_parser.py failed with code {p.returncode}")
        with open(out_file, 'w') as fh_out:
            fh_out.write(out.decode('utf-8'))
        success = True
        log_storage(seq_id, f"Final output written: {out_file}")
        log_info(task_name, seq_id, "Completed")
        return seq_paths
    except Exception as e:
        log_storage_error(seq_id,f"Failed to write final output {out_file} | {type(e).__name__}: {str(e)}")
       	log_error(task_name, seq_id, f"Failed: {str(e)}")
        raise


def run_hhsearch(seq_paths):
    """
    Run HHSearch to produce the hhr file
    """
    task_name = "run_hhsearch"
    seq_id = seq_paths["seq_id"]
    run_id = seq_paths["run_id"]
    log_info(task_name, seq_id, "Started")
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

        log_info(task_name, seq_id, "Completed")
        return seq_paths
    except Exception as e:
       	log_error(task_name, seq_id, f"Failed: {str(e)}")
        raise


def read_horiz(seq_paths):
    """
    Parse horiz file and concatenate the information to a new tmp a3m file
    """
    task_name = "read_horiz"
    seq_id = seq_paths["seq_id"]
    run_id = seq_paths["run_id"]
    log_info(task_name, seq_id, "Started")
    try:
        tmp_file = seq_paths['tmp_fas']
        horiz_file = seq_paths['tmp_horiz']
        a3m_file = seq_paths['tmp_a3m']

        if not os.path.exists(horiz_file):
            raise RuntimeError("tmp.horiz missing (S4Pred output not ready)")
        if os.path.getsize(horiz_file) == 0:
            raise RuntimeError("tmp.horiz empty (S4Pred output not ready)")
        if not os.path.exists(tmp_file):
            raise RuntimeError("tmp.fas missing (FASTA not written yet)")
        if os.path.getsize(tmp_file) == 0:
            raise RuntimeError("tmp.fas empty")

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

        if pred == "" or conf == "":
            raise RuntimeError("tmp.horiz did not contain Pred/Conf lines")

        log_info(task_name, seq_id, "Completed")
        return seq_paths
    except Exception as e:
       	log_error(task_name, seq_id, f"Failed: {str(e)}")
        raise


def run_s4pred(seq_paths):
    """
    Runs the s4pred secondary structure predictor to produce the horiz file
    """
    task_name = "run_s4pred"
    seq_id = seq_paths["seq_id"]
    run_id = seq_paths["run_id"]
    log_info(task_name, seq_id, "Started")
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
        log_info(task_name, seq_id, "Completed")
        return seq_paths
    except Exception as e:
       	log_error(task_name, seq_id, f"Failed: {str(e)}")
        raise



def read_input(file):
    """
    Function reads a fasta formatted file of protein sequences
    """
    task_name = "read_input_task"
    #Use the file path as the seq_id as its more informative than leaving blank
    log_info(task_name, file, "Started") 
    try:
        print("READING FASTA FILES")
        sequences = {}
        ids = []
        for record in SeqIO.parse(file, "fasta"):
            sequences[record.id] = record.seq
            ids.append(record.id)
        log_info(task_name, file, "Completed")
        return(sequences)
    except Exception as e:
        log_error(task_name, file, f"Failed: {str(e)}")
        raise

def get_minio_client():
    with open("/shared/almalinux/miniopass", "r", encoding="utf-8") as f:
        secret_key = f.read().strip()
    return Minio("ucabjsy-s3.comp0235.condenser.arc.ucl.ac.uk",access_key="myminioadmin",secret_key=secret_key,secure=True,)

def ensure_bucket(client, bucket):
    try:
        client.make_bucket(bucket)
    except S3Error as e:
        if e.code not in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
            raise 

def put_file(client, bucket, object_name, local_path):
    ensure_bucket(client, bucket)
    client.fput_object(bucket, object_name, local_path)


def upload_parsed_output(seq_paths):
    task_name = "upload_to_minio"
    seq_id = seq_paths["seq_id"]
    log_info(task_name, seq_id, "Started")
    try:
        local_path = seq_paths["parsed_results"]
        if not os.path.exists(local_path):
            raise RuntimeError("Parsed output missing")
        client = get_minio_client()
        bucket = "protein-pipeline"
        object_name = f"{seq_paths['run_id']}/{seq_id}.out"
        put_file(client, bucket, object_name, local_path)
        log_storage(seq_id, f"Uploaded to MinIO: {bucket}/{object_name}")
        log_info(task_name, seq_id, "Completed")
    except Exception as e:
        log_storage_error(seq_id, f"Minio upload failed: {str(e)}")
        log_error(task_name, seq_id, f"Failed: {str(e)}")
        raise

@app.task(autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 30}, bind=True)
def run_sequence_task(self, run_id, seq_id, sequence):
    run_dir = f"/shared/almalinux/runs/{run_id}"
    task_name = "run_sequence_task"
    task_started(run_id)
    log_info(task_name, seq_id, "Sequence started")
    success = False
    try:
        seq_paths = make_seq_dir(run_id, run_dir, seq_id)
        seq_paths = write_fasta(seq_paths, sequence)
        seq_paths = run_s4pred(seq_paths)
        seq_paths = read_horiz(seq_paths)
        seq_paths = run_hhsearch(seq_paths)
        seq_paths = run_parser(seq_paths)
        upload_parsed_output(seq_paths)
        success = True
        log_info(task_name, seq_id, "Sequence completed successfully")
        return seq_paths
    except Exception as e:
        attempt = self.request.retries + 1
        log_error(task_name, seq_id, f"Attempt {attempt} failed: {str(e)}")
        if self.request.retries >= self.max_retries:
            task_failed(task_name, run_id)
        raise
    finally:
        if success == True:
            task_finished(task_name, run_id)

def upload_aggregated_csvs(run_id):
    client = get_minio_client()
    bucket = "protein-pipeline"
    output_dir = f"/shared/almalinux/runs/{run_id}/output"
    if not os.path.isdir(output_dir):
        raise RuntimeError(f"output directory not found: {output_dir}")
    files = [f"{run_id}_hits_output.csv",f"{run_id}_profile_output.csv"]
    for fname in files:
        local_path = os.path.join(output_dir, fname)
        if not os.path.exists(local_path):
            raise RuntimeError(f"No aggregated csv: {local_path}")
        object_name = f"{run_id}/output/{fname}"
        put_file(client, bucket, object_name, local_path)


@app.task
def aggregate_results_task(results, run_id):
    """
    Aggregates results csvs after all sequences are complete, triggered by celery chord.
    """
    log_info("aggregate_results", run_id, "Started")
    cmd = ["python3","/shared/almalinux/scripts/celery/aggregate_results.py",run_id,]
    subprocess.check_call(cmd)
    upload_aggregated_csvs(run_id)
    log_info("aggregate_results", run_id, "Completed")
    pipeline_finished(run_id)
    return True
