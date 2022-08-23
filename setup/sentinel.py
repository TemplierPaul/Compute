import os
import subprocess
import requests
from time import sleep, localtime, strftime
import time
import argparse

# IFTTT webhooks token: https://ifttt.com/maker_webhooks
# None or empty to ignore notifications
token = "bQYn8DuIiJSpmioPsxYDPl"

# To detect which command is run
cmd_grep = "CMD"

# Keys are grepped in .err files
# Value: bool, if True cancels the run when the error is found in .err
ISSUE_CANCEL = {
    "MPI.Exception": True,
    "_pickle.UnpicklingError": True,
    "Disk quota exceeded": True,
    "numpy.core._exceptions.MemoryError": True,
    "NameError": True,
    "Permission denied": False,
    "Out Of Memory": False,
    "slurmstepd": False,
    "Unknown error": False,
    'other system errors': False,
    "unexpected system error": False,
    # "Error: Failure in initializing endpoint": False,
    # 'Returned "Error" (-1) instead of "Success"': False,
    # "An error occurred in MPI_Init_thread": False,
    # "MPI_ERRORS_ARE_FATAL": False,
}

# When grepping for "error", ignore if the line contains one of these
IGNORE_ISSUES = {
    "dlerror",
    "other system errors; your job may hang, crash, or produce silent",
    "Network error",
    "CANCELLED",
    "CondaValueError",
    "to see all help / error messages",
    # 'Returned "Error" (-1) instead of "Success"',
    # "Error: Failure in initializing endpoint",
    # "An error occurred in MPI_Init_thread"
}

ISSUES = {}


def add_issue(t, i):
    if t in ISSUES:
        ISSUES[t].append(i)
    else:
        ISSUES[t] = [i]


def run(cmd):
    sp = subprocess.run(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return sp.stdout.decode('utf-8'), sp.stderr.decode('utf-8')


def clear(): return os.system('clear')


clear()


def cancel(i):
    out, err = run(f"scancel {i}")
    print(f"Canceling job {i} | {out} {err}")


WARNED = {
    k: [] for k in ISSUE_CANCEL.keys()
}


def warn(jobs, err_type):
    if not isinstance(jobs, list):
        jobs = [jobs]
    if token is None or token == "":
        return
    jobs = [i for i in jobs if i not in WARNED[err_type]]
    if len(jobs) == 0:
        return
    WARNED[err_type] += jobs
    event = "Compute"
    url = f"https://maker.ifttt.com/trigger/{event}/with/key/{token}"
    json = {
        "value1": HOST,
        "value2": " | ".join(jobs),
        "value3": err_type
    }
    requests.post(url, json=json)


HOST = run("hostname")[0].replace("\n", "")
user = run("whoami")[0].replace("\n", "")

if "pando" in HOST:
    logs_dir = f"/scratch/disc/{user}/slurm_logs/"
    HOST = "pando"
elif "olympe" in HOST:
    logs_dir = f"/tmpdir/{user}/slurm_logs/"
    HOST = "calmip"
else:
    warn([], "Compute cluster not recognised")


def get_jobs():
    jobs_cmd = run(f"squeue -u {user} -o '%.8i %.6M %.6C'")[0]
    squeue = jobs_cmd.split("\n")[1:-1]
    squeue = [i.strip() for i in squeue]

    time = {}
    cpus = {}
    running_jobs = []
    pending_jobs = []
    for s in squeue:
        i, t, c = s.split()
        time[i] = t
        cpus[i] = c
        if t == "0:00":
            pending_jobs.append(i)
        else:
            running_jobs.append(i)

    running_jobs.sort()
    pending_jobs.sort()
    return running_jobs, pending_jobs, time, cpus


def count_finished(job):
    mpiout, mpierr = run(f"cat {logs_dir}slurm.{job}.err | grep 'Run summary'")
    mpiout = mpiout.split("\n")[:-1]
    return len(mpiout)


def get_free_nodes():
    if HOST == "pando":
        mpiout, mpierr = run("sinfo -o%C%P | grep short")
        mpiout = mpiout.replace("short*\n", "")
    else:
        mpiout, mpierr = run("sinfo -o%C%P | grep exclusive")
        mpiout = mpiout.replace("exclusive*\n", "")
    allocated, idle, other, total = mpiout.split("/")
    return idle, total


def get_issues(joblist):
    global ISSUES
    ISSUES = {}
    for i in joblist:
        for grep in ISSUE_CANCEL.keys():
            mpiout, mpierr = run(
                f"cat {logs_dir}slurm.{i}.err | grep '{grep}'")
            if mpiout != "":
                add_issue(grep, i)

        for grep in ["error", "Error"]:
            mpiout, mpierr = run(
                f"cat {logs_dir}slurm.{i}.err | grep '{grep}'")
            if mpiout != "":
                l_errors = mpiout.split("\n")
                for l in l_errors:
                    if l == "":
                        continue
                    report = True
                    for ignore in IGNORE_ISSUES:
                        if ignore in l:
                            report = False
                    if report:
                        print(f"Unknown error: {l}")
                        add_issue("Unknown error", i)


def render(running_jobs, pending_jobs, time, cpus, ignore=False):
    t = localtime()
    current_time = strftime("%H:%M:%S", t)
    clear()
    print(f"{current_time} - Logged as {user} on {HOST}")
    print("------------------------------------")
    print(f"{len(running_jobs)} Running jobs")
    print(f"{len(pending_jobs)} Pending jobs")
    idle, total = get_free_nodes()
    print(f"Idle CPU cores: {idle} / {total}")
    print("------------------------------------")

    total_issues = sum([len(v) for v in ISSUES.values()])
    print(f"{total_issues} ISSUES FOUND")
    # print("------------------------------------")

    if not ignore:
        if total_issues > 0:
            for issue_type in ISSUES:
                print(f"> {issue_type}:")
                warn(jobs=ISSUES[issue_type], err_type=issue_type)
                for i in ISSUES[issue_type]:
                    print(i)
                    if issue_type in ISSUE_CANCEL and ISSUE_CANCEL[issue_type]:
                        cancel(i)

    if len(running_jobs) > 0:
        print("------------------------------------")
        print(f"RUNNING")
        for i in running_jobs:
            out, err = run(f"cat {logs_dir}slurm.{i}.out | grep '{cmd_grep}'")
            cmd = out.replace("--", "| ").replace("\n", "")
            if ("pando" in cmd and HOST == "calmip") or ("calmip" in cmd and HOST == "pando"):
                warn([i], "Wrong platform as argument")
                cancel(i)
            n_finished = count_finished(i)
            print(f"{i} ({time[i]:>8}) [{cpus[i]:>3}]\t({n_finished})  {cmd}")

    if len(pending_jobs) > 0:
        print("------------------------------------")
        print(f"Pending")
        for i in pending_jobs:
            print(f"{i} ({'0:00':>8}) [{cpus[i]:>3}]\t  pending...")
    print("------------------------------------")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get sentinel arguments')
    parser.add_argument('--freq', type=int, default=15)
    parser.add_argument('--ignore', action='store_true')
    args = parser.parse_args()

    sleep_time = args.freq

    while True:
        try:
            running_jobs, pending_jobs, time, cpus = get_jobs()
            if not args.ignore:
                get_issues(running_jobs)
            render(running_jobs, pending_jobs, time, cpus, ignore=args.ignore)
            sleep(sleep_time)
        except KeyboardInterrupt:
            print("Stopped")
            break
