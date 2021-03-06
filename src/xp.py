from src.task import register
from src.task import *
from src.slurm import *


class XP(Task):
    def __init__(self, name, cfg, servers):
        super().__init__(name, cfg, servers)
        self.args_list = []
        self.get_args(cfg)
        self.xp = {}
        if "scatter" in cfg and cfg["scatter"]:
            self.scatter()
        else:
            self.no_scatter()

    def get_args(self, task):
        self.args_list = task["args"] if "args" in task else [""]

        if "sweep" in task:
            for arg, values in task["sweep"].items():
                new_configs = []
                for v in values:
                    for c in self.args_list:
                        n = f"{c} {arg} {v}" if isinstance(
                            v, str) and " " in v else f"{c} {arg}={v}"
                        new_configs.append(n)
                self.args_list = new_configs

    def scatter(self):
        self.xp = {}
        n = len(self.servers)
        b = [[] for _ in range(n)]
        i = 0
        for k in self.args_list:
            b[i].append(k)
            i = (i+1) % n
        for k in range(n):
            if len(b[k]) > 0:
                self.xp[self.servers[k]] = b[k]

    def no_scatter(self):
        for s in self.servers:
            self.xp[s] = self.args_list

    def run(self):
        pass


@register("slurm")
class Slurm(XP):
    def __init__(self, name, cfg, servers):
        super().__init__(name, cfg, servers)

    def run(self):
        for server, args in self.xp.items():
            for a in args:
                print(f"Running {a} on {server.alias}")
                s = make_slurm(self.cfg, server, a)
                server.to_file(text=s, path="Compute/custom.slurm")
                # o, e = "Submitted batch job 12345\n", ""
                o, e = server.srun("Compute/custom.slurm")
                if e != "":
                    print(e)
                job_id = o.replace("Submitted batch job ",
                                   "").replace("\n", "")
                recap = f"{server.alias} , {job_id} , {a} \n"
                with open("jobs.csv", "a") as f:
                    f.write(recap)

                with open(f"archive/{server.alias}/{server.alias}_{job_id}.slurm", "w") as f:
                    f.write(s)


@register("tmux")
class Tmux(XP):
    def __init__(self, name, cfg, servers):
        super().__init__(name, cfg, servers)

    def run(self):
        for s, args in self.xp.items():
            print(f"Running {args} on {s.alias}")

            cd = f"cd {self.cfg['cd']} && " if "cd" in self.cfg else ""

            if "parallel" in self.cfg and self.cfg["parallel"]:
                # Run all commands in parallel tmux sessions
                base_cmd = self.cfg["cmd"]
                for i in range(len(args)):
                    cmd = f"{cd} {base_cmd} {args[i]}"
                    session_name = f"{self.cfg['job_name']}_{i}"
                    s.tmux(cmd, session_name)
                    # print(s, session_name)

            else:
                # One tmux session, consecutive jobs
                cmds = [f"{self.cfg['cmd']} {a}" for a in args]
                cmd = cd + " && ".join(cmds)
                print(s, cmd)
                s.tmux(cmd, self.cfg["job_name"])
