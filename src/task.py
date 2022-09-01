import subprocess
import sys

TASKS = {}


def register(name):
    def decorator(cls):
        TASKS[name] = cls
        return cls
    return decorator


class Task:
    def __init__(self, name, cfg, servers):
        self.name = name
        self.cfg = cfg
        self.servers = servers

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name

    def run(self):
        pass

    def local_run(self, cmd):
        sp = subprocess.run(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return sp.stdout.decode('utf-8'), sp.stderr.decode('utf-8')


class Multi:
    def __init__(self, tasks):
        self.tasks = tasks

    def run(self):
        for task in self.tasks:
            task.run()


@register("cmd")
class CMD(Task):
    def __init__(self, name, cfg, servers):
        super().__init__(name, cfg, servers)

    def run(self):
        cmd = self.cfg
        if isinstance(cmd, str):
            cmd = [cmd]
        for server in self.servers:
            for c in cmd:
                print(f"> {c}")
                out, err = server.run(c)
                print(out, err)


@register("git")
class Git(Task):
    def __init__(self, name, cfg, servers):
        super().__init__(name, cfg, servers)

    def run(self):
        action = self.cfg["action"] if "action" in self.cfg else "pull"
        path = self.cfg["path"]
        for server in self.servers:
            if action in ['push', 'pull']:
                server.git(path, action)
            elif action == "clone":
                repo = self.cfg["repo"]
                cmd = f"mkdir -p {path} && cd {path} && git clone {repo}"
                print(cmd)
                o, e = server.run(cmd)
                # print(o, e)
                if self.cfg["install"]:
                    repo_name = repo.split("/")[-1].replace(".git", "")
                    cmd = f"{server.init}\n cd {repo_name}\n python3 -m pip install -y -e . \ncd"
                    print(cmd)
                    server.run(cmd)


@register("pip")
class Pip(Task):
    def __init__(self, name, cfg, servers):
        super().__init__(name, cfg, servers)

    def run(self):
        action = self.cfg["action"] if "action" in self.cfg else "install"
        packages = self.cfg["packages"] if "packages" in self.cfg else []
        for server in self.servers:
            try:
                init = server.init + "\n"
            except AttributeError:
                init = ""
            for p in packages:
                cmd = f"{init}python3 -m pip {action} --user {p}"
                print(f"> {cmd}")
                o, e = server.run(cmd)
                e = e.lower()
                if "error" in e or "warning" in e:
                    print(e)


@register("copy")
class Copy(Task):
    def __init__(self, name, cfg, servers):
        super().__init__(name, cfg, servers)

    def run(self):
        for server in self.servers:
            source = self.cfg["src"]
            dest = self.cfg["dest"]
            if self.cfg["mode"] == "pull":  # Get files from server
                source = f'{server.user}@{server.host}:{source}'
                # Make directory if it doesn't exist
                if not os.path.exists(dest):
                    os.makedirs(dest)
            elif self.cfg["mode"] == "push":  # Put files on server
                # Make directory if it doesn't exist
                cmd = f"mkdir -p {dest}"
                dest = f'{server.user}@{server.host}:{dest}'
                server.run(cmd)
            else:
                raise Exception("Unknown mode")
            cmd = f'scp -r {source} {dest}'
            print(cmd)
            print(f"> Copy {source} ==> {dest}")
            o, e = self.local_run(cmd)
            print(o, e)
