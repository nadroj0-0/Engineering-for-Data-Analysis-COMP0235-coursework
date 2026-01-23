#!/usr/bin/env python3

import sys
import subprocess
import tempfile

"""
usage:
    python test_run_pipeline.py <num_ids> [run_name]
"""

UNIPROT_FASTA = "/home/almalinux/dataset/uniprot/uniprot_dataset.fasta"
SELECT_IDS_SCRIPT = "/shared/almalinux/scripts/celery/select_ids.py"
PIPELINE_SCRIPT   = "/shared/almalinux/scripts/celery/run_pipeline_host.py"


def generate_experiment_ids(num_ids):
    """
    Run select_ids.py over the full UniProt FASTA and capture output
    into a temporary experiment_ids.txt file.
    """
    tmp = tempfile.NamedTemporaryFile(
        mode="w",
        delete=False,
        prefix="experiment_ids_",
        suffix=".txt"
    )

    cmd = [
        "python3",
        SELECT_IDS_SCRIPT,
        UNIPROT_FASTA,
        str(num_ids)
    ]

    print("Selecting experiment IDs:")
    print(" ".join(cmd))

    result = subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.PIPE,
        text=True
    )

    tmp.write(result.stdout)
    tmp.close()
    return tmp.name


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python test_run_pipeline.py <num_ids> [run_name]")
        sys.exit(1)

    num_ids = int(sys.argv[1])
    run_name = sys.argv[2] if len(sys.argv) > 2 else None

    ids_file = generate_experiment_ids(num_ids)
    print(f"Generated experiment ID file: {ids_file}")

    cmd = ["python3", PIPELINE_SCRIPT, ids_file]
    if run_name:
        cmd.append(run_name)

    print("Launching pipeline:")
    print(" ".join(cmd))

    subprocess.run(cmd, check=True)
