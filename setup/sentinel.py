import os
import subprocess
import requests
from time import sleep, localtime, strftime
import time
import argparse
# test
# IFTTT webhooks token: https://ifttt.com/maker_webhooks
# None or empty to ignore notifications

# get token from env 
# token = os.environ.get('IFTTT_TOKEN')
token = "bQYn8DuIiJSpmioPsxYDPl"

MAX_PENDING = 30

# To detect which command is run
cmd_grep = "CMD"

REQUEUE_FAILED = True

args_to_parse = ['--env', '--optim', '--seeding', "--pop"]

# Keys are grepped in .err files
# Value: bool, if True cancels the run when the error is found in .err
ISSUE_CANCEL = {
    "Exception in thread SockSrvRdThr": True,
    "MPI.Exception": True,
    "_pickle.UnpicklingError": True,
    "Disk quota exceeded": True,
    "numpy.core._exceptions.MemoryError": True,
    "NameError": True,
    "Segmentation fault": True,
    "Permission denied": False,
    "Out Of Memory": False,
    "ObjectStoreFullError": True,
    # "slurmstepd": False,
    "Unknown error": False,
    'other system errors': False,
    "unexpected system error": False,
    "Internal wandb error": False,
    "unrecognized arguments": True,
    "FALED": False,
    "slow_operation_alarm.cc": True, # Jax slow operation
    "CUDA_ERROR_OUT_OF_MEMORY": False,
    # "Waiting for W&B process to finish... (success)": True,
    # "GOAWAY": False,
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
    "wandb: Network error resolved",
    "retrying request",
    "internal database error",
    "GOAWAY",
    "This warning will be replaced by an error",
    # "slurmstepd",
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

def clear_core():
    out, err = run("rm core.*")
    return out, err

def clear(): return os.system('clear')

def make_red(text):
    return "\033[1;31;40m" + text + "\033[0m"

def make_green(text):
    return "\033[1;32;40m" + text + "\033[0m"

def make_yellow(text):
    return "\033[1;33;40m" + text + "\033[0m"

def make_blue(text):
    return "\033[1;34;40m" + text + "\033[0m"

def make_magenta(text):
    return "\033[1;35;40m" + text + "\033[0m"

def make_cyan(text):
    return "\033[1;36;40m" + text + "\033[0m"

def make_white(text):
    return "\033[1;37;40m" + text + "\033[0m"


# clear()


def cancel(i):
    out, err = run(f"scancel {i}")
    print(f"Canceling job {i} | {out} {err}")

def requeue(i):
    out, err = run(f"scontrol requeue {i}")
    print(f"Requeuing job {i} | {out} {err}")

stop = requeue if REQUEUE_FAILED else cancel

WARNED = {
    k: [] for k in ISSUE_CANCEL.keys()
}


def warn(jobs, err_type):
    if not isinstance(jobs, list):
        jobs = [jobs]
    if len(jobs) == 0:
        return
    if token is None or token == "":
        return
    jobs = [i for i in jobs if i not in WARNED[err_type]]
    # get unique jobs
    jobs = list(set(jobs))
    WARNED[err_type] += jobs
    event = "Compute"
    url = f"https://maker.ifttt.com/trigger/{event}/with/key/{token}"
    jobs = " | ".join(jobs)
    if jobs.replace(" ", "") == "":
        return

    stopped = ""
    if err_type in ISSUE_CANCEL and ISSUE_CANCEL[err_type]:
        stopped = " (Requeued)" if REQUEUE_FAILED else " (Canceled)"

    json = {
        "value1": HOST,
        "value2": jobs,
        "value3": err_type + stopped
    }
    requests.post(url, json=json)


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


def get_jobs():
    pending_reason = None
    jobs_cmd = run(f"squeue --all -u {user} -o '%.8i %.6M %.6C %R'")[0]
    squeue = jobs_cmd.split("\n")[1:-1]
    squeue = [i.strip() for i in squeue]

    time = {}
    cpus = {}
    running_jobs = []
    pending_jobs = []
    for s in squeue:
        try:
            i, t, c, r = s.split(maxsplit=3)
        except:
            print("Error parsing squeue\n", s)
            for i in s.split(maxsplit=3):
                print(i)
            raise ValueError
        time[i] = t
        cpus[i] = c
        if t == "0:00":
            pending_jobs.append(i)
            if "Priority" not in r:
                pending_reason = r
        else:
            running_jobs.append(i)
    if pending_jobs and pending_reason is None:
        pending_reason = "Priority"

    running_jobs.sort()
    pending_jobs.sort()
    return running_jobs, pending_jobs, time, cpus, pending_reason


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

def get_free_gpus():
    mpiout, mpierr = run("squeue --all -h -t R -O gres | grep gpu|wc -l")
    idle = int(mpiout)
    if HOST == "pando":
        mpiout, mpierr = run('sinfo --Node --format="%.10P  %.10G" | grep -vE "gpucpu|visu" | grep gpu:')
    else:
        mpiout, mpierr = run("sinfo --Node --Format=gres | grep gpu:")
    gpus = mpiout.split("gpu")
    max_gpu = 0
    for g in gpus:
        if ":" in g:
            g = g.split(":")[-1]
            max_gpu += int(g)
    max_gpu = max_gpu    
    return max_gpu - idle, max_gpu

def get_pending_gpus():
    command = f"squeue --all --states=PD | grep gpu | grep -v {user[:8]}"
    mpiout, mpierr = run(command)
    pending = mpiout.count("0:00")
    return pending

def get_issues(joblist):
    global ISSUES
    ISSUES = {}
    for i in joblist:
        for grep in ISSUE_CANCEL.keys():
            mpiout, mpierr = run(
                f"cat {logs_dir}slurm.{i}.err | grep '{grep}'")
            if mpiout != "":
                add_issue(grep, i)
        # print("Known issues")

        for grep in ["error", "Error"]:
            mpiout, mpierr = run(
                f"cat {logs_dir}slurm.{i}.err | grep '{grep}'")
            if mpiout != "":
                l_errors = mpiout.split("\n")
                for l in l_errors:
                    if l == "":
                        continue
                    report = all(i not in l for i in IGNORE_ISSUES) and all(
                        i not in l for i in ISSUE_CANCEL.keys())
                    # for ignore in IGNORE_ISSUES:
                    #     if ignore in l:
                    #         report = False
                    if report:
                        # print(f"Unknown error: {l}")
                        add_issue("Unknown error", i)
        # print("Unknown issues")


def render(running_jobs, pending_jobs, time, cpus, args, pending_reason):
    ignore = args.ignore
    wandb = args.wandb
    config = args.config
    clean = len(args.parse) > 0

    t = localtime()
    current_time = strftime("%H:%M:%S", t)
    if not args.debug:
        clear()
    print(f"{current_time} - Logged as {user} on {HOST}")
    print("------------------------------------")
    r_j = f"{len(running_jobs)} Running jobs"
    if len(running_jobs) > 0:
        r_j = make_green(r_j)
    p_j = f"{len(pending_jobs)} Pending jobs"
    if len(pending_jobs) > 0:
        p_j = make_red(p_j)
    print(r_j)
    print(p_j)

    idle, total = get_free_nodes()
    print(f"Idle CPU cores: {idle} / {total}")
    idle, total = get_free_gpus()
    s = f"Idle GPUs: {idle} / {total}"
    if idle > 0:
        s = make_green(s)
    else:
        s = make_red(s)
    print(s)
    pending = get_pending_gpus()
    if pending > 0:
        pending = f"Requested GPUs: {pending}"
        pending = make_red(pending)
    else:
        pending = f"Requested GPUs: {pending}"
        pending = make_green(pending)
    print(pending)

    total_issues = sum(len(v) for v in ISSUES.values())
    if total_issues > 0:
        print("------------------------------------")
        print(f"{total_issues} ISSUES FOUND")
    # print("------------------------------------")

    if not ignore and total_issues > 0:
        for issue_type in ISSUES:
            print(f"> {issue_type}:")
            warn(jobs=ISSUES[issue_type], err_type=issue_type)
            for i in ISSUES[issue_type]:
                print(i)
                if issue_type in ISSUE_CANCEL and ISSUE_CANCEL[issue_type]:
                    stop(i)

    if len(running_jobs) > 0:
        print("------------------------------------")
        print("RUNNING")
        for i in running_jobs:
            if wandb:
                out, err = run(
                    f"cat {logs_dir}slurm.{i}.out | grep 'wandb run: '")
                # cmd = out
                cmd = out.replace("wandb run: ", " ").replace("\n", "")
                cmd = f'WandB: {cmd}'
            elif config:
                if args.max_fit:
                    try:
                        out, err = run(
                            f"cat {logs_dir}slurm.{i}.err | grep 'Gen:'")
                        out = out.split("\r")[-1]
                        max_fit = out.split("max_fitness: ")[1].split(",")[0]
                        max_fit = f" -> {float(max_fit):>.0f}"
                    except:
                        max_fit = ""
                else:
                    max_fit = ""

                out, err = run(
                    f"cat {logs_dir}slurm.{i}.out")
                try:
                    config_cmd = out.split("Initialized wandb")
                    if len(config_cmd) == 0:
                        raise ValueError
                    config_cmd = config_cmd[0]
                    config_cmd = config_cmd.split('\n')[-2]
                    config_cmd = make_green(config_cmd)
                    try:
                        net = out.split("Policy network MLP")[1].split("\n")[0]
                        net = make_yellow(net)
                    except:
                        net = ""
                    try:
                        critic = out.split("Critic network MLP")[1].split("\n")[0]
                        critic = make_yellow(critic)
                    except:
                        critic = ""
                    run_cmd = out.split(cmd_grep)[1].split("\n")[0]
                    env = run_cmd.split("--env=")[1].split(" ")[0]
                    env = make_red(env)
                    seed = run_cmd.split("--seed=")[1].split(" ")[0]
                    seed = make_red(seed)
                    tag = run_cmd.split("--tag=")[1].split(" ")[0]
                    tag = make_blue(tag)
                    # print(env)
                    cmd = f"{env:<15} {seed:<2} [{tag}] {max_fit} \n{config_cmd} - {net} | {critic}"
                except:
                    cmd = "Starting..."
            elif clean:
                out, err = run(
                    f"cat {logs_dir}slurm.{i}.out | grep '{cmd_grep}'")
                out = out.replace("\n", "")
                arg_list = []
                for l in out.split("--")[1:]:
                    if "=" in l:
                        k, v = l.split("=")
                    else:
                        k = l
                        v = "True"
                    if k in args_to_parse:
                        arg_list.append(v)
                # Get env argument
                # arg_list = [d[arg] for arg in args_to_parse if arg in d]

                cmd = " | ".join(arg_list)

            else:
                out, err = run(
                    f"cat {logs_dir}slurm.{i}.out | grep '{cmd_grep}'")
                cmd = out.replace("--", "| ").replace("\n", "")

            if ("pando" in cmd and HOST == "calmip") or ("calmip" in cmd and HOST == "pando"):
                warn([i], "Wrong platform as argument")
                cancel(i)
            n_finished = count_finished(i)
            # print(f"{i} ({time[i]:>8}) [{cpus[i]:>3}]\t({n_finished})  {cmd}")
            run_data = f" > {i} ({time[i]:>8}) [{cpus[i]:>3}]"
            # run_data = make_blue(run_data)
            print(f"{run_data} \n{cmd}")

    if len(pending_jobs) > 0:
        print("------------------------------------")
        print(f"Pending {pending_reason}")
        if len(pending_jobs) + len(running_jobs) > args.pending:
            pending_jobs = pending_jobs[:args.pending -
                                        len(running_jobs) - len(pending_jobs)]
            for i in pending_jobs:
                print(f"{i} ({'0:00':>8}) [{cpus[i]:>3}]\t  pending...")
            print("Too many jobs to display...")
        else:
            for i in pending_jobs:
                print(f"{i} ({'0:00':>8}) [{cpus[i]:>3}]\t  pending...")
    print("------------------------------------")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get sentinel arguments')
    parser.add_argument('--freq', type=int, default=15,
                        help='Refresh frequency')
    parser.add_argument('--ignore', action='store_true', help='Ignore issues')
    parser.add_argument('--wandb', action='store_true',
                        help='Show wandb commands')
    parser.add_argument('--config', action='store_true',
                        help='Get config field')
    parser.add_argument('--headless', action='store_true',
                        help='Run without display')
    parser.add_argument('--debug', action='store_true',
                        help='One loop, no clear')
    parser.add_argument('--pending', type=int, default=MAX_PENDING,
                        help='Max pending jobs')
    parser.add_argument('--max_fit', action='store_true',
                        help='Get max fitness')
    # list of args to parse
    parser.add_argument('--parse', nargs='+', default=[],
                        help='List of args to parse, plots the command if empty')
    args = parser.parse_args()

    args_to_parse = [f"{i}" for i in args.parse]
    print(args_to_parse)

    sleep_time = args.freq

    while True:
        try:
            out, err = clear_core()
            # print("Getting jobs...")
            running_jobs, pending_jobs, time, cpus, pending_reason = get_jobs()
            # print("Getting issues...")
            if not args.ignore:
                get_issues(running_jobs)
            # print("Rendering...")
            if not args.headless:
                render(running_jobs, pending_jobs, time, cpus,
                       args=args, pending_reason=pending_reason)
            if args.debug:
                break
            sleep(sleep_time)
        except KeyboardInterrupt:
            print("Stopped")
            break
