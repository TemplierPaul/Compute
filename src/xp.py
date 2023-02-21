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

    def get_args(self, task):  # sourcery skip: assign-if-exp
        self.args_list = task["args"] if "args" in task else [""]

        if "sweep" in task:
            for arg, values in task["sweep"].items():
                new_configs = []
                if "--" not in arg:
                    arg = f"--{arg}"
                for v in values: # Loop on the values to sweep over
                    for c in self.args_list: # Loop on he previous configs
                        if isinstance(v, str) and " " in v: # If the value is a string with spaces
                            n = f"{c} {arg} {v}"  
                        elif isinstance(v, bool):
                            n = f"{c} {arg}" if v else c
                        else:
                            n = f"{c} {arg}={v}"
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
            print(f"\n\n--- {len(args)} JOBS ON {server} ---")
            for a in args:
                print(f"Running on {server.alias}: {self.cfg['cmd']} {a}")
                if "ray" in self.cfg and self.cfg["ray"]:
                    if "heterogeneous" in self.cfg and self.cfg["heterogeneous"]:
                        s = make_ray_hetero_slurm(self.cfg, server, a)
                    else:
                        s = make_ray_slurm(self.cfg, server, a)
                else:
                    s = make_slurm(self.cfg, server, a)
                path = "Compute/remote.slurm"
                server.run(f"touch {path}")
                o, e = server.to_file(text=s, path=path)
                if e:
                    raise Exception(e)
                # o, e = "Submitted batch job 12345\n", ""
                o, e = server.srun(path)
                # print(o)
                if e != "":
                    print(e)
                    print(s)
                o = o.split("Submitted")[-1]
                job_id = o.replace("batch job ",
                                   "").replace("\n", "").replace(" ", "")
                print("> job_id:", job_id)
                recap = f"{server.alias} , {job_id} , {self.cfg['cmd']} {a} \n"
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
            print(f"Running {len(args)} args on {s.alias}:")
            for a in args:
                print(a)                

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
