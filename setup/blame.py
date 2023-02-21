import os
import subprocess
import requests
from time import sleep, localtime, strftime
import time
import argparse
import numpy as np


def run(cmd):
    sp = subprocess.run(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return sp.stdout.decode('utf-8'), sp.stderr.decode('utf-8')


def clear(): return os.system('clear')


HOST = run("hostname")[0].replace("\n", "")
user = run("whoami")[0].replace("\n", "")

if "pando" in HOST or "node" in HOST:
    print("Pando")
    logs_dir = f"/scratch/disc/{user}/slurm_logs/"
    HOST = "pando"
elif "olympe" in HOST:
    print("CALMIP")
    logs_dir = f"/tmpdir/{user}/slurm_logs/"
    HOST = "calmip"
else:
    print("Unknown host", HOST, user)
    warn([], "Compute cluster not recognised")


jobs_cmd = run(f"squeue -o '%u %.8i %.6M %.6D %R'")[0]
squeue = jobs_cmd.split("\n")[1:-1]
squeue = [i.strip() for i in squeue]

users = {}
for s in squeue:
    u, i, t, c, r = s.split(maxsplit=4)
    c = int(c)
    if u not in users:
        users[u] = {
            "running": [],
            "pending": []
        }
    if t == "0:00":
        users[u]["pending"].append(c)
    else:
        users[u]["running"].append(c)

names, cpus = [], []
for k, v in users.items():
    names.append(k)
    cpus.append(sum(v["running"]))

indices = np.argsort(-1 * np.array(cpus))[:10]
for i in indices:
    u = names[i]
    d = users[u]

    p = d["pending"]
    r = d["running"]
    print(f"{u}: R {len(r)} ({sum(r)}) | R {len(p)} ({sum(p)})")
