from collections import Counter

fasta_path = "uniprot_dataset.fasta"

ids = []
bad_headers = 0
records = 0
payload_gt_errors = 0

current_id = None
current_payload_lines = []

with open(fasta_path, "r") as f:
    for line_num, line in enumerate(f, start=1):
        line = line.rstrip("\n")

        if line.startswith(">"):
            # Finalise previous record
            if current_id is not None:
                records += 1
                ids.append(current_id)
                if any(">" in l for l in current_payload_lines):
                    payload_gt_errors += 1

            # Start new record
            header = line[1:]
            if " " not in header:
                bad_headers += 1
                current_id = None
            else:
                current_id = header.split(" ", 1)[0]

            current_payload_lines = []

        else:
            current_payload_lines.append(line)

# Final record
if current_id is not None:
    records += 1
    ids.append(current_id)
    if any(">" in l for l in current_payload_lines):
        payload_gt_errors += 1

# Diagnostics
id_counts = Counter(ids)
duplicate_ids = [i for i, c in id_counts.items() if c > 1]

print("Total records:", records)
print("Unique IDs:", len(id_counts))
print("Duplicate IDs:", len(duplicate_ids))
print("Headers without space:", bad_headers)
print("Records with '>' inside payload:", payload_gt_errors)

if duplicate_ids:
    print("Example duplicate ID:", duplicate_ids[0])
