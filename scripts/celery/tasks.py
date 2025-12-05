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

    seq_dir = os.path.join(run_dir, seq_id)
    os.makedirs(seq_dir, exist_ok=True)
    tmp_fas_path = os.path.join(seq_dir, "tmp.fas")
    tmp_horiz_path = os.path.join(seq_dir, "tmp.horiz")
    tmp_a3m_path = os.path.join(seq_dir, "tmp.a3m")
    tmp_hhr_path = os.path.join(seq_dir, "tmp.hhr")
    results_parsed_path =os.path.join(seq_dir, f"{seq_id}_parsed.out")
    seq_paths = {"seq_id": seq_id, "seq_dir": seq_dir, "tmp_fas": tmp_fas_path, "tmp_horiz": tmp_horiz_path, "tmp_a3m": tmp_a3m_path, "tmp_hhr": tmp_hhr_path, "parsed_results": results_parsed_path}
    return seq_paths


@app.task
def write_fasta_task(seq_paths, sequence):
    """
    Write the fasta sequence inot tmp.fas in the specific seq folder
    """
    fas_file = seq_paths['tmp_fas']
    seq_id = seq_paths['seq_id']
    with open(fas_file, 'w') as fh_out:
        fh_out.write(f">{seq_id}\n{sequence}\n")
    return seq_paths


@app.task
#def run_parser_task(hhr_file):
def run_parser_task(seq_paths):
    """
    Run the results_parser.py over the hhr file to produce the output summary
    """
    hhr_file = seq_paths['tmp_hhr']
    out_file = seq_paths['parsed_results']
#    cmd = ['python', './results_parser.py', hhr_file]
    cmd	= ['python', '/shared/almalinux/scripts/helperScripts/results_parser.py', hhr_file]
    #path to results_parser.py file
    print(f'STEP 4: RUNNING PARSER: {" ".join(cmd)}')
    p = Popen(cmd, stdin=PIPE,stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    with open(out_file, 'w') as fh_out:
        fh_out.write(out.decode('utf-8'))
    return seq_paths
#    return out.decode("utf-8")

@app.task
#def run_hhsearch_task(a3m_file):
def run_hhsearch_task(seq_paths):
    """
    Run HHSearch to produce the hhr file
    """
    a3m_file = seq_paths['tmp_a3m']
    hhr_file = seq_paths['tmp_hhr']
    cmd = ['/shared/almalinux/tools/hhsuite/build/src/hhsearch',
           '-i', a3m_file, '-cpu', '1', '-d',
           '/shared/almalinux/dataset/pdb70', '-o', hhr_file]
    print(f'STEP 3: RUNNING HHSEARCH: {" ".join(cmd)}')
    p = Popen(cmd, stdin=PIPE,stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    return seq_paths

@app.task
#def read_horiz_task(tmp_file, horiz_file, a3m_file):
def read_horiz_task(seq_paths):
    """
    Parse horiz file and concatenate the information to a new tmp a3m file
    """
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
    return seq_paths

@app.task
#def run_s4pred_task(input_file, out_file):
def run_s4pred_task(seq_paths):
    """
    Runs the s4pred secondary structure predictor to produce the horiz file
    """
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
    return seq_paths

@app.task
def read_input_task(file):
    """
    Function reads a fasta formatted file of protein sequences
    """
    print("READING FASTA FILES")
    sequences = {}
    ids = []
    for record in SeqIO.parse(file, "fasta"):
        sequences[record.id] = record.seq
        ids.append(record.id)
    return(sequences)


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
