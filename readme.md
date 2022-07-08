# Compute platform

This tool is freely inspired from the concepts used in [Ansible](https://docs.ansible.com/ansible/latest/index.html) and coded in python3 using the `paramiko` library for SSH commands.

It relies on 3 types of `yaml` files:
- hosts files, describing the hosts to connect to
- configuration files, describing the configuration for each job type hosts
- playbooks, describing a list of tasks to run on specific hosts

## Hosts
Hosts are remote servers to SSH to connect to to run tasks.
Each host should be accessible through SSH without a passphrase. 

```yaml
raspi:
  user: username
  host: 192.168.123.1
  cpus_per_node: 8
  platform: linux
  gpu: False
```

To account for slurm clusters complexity, you can add a path to save logs to, and the `init` field allows to load modules and activate python environments. 

```yaml
calmip:
  user: username
  host: olympe.calmip.univ-toulouse.fr
  cpus_per_node: 36
  platform: slurm
  wandb: offline
  gpu: True
  save_path: "/tmpdir/username/slurm_logs"
  init: |
    export OMP_NUM_THREADS=1
    module purge
    module load intel/18.2
    module load intelmpi/18.2
    module load python/3.6.8
    source activate /tmpdir/username/envs/torchenv
    cd

```

### Localhost
Localhost can be defined as a host to run tasks locally, commands will then be run directly in local CLI without ssh.

## Configs
Each configuration can describe how many CPUs to allocate for the job depending on the platform, how long the job can be, what partition to use and if a GPU is required. 
If these parameters are not specified, they will be set to the default values.

## Variables
Variables can be set in a playbook, and the string used as key will be replaced by the value everywhere at run time. This allows to easily run a whole playbook on a specific set of hosts, without changing each task, or to reuse a parameter in multiple tasks.

```yaml
variables:
  "£hosts": 
    - localhost
    - cluster

tasks:
  - name: "Run echo hostname"
    hosts: "£hosts"
    cmd: 
      - "echo hello $HOSTNAME"
```

## Playbooks
A playbook is a set of tasks to run on specific hosts.
It starts with an `inventory` field to specify the paths of hosts and configuration files. Then all tasks are run sequentially as described.

### `cmd`
A `cmd` task simply runs the commands on the remote server through ssh. 
```yaml
  - name: "Run echo hostname"
    hosts: 
      - cluster
    cmd: 
      - "echo hello $HOSTNAME"
      - "pwd"
```

### `pip`
The `pip` field is a list of packages to install on the hosts with pip. 
```yaml
  - name: "Test pip"
    hosts: 
      - localhost
    pip:
      action: install
      packages:
        - numpy
        - pandas
```

### `git`
The `git` field allows to push or pull from a directory on the remote host.
Its `action` subfield can be set to "push" or "pull", default is "pull".
If github is not accessible, the code will hang and try 25 times to connect to github with a 5s delay. This was implemented to bypass some proxy settings that were annoying the author and about which the IT service never answered, forcing a more robust solution.

```yaml
  - name: "Git pull"
    hosts: 
      - localhost
    git:
      action: pull
      path: "~/Documents/Doctorat/Dev/BERL"
```
It can also be used to clone a repository.
```yaml
  - name: "Git clone"
    hosts: 
      - localhost
    git:
      action: clone
      path: "~/Documents/Doctorat/Dev/test_compute"
      repo: git@github.com:TemplierPaul/BERL.git
      install: False
```

### `slurm`
The `slurm` field allows to run a job on a specific partition on the remote host with slurm, and to do hyperparameter sweeps easily.

It can take the following parameters:
- cmd: the command to run on the remote host
- config: the configuration file to use
- seeds: the list of seeds to use, each job will run one experiment per seed sequentially
- sweep: dictionary {parameter: list of values} to sweep over
- args: list of arguments to pass to the command, one job will be started for each argument in the list
- scatter: if True, scatters the configurations to run between the hosts, else runs all configs on each host. 

All slurm files generated are saved to the local `archive` directory and named after their slurm job ID, and commands are also saved in the `job.csv` file for archiving. 

```yaml
  - name: "Test slurm"
    hosts: 
      - cluster
    slurm:
      job_name: "Testing"
      scatter: True
      parallel: True
      cmd: "python myscript.py"
      config: test
      seeds: 0, 1, 2, 3
      sweep:
        "--preset": ["canonical", "openai"]
        "--n_evaluations": [1, 5, 8]
      args:
        - "run_1"
        - "run_2"
        - "run_3"
```

### `tmux`
The `tmux` field allows to run a job on a host that does not use Slurm by using tmux. It can be used to run multiple jobs in parallel by setting the `parallel` field to True, else it will run one job at a time. 
Similarly to `srun`, it can take multiple args. 
The `cd` field can be used to start a tmux instance from a specific directory.

```yaml
  - name: "Test tmux"
    hosts: 
      - cluster
    tmux:
      job_name: "Testing"
      scatter: True
      parallel: True
      cd: "~/path/to/cd"
      cmd: "python myscript.py"
      seeds: 0
      args:
        - "run_1"
        - "run_2"
        - "run_3"
```

### `copy`
The `copy` field allows to copy a file or directory between the remote host and localhost with scp. 
To copy from localhost to remote host, the `mode` field should be set to "push", else set it to "pull" to get the file from remote host. 
```yaml
  - name: "Push file to a remote machine"
    hosts:
      - cluster
    copy:
      mode: "push"
      src: "/path/to/local/file/filename.txt" # File
      dest: "/path/to/save/to/on/cluster" # Directory
```

```yaml
  - name: "Copy a file from a remote machine"
    hosts:
      - cluster
    copy:
      mode: "pull"
      src: "/path/to/remote/file/filename.txt" # File
      dest: "/path/to/save/to/locally" # Directory
```

# Setup
To set up this tool for you:
- Clone the repository: `git clone
- Install the needed libraries (namely `paramiko`) with pip
- Setup a `hosts.yaml` file with the hosts you want to connect to 
- Make sure all hosts are accessible through SSH without a passphrase  
- Setup a `configs.yaml` file with the configurations you can use
- Create your playbooks in the `playbooks` directory

## Running playbooks
To start a playbook, just run: 
```
python3 compute.py playbooks/<playbook-name>.yaml
```

### Global command
To make the command global and simply type `run playbook` from anywhere, add this to your `.bashrc`:
```bash
run () {
    cd <path-to-Compute>
    python compute.py playbooks/$1.yaml
    cd -
}
```

# Contributing
To add features, you can create new classes in python:
```python
@register("cmd")
class CMD(Task):
    def __init__(self, name, cfg, servers):
        super().__init__(name, cfg, servers)

    def run(self):
        # Code to run the parsed task
        cmd = self.cfg
        if isinstance(cmd, str):
            cmd = [cmd]
        for server in self.servers:
            for c in cmd:
                print(f"> {c}")
                out, err = server.run(c)
                print(out, err)
```