#!/usr/bin/env python3

from Bio import SeqIO
import tempfile
import sys


def extract_ids(fasta_path):
    ids = [record.id for record in SeqIO.parse(fasta_path, "fasta")]
    if not ids:
        raise ValueError("FASTA file contains no sequences")
    tmp = tempfile.NamedTemporaryFile(mode="w",delete=False,prefix="experiment_ids_",suffix=".txt")
    for seq_id in ids:
        tmp.write(seq_id + "\n")
    tmp.close()
    return tmp.name


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python extract_ids_from_fasta.py <fasta_file>")
        sys.exit(1)
    ids_file = extract_ids(sys.argv[1])
    print(ids_file)
