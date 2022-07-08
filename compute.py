import subprocess
import sys

from src import *

from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


def read(filename):
    with open(filename, 'r') as f:
        return load(f, Loader=Loader)


def replace(x, vars):
    if isinstance(x, str):
        for var_name, var_val in vars.items():
            if isinstance(var_val, str):
                x = x.replace(var_name, var_val)
            elif x == var_name:
                x = var_val

    elif isinstance(x, dict):
        for k, v in x.items():
            x[k] = replace(v, vars)

    elif isinstance(x, list):
        x = [replace(v, vars) for v in x]

    return x


class Compute:
    def __init__(self, config_file=None):
        self.servers = {}
        if config_file is not None:
            self.get_config(config_file)
        self.tasks = []

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

    def parse_playbook(self, path):
        playbook = read(path)
        if "variables" in playbook:
            playbook = replace(playbook, vars=playbook["variables"])
        inventory = playbook["inventory"]
        self.get_config(inventory["configs"], inventory["hosts"])

        for task in playbook["tasks"]:
            name = task["name"]
            servers = [self.servers[server_name]
                       for server_name in task["hosts"]]

            for k, v in task.items():
                if k in ["name", "hosts"]:
                    continue
                if k in TASKS:
                    t = TASKS[k](name, v, servers)
                    # print(t)
                    self.tasks.append(t)

    def run(self):
        for t in self.tasks:
            t.run()


if __name__ == "__main__":
    path = sys.argv[1]
    comp = Compute()
    comp.parse_playbook(path)
    print(comp.tasks)
    comp.run()
