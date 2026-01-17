#!/usr/bin/env python3

import os
import csv
import sys
import numpy as np

"""
usage:
    python aggregate_results.py <run_id>
"""

# Where all runs live on shared storage
RUNS_DIR = "/shared/almalinux/runs"
# Where final results should be stored on the host
HOST_RESULTS_DIR = os.path.expanduser("~/results")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python aggregate_results.py <run_id>")
        sys.exit(1)
    run_id = sys.argv[1]
    run_path = os.path.join(RUNS_DIR, run_id)
    if not os.path.isdir(run_path):
        print(f"Run directory not found: {run_path}")
        sys.exit(1)
    # Create output directory on host
    results_path = os.path.join(HOST_RESULTS_DIR, run_id)
    os.makedirs(results_path, exist_ok=True)
    # Data we will aggregate
    hits_rows = []
    all_stds = []
    all_gmeans = []
    # Loop through each sequence directory in the run
    for seq_name in os.listdir(run_path):
        seq_dir = os.path.join(run_path, seq_name)
        if not os.path.isdir(seq_dir):
            continue
        parsed_file = os.path.join(seq_dir, f"{seq_name}_parsed.out")
        # Skip sequences that failed or never produced output
        if not os.path.exists(parsed_file):
            continue
        with open(parsed_file, "r") as f:
            reader = csv.DictReader(f)
            row = next(reader)
            # For example_hits_output.csv
            hits_rows.append({"fasta_id": row["query_id"],"best_hit_id": row["best_hit"]})
            # For example_profile_output.csv
            all_stds.append(float(row["score_std"]))
            all_gmeans.append(float(row["score_gmean"]))
    if len(hits_rows) == 0:
        print("No parsed output files found, nothing to aggregate")
        sys.exit(1)
    # ---- Write example_hits_output.csv ----
    hits_output_path = os.path.join(results_path,f"{run_id}_hits_output.csv")
    with open(hits_output_path, "w", newline="") as f:
        writer = csv.DictWriter(f,fieldnames=["fasta_id", "best_hit_id"])
        writer.writeheader()
        writer.writerows(hits_rows)
    # ---- Write example_profile_output.csv ----
    profile_output_path = os.path.join(results_path,f"{run_id}_profile_output.csv")
    with open(profile_output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ave_std", "ave_gmean"])
        writer.writerow([round(np.mean(all_stds), 2),round(np.mean(all_gmeans), 2)])
    print(f"Aggregation finished for run: {run_id}")
    print(f"Results saved to: {results_path}")
