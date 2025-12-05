#!/usr/bin/env python3

import sys
import os
from Bio import SeqIO
from celery import chain


from tasks import make_seq_dir_task
from tasks import write_fasta_task
from tasks import run_s4pred_task
from tasks import read_horiz_task
from tasks import run_hhsearch_task
from tasks import run_parser_task

def read_input(fasta_path):
    """Reead a fasta file and returns a dictionary {seq_id : sequence}"""
    sequences = {}
    for record in SeqIO.parse(fasta_path, "fasta"):
        sequences[record.id] = str(record.seq)
    return sequences


def submit_chain(run_name, seq_id, sequence):
    """
    Build and dispatch the Celery chain for one sequence.
    """
    c = chain(
        make_seq_dir_task.s(run_name, seq_id),
        write_fasta_task.s(sequence),   
        run_s4pred_task.s(),
        read_horiz_task.s(),
        run_hhsearch_task.s(),
        run_parser_task.s(),
    )
    return c.apply_async()



if __name__ == "__main__":
    fasta_path = sys.argv[1]
    run_name = sys.argv[2]
    os.makedirs(run_name, exist_ok=True)
    sequences = read_input(fasta_path)
    for k, v in sequences.items():
        print(f'Now analysing input: {k}')
        submit_chain(run_name, k, v)
    print("All sequences sent for analysis")


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
