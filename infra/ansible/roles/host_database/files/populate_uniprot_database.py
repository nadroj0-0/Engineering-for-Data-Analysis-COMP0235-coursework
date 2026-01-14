import psycopg2
from Bio import SeqIO

FASTA_FILE = "/srv/uniprot/uniprot_dataset.fasta"
DB_NAME = "pipeline_db"
DB_USER = "postgres"
DB_HOST = "localhost"

def connect_to_database():
    """
    Open connection to postgresql and return connection and a cursor
    """
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
    )
    cursor = conn.cursor()    #cursor object used to send sql cmds
    return conn, cursor


def insert_protein(cursor, protein_id, payload):
    """
    Insert a single protein entry into the database
    """
    query = """
        INSERT INTO proteins (id, payload)
        VALUES (%s, %s)
        ON CONFLICT (id) DO NOTHING;
    """
    cursor.execute(query, (protein_id, payload))

#def read_fasta_file(file_path):
#    """
#    Read a FASTA file and return a list of (id, payload)
#
#    id: start of entry (after > up to first space)
#    payload: full FASTA entry including >
#    """
#    records = []
#    current_id = None
#    current_payload = ""
#    with open(file_path, "r") as file:
#        for line in file:
#            if line.startswith(">"):
#                # Save previous entry
#                if current_id is not None:
#                    records.append((current_id, current_payload))
#
#                current_id = line[1:].split(" ")[0]  # remove '>' and extract id
#                current_payload = line # Start new payload
#            else:
#                current_payload = current_payload + line # Add line to payload of lines
#    if current_id is not None:
#        records.append((current_id, current_payload))
#
#    return records


def read_fasta_file(file_path):
    """
    Read a FASTA file and return a list of (id, sequence)

    id: UniProt identifier (record.id)
    sequence: amino acid sequence only (no header, no newlines)
    """
    records = []
    for record in SeqIO.parse(file_path, "fasta"):
        protein_id = record.id
        sequence = str(record.seq)
        records.append((protein_id, sequence))
    return records


def populate_database():
    """
    Read the FASTA file and populate the postgresql database.
    """
    conn, cursor = connect_to_database()
    records = read_fasta_file(FASTA_FILE)
    for protein_id, payload in records:
        insert_protein(cursor, protein_id, payload)
    conn.commit()    # Make all inserts permanent
    cursor.close()
    conn.close()
    print(f"Inserted {len(records)} protein records.")


populate_database()
