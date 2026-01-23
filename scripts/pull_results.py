#!/usr/bin/env python3

import sys
import os
from minio import Minio

MINIO_ENDPOINT = "ucabjsy-s3.comp0235.condenser.arc.ucl.ac.uk"
BUCKET = "protein-pipeline"
DEST_BASE = "/home/almalinux/results"

def main(run_id: str):
    dest_dir = os.path.join(DEST_BASE, run_id)
    os.makedirs(dest_dir, exist_ok=True)

    with open("/shared/almalinux/miniopass") as f:
        secret = f.read().strip()

    client = Minio(
        MINIO_ENDPOINT,
        access_key="myminioadmin",
        secret_key=secret,
        secure=True,
    )

    files = [
        f"{run_id}/output/{run_id}_hits_output.csv",
        f"{run_id}/output/{run_id}_profile_output.csv",
    ]

    for obj in files:
        local = os.path.join(dest_dir, os.path.basename(obj))
        print(f"Downloading {obj} → {local}")
        client.fget_object(BUCKET, obj, local)

    print(f"Results downloaded to {dest_dir}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: pull_results.py <run_id>")
        sys.exit(1)

    main(sys.argv[1])
