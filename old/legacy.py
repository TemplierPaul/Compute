
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
                        if isinstance(v, str) and " " in v:
                            n = f"{c} {arg} {v}"
                        else:
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
        self._slurm_run(task, args_list, server)

    def slurm_scatter(self, task, servers):
        args_list = self.get_args(task)

        n = len(servers)
        b = [[] for _ in range(n)]
        i = 0
        for k in args_list:
            b[i].append(k)
            i = (i+1) % n

        for i in range(n):
            if len(b[i]) > 0:
                self._slurm_run(task, b[i], servers[i])

    def _slurm_run(self, task, args_list, server):
        for args in args_list:
            print(f"Running {args} on {server.alias}")
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
        args_list = self.get_args(task)
        self._tmux_run(task, args_list, server)

    def tmux_scatter(self, task, servers):
        args_list = self.get_args(task)

        n = len(servers)
        b = [[] for _ in range(n)]
        i = 0
        for k in args_list:
            b[i].append(k)
            i = (i+1) % n

        for i in range(n):
            if len(b[i]) > 0:
                self._tmux_run(task, b[i], servers[i])

    def _tmux_run(self, task, args_list, server):
        for args in args_list:
            print(f"Running {args} on {server.alias}")

        cd = f"cd {task['cd']} && " if "cd" in task else ""

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
        for t in task:
            cmd = f"{server.init}\n python3 -m pip install --user {t}"
            print(f"> {t}")
            o, e = server.run(cmd)
            e = e.lower()
            if "error" in e or "warning" in e:
                print(e)

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
        if "variables" in playbook:
            playbook = replace(playbook, vars=playbook["variables"])
        inventory = playbook["inventory"]
        self.get_config(inventory["configs"], inventory["hosts"])

        for task in playbook["tasks"]:
            if "playbook" in task:
                self.parse_playbook(task["playbook"])

            servers = [servers] if isinstance(
                task["hosts"], Server) else task["hosts"]

            # SCATTER
            if "scatter" in task and task["scatter"]:
                if "name" in task:
                    print(
                        f" >> {task['name']} | SCATTER on {', '.join(servers)} << ")

                server_list = [self.servers[server_name]
                               for server_name in servers]

                mapping = {
                    "tmux": self.tmux_scatter,
                    "srun": self.slurm_scatter,
                }

                for k, v in mapping.items():
                    if k in task:
                        v(task[k], server_list)

            # NO SCATTER
            else:
                for server_name in servers:
                    if "name" in task:
                        print(f" >> {server_name} | {task['name']} << ")

                    # if "cd" in task:
                    #     server.run(f"cd {task['cd']}")

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
