from Bio import SeqIO
from celery import chord
from tasks import run_sequence_task, aggregate_results_task

FASTA = "/home/almalinux/pipeline_example/test.fa"

run_id = "lecturer_example"

records = list(SeqIO.parse(FASTA, "fasta"))
assert len(records) == 1

record = records[0]
seq_id = record.id
sequence = str(record.seq)

chord([
    run_sequence_task.s(run_id, seq_id, sequence)
])(aggregate_results_task.s(run_id))
