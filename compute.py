from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

import paramiko
import subprocess
import math
import sys


def read(filename):
    with open(filename, 'r') as f:
        return load(f, Loader=Loader)


class Server:
    def __init__(self, host, user, alias=None, configs=None):
        self.host = host
        self.port = 22
        self.user = user
        self.alias = alias
        self.ssh = None
        self.connected = False
        self.configs = configs

    def __repr__(self):
        return f"Server {self.alias} ({self.user}@{self.host})"

    def connect(self):
        assert self.test_connect(), f"{self} | Failed to connect"
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(self.host, self.port, self.user)
        self.connected = True

    def test_connect(self):
        s = f"""timeout 5 ssh {self.user}@{self.host} << EOF
echo "Connected!"
EOF"""
        out, err = self.run_local(s)
        if "Connected!" in out:
            return True
        return False

    def run_local(self, cmd):
        sp = subprocess.run(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return sp.stdout.decode('utf-8'), sp.stderr.decode('utf-8')

    def run(self, command):
        if not self.connected:
            self.connect()
        stdin, stdout, stderr = self.ssh.exec_command(command)
        stdout = stdout.read().decode('utf-8')
        stderr = stderr.read().decode('utf-8')
        return stdout, stderr

    def to_file(self, text, path):
        self.run(f"echo -e '{text}' > {path}")

    def git(self, path, action="pull"):
        max_tests = 25
        success = False
        for i in range(max_tests):
            if self.test_git():
                success = True
                break
            print(f"{self} | Waiting for git... ({i+1}/{max_tests})")

        if not success:
            # raise warning
            print(f"{self} | Failed to git {action} {path}")

        if action in ['push', 'pull']:
            return self.run(f"cd {path} && git {action} && cd")

    def test_git(self):
        s = "timeout 5 ssh -T git@github.com"
        out, err = self.run(s)
        if "You've successfully authenticated" in err:
            return True
        return False

    def load(self, d):
        # Merge d into self
        for k, v in d.items():
            self.__dict__[k] = v

    def get_config(self, name):
        if self.configs is None:
            return None
        d = self.configs["default"]
        if name in self.configs:
            c = self.configs[name]
            # merge c into d
            for k, v in c.items():
                d[k] = v

            d["cpus"] = c["cpus"] if isinstance(
                c["cpus"], int) else c["cpus"][self.alias]

            d["partition"] = c["partition"][self.alias] if self.alias in c["partition"] else None
        return d


class SlurmServer(Server):
    def __init__(self, host, user, alias=None, configs=None):
        super().__init__(host, user, alias, configs)

    def __repr__(self):
        return f"Slurm Server {self.alias} ({self.user}@{self.host})"

    def srun(self, path):
        cmd = 'sbatch --export=ALL '
        cmd += f"--error={self.save_path}/slurm.%j.err "
        cmd += f"--output={self.save_path}/slurm.%j.out "
        cmd += path
        return self.run(cmd)


class LinuxServer(Server):
    def __init__(self, host, user, alias=None, configs=None):
        super().__init__(host, user, alias, configs)

    def __repr__(self):
        return f"Linux Server {self.alias} ({self.user}@{self.host})"

    def tmux(self, cmd, name):
        s = f"tmux new -d -s {name} '{cmd}'"
        print(s)
        return self.run(s)


class LocalHost(LinuxServer):
    def __init__(self, host, user, alias=None, configs=None):
        super().__init__(host, user, alias, configs)

    def __repr__(self):
        return f"Localhost ({self.user}@{self.host})"

    def run(self, command):
        return self.run_local(command)

    def connect(self):
        self.connected = True


def make_slurm(task, server, args="", save="custom.slurm"):
    config = server.get_config(task["config"])

    nodes = math.ceil(config["cpus"] / server.cpus_per_node)
    cpus = nodes * server.cpus_per_node if nodes > 1 else config["cpus"]

    sbatch = f"""#!/bin/bash                                                                                                                                                                                                        
                                                                                                                                                                                                                
#SBATCH -J {task["job_name"]}

#SBATCH -N {nodes}
#SBATCH -n {cpus}

#SBATCH --ntasks-per-node={server.cpus_per_node}
#SBATCH --ntasks-per-core=1
#SBATCH --threads-per-core=1
#SBATCH --time={config["time"]}
"""
    if config["partition"] is not None:
        sbatch += f"#SBATCH --partition={config['partition']}\n"

    # email
    if config["mail"]:
        sbatch += f"\n#SBATCH --mail-user={config['mail-user']}"
        sbatch += "\n#SBATCH --mail-type=ALL"

    if config["gpu"] and config["gpu"] > 0:
        assert server.gpu, f"GPU requested but no GPU available on {server.alias}"
        sbatch += f"\n#SBATCH --gres=gpu:{config['gpu']}"

    # Initialize modules

    sbatch += f"""\n
{server.init if server.init else ""}

{"wandb enabled" if server.wandb else ""}
{("wandb "+ server.wandb) if server.wandb else ""}

echo CMD {task["cmd"]} {args}

"""

    if "seeds" in task:
        sbatch += f"""for seed in {task["seeds"]}
do 
{task["cmd"]} {args}
done"""
    else:
        sbatch += f"""{task["cmd"]} {args}"""

    if save != False:
        with open(save, "w") as f:
            f.write(sbatch)
    return sbatch


class Compute:
    def __init__(self, config_file=None):
        self.servers = {}
        if config_file is not None:
            self.get_config(config_file)

    def local_run(self, cmd):
        sp = subprocess.run(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return sp.stdout.decode('utf-8'), sp.stderr.decode('utf-8')

    def get_config(self, config_path, hosts_path):
        config = read(config_path)
        hosts = read(hosts_path)
        self.servers = {}
        for h, d in hosts.items():
            if d["host"] == "localhost":
                self.servers[h] = LocalHost(d["host"], d["user"], h,
                                            configs=config)
            elif d["platform"] == "slurm":
                self.servers[h] = SlurmServer(
                    d["host"], d["user"], h, configs=config)
            elif d["platform"] == "linux":
                self.servers[h] = LinuxServer(
                    d["host"], d["user"], h, configs=config)
            else:
                self.servers[h] = Server(
                    d["host"], d["user"], h, configs=config)
            self.servers[h].load(d)
        # print("Servers:")
        # for k, v in self.servers.items():
        #     print(v)
        return self

    def get_args(self, task):
        args_list = task["args"] if "args" in task else [""]

        if "sweep" in task:
            for arg, values in task["sweep"].items():
                new_configs = []
                for v in values:
                    for c in args_list:
                        n = f"{c} {arg}={v}"
                        new_configs.append(n)
                args_list = new_configs

        return args_list

    def run(self, task, server):
        for t in task:
            print(f"> {t}")
            out, err = server.run(t)
            print(out, err)

    def slurm_run(self, task, server):
        args_list = self.get_args(task)

        for args in args_list:
            s = make_slurm(task, server, args)
            server.to_file(text=s, path="Compute/custom.slurm")
            o, e = server.srun("Compute/custom.slurm")
            if e != "":
                print(e)
            job_id = o.replace("Submitted batch job ", "").replace("\n", "")
            recap = f"{server.alias} , {job_id} , {args} \n"
            with open("jobs.csv", "a") as f:
                f.write(recap)

            with open(f"archive/{server.alias}/{server.alias}_{job_id}.slurm", "w") as f:
                f.write(s)

    def tmux_run(self, task, server):
        cd = f"cd {task['cd']} && " if "cd" in task else ""

        args_list = self.get_args(task)

        if "parallel" in task and task["parallel"]:
            cmd = task["cmd"]
            for i in range(len(args_list)):
                args = args_list[i]
                s = f"{cd} {cmd} {args}"
                name = f"{task['job_name']}_{i}"
                server.tmux(s, name)

        else:
            cmds = [f"{task['cmd']} {args}" for args in args_list]
            s = cd + " && ".join(cmds)
            print(s)
            server.tmux(s, task["job_name"])

    def pip(self, task, server):
        cmd = f"{server.init}\n python3 -m pip install -y " + \
            " ".join(task)
        print(cmd)
        server.run(cmd)

    def clone(self, task, server):
        repos = task["repos"]
        for repo in repos:
            cmd = f"git clone {repo}"
            print(cmd)
            server.run(cmd)
            if task["install"]:
                repo_name = repo.split("/")[-1].replace(".git", "")
                cmd = f"{server.init}\n cd {repo_name}\n python3 -m pip install -y -e . \ncd"
                print(cmd)
                server.run(cmd)

    def copy(self, task, server):  # sourcery skip: raise-specific-error
        source = task["src"]
        dest = task["dest"]
        if task["mode"] == "pull":  # Get files from server
            source = f'{server.user}@{server.host}:{source}'
            # Make directory if it doesn't exist
            if not os.path.exists(dest):
                os.makedirs(dest)
        elif task["mode"] == "push":  # Put files on server
            # Make directory if it doesn't exist
            cmd = f"mkdir -p {dest}"
            dest = f'{server.user}@{server.host}:{dest}'
            server.run(cmd)
        else:
            raise Exception("Unknown mode")
        cmd = f'scp -r {source} {dest}'
        print(cmd)
        self.local_run(cmd)

    def sync(self, task, server):
        cmd = server.init + "\n" or ''
        # get save_path
        save_path = server.save_path
        # get jobs
        jobs = task["jobs"] if 'jobs' in task else[]
        if "job_array" in task:
            job_array = task["job_array"]
            jobs += list(range(job_array[0], job_array[1]+1))
        print(jobs)

        sync_cmd = []
        for job in jobs:
            s = f"{cmd} cat {save_path}/slurm.{job}.err | grep 'wandb sync'"
            out, err = server.run(s)
            l = out.split("\n")[:-1]
            for i in l:
                i = i.replace("wandb:", "")
                sync_cmd.append(i)
            # sync_cmd.append(f"echo '{job}: {len(l)-1} synced'")
        cmd = cmd + " \n".join(sync_cmd)
        # print(cmd)
        server.run(cmd)

    def parse_playbook(self, path):
        playbook = read(path)
        inventory = playbook["inventory"]
        self.get_config(inventory["configs"], inventory["hosts"])

        for task in playbook["tasks"]:
            if "playbook" in task:
                self.parse_playbook(task["playbook"])

            servers = [servers] if isinstance(
                task["hosts"], Server) else task["hosts"]
            for server_name in servers:
                if "name" in task:
                    print(f" >> {server_name} | {task['name']} << ")

                if "cd" in task:
                    server.run(f"cd {task['cd']}")

                server = self.servers[server_name]
                if "run" in task:
                    self.run(task["run"], server)

                mapping = {
                    "pip": self.pip,
                    "copy": self.copy,
                    "sync": self.sync,
                    "tmux": self.tmux_run,
                    "srun": self.slurm_run,
                    "cmd": self.run,
                    "clone": self.clone,
                }

                for k, v in mapping.items():
                    if k in task:
                        v(task[k], server)

                if "git" in task:
                    action = task["git"]["action"] if "action" in task["git"] else "pull"
                    server.git(task["git"]["path"], action)


if __name__ == "__main__":
    path = sys.argv[1]
    comp = Compute()
    comp.parse_playbook(path)
