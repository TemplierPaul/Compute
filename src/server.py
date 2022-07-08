import paramiko
import subprocess


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
