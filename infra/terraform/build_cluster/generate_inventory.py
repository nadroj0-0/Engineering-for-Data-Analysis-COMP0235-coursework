#!/usr/bin/env python3

"""Generate an Ansible inventory from Terraform outputs.
Usage: python3 generate_inventory.py [--write-ini inventory.ini]
"""

import json
import subprocess
import argparse
from pathlib import Path
import sys

def find_terraform_dir(start_path):
    """
    Go up from `start_path` until find Terraform working directory.
    """
    cur = start_path.resolve()
    while True:
        if (cur / ".terraform").exists() or any(cur.glob("*.tf")):
            return cur
        if cur.parent == cur:
            raise RuntimeError(
                "Could not locate Terraform directory "
                "(searched upwards from script and CWD)"
            )
        cur = cur.parent
try: #Try cwd first, script location 2nd
    TERRAFORM_DIR = find_terraform_dir(Path.cwd())
except RuntimeError:
    TERRAFORM_DIR = find_terraform_dir(Path(__file__).resolve().parent)



def run(command, **kwargs):
    return subprocess.run(command, capture_output=True, encoding='UTF-8', **kwargs)

def render_ini(inv):
    lines=[]
    lines.append("[host]")
    for h in inv["host"]["hosts"]:
        lines.append(f"{h} ansible_connection=local")
    lines.append("")
    for group in ["workers", "storage"]:
        lines.append(f"[{group}]")
        for h in inv[group]["hosts"]:
            lines.append(h)
        lines.append("")
    return "\n".join(lines)


def generate_inventory():
    host_cmd = "terraform output --json host_ips".split()
    host_ip_list = json.loads(run(host_cmd, cwd=TERRAFORM_DIR).stdout)
    host = host_ip_list[0]

    host_vars = {}
    host_vars[host] = { "ip": [host] }



    counter = 0
    workers = []

    worker_cmd = "terraform output --json worker_ips".split()
    worker_ips = json.loads(run(worker_cmd, cwd=TERRAFORM_DIR).stdout)

    for a in worker_ips:
        name = a
        host_vars[name] = { "ip": [a] }
        workers.append(name)
        counter += 1

    storage = worker_ips[0]     #Worker 1 = Storage node


    _meta = {}
    _meta["hostvars"] = host_vars
    _all = { "children": ["host", "workers", "storage"] }

    _workers = { "hosts": workers }
    _host = { "hosts" : [host] }
    _storage = { "hosts": [storage] }

    _jd = {}
    _jd["_meta"] = _meta
    _jd["all"] = _all
    _jd["workers"] = _workers
    _jd["host"] = _host
    _jd["storage"] = _storage

    return _jd


if __name__ == "__main__":

    ap = argparse.ArgumentParser(
        description = "Generate a cluster inventory from Terraform.",
        prog = __file__
    )

    mo = ap.add_mutually_exclusive_group()
    mo.add_argument("--list",action="store", nargs="*", default="dummy", help="Show JSON of all managed hosts")
    mo.add_argument("--host",action="store", help="Display vars related to the host")
    ap.add_argument("--write-ini", metavar="PATH", help="Write static inventory.ini file to PATH")

    args = ap.parse_args()

    inventory = generate_inventory()

    if args.write_ini:
        ini = render_ini(inventory)
        with open(args.write_ini, "w", encoding="utf-8") as f:
            f.write(ini)
        print(f"Wrote inventory to {args.write_ini}")
        raise SystemExit(0)

    if args.host:
        print(json.dumps({}))
    elif len(args.list) >= 0:
        print(json.dumps(inventory, indent=4))
    else:
        raise ValueError("Expecting either --host $HOSTNAME or --list")
