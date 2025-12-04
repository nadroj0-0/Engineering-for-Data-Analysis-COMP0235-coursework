#!/usr/bin/env python3

import json
import subprocess
import argparse

def run(command):
    return subprocess.run(command, capture_output=True, encoding='UTF-8')

def generate_inventory():
    host_cmd = "terraform output --json host_ips".split()
    host_ip_list = json.loads(run(host_cmd).stdout)
    host = host_ip_list[0]

    host_vars = {}
    host_vars[host] = { "ip": [host] }



    counter = 0
    workers = []

    worker_cmd = "terraform output --json worker_ips".split()
    worker_ips = json.loads(run(worker_cmd).stdout)

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

    jd = json.dumps(_jd, indent=4)
    return jd


if __name__ == "__main__":

    ap = argparse.ArgumentParser(
        description = "Generate a cluster inventory from Terraform.",
        prog = __file__
    )

    mo = ap.add_mutually_exclusive_group()
    mo.add_argument("--list",action="store", nargs="*", default="dummy", help="Show JSON of all managed hosts")
    mo.add_argument("--host",action="store", help="Display vars related to the host")

    args = ap.parse_args()

    if args.host:
        print(json.dumps({}))
    elif len(args.list) >= 0:
        jd = generate_inventory()
        print(jd)
    else:
        raise ValueError("Expecting either --host $HOSTNAME or --list")
