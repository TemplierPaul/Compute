# Compute platform

This tool is freely inspired from the concepts used in [Ansible](https://docs.ansible.com/ansible/latest/index.html) and coded in python3 using the `paramiko` library for SSH commands.

It relies on 3 types of `yaml` files:
- hosts files, describing the hosts to connect to
- configuration files, describing the configuration for each job type hosts
- playbooks, describing a list of tasks to run on specific hosts

## Hosts
Hosts are remote servers to SSH to connect to to run tasks.
Each host should be accessible through SSH without a passphrase. 

### Localhost
Localhost can be defined as a host to run tasks locally, commands will then be run directly in local CLI without ssh.

## Configs
Each configuration can describe how many CPUs to allocate for the job depending on the platform, how long the job can be, what partition to use and if a GPU is required. 
If these parameters are not specified, they will be set to the default values.

## Playbooks
A playbook is a set of tasks to run on specific hosts.
It starts with an `inventory` field to specify the paths of hosts and configuration files. Then all tasks are run sequentially as described.

### pip
The `pip` field is a list of packages to install on the hosts with pip. 

### git
The `git` field allows to push or pull from a directory on the remote host.
Its `action` subfield can be set to "push" or "pull", default is "pull".
If github is not accessible, the code will hand and try 25 times to connect to github with a 5s delay. This was implemented to bypass some proxy settings that were annoying the author and about which the IT service never answered, forcing a more robust solution.

### srun
The `srun` field allows to run a job on a specific partition on the remote host with slurm, and to do hyperparameter sweeps easily.

It can take the following parameters:
- cmd: the command to run on the remote host
- config: the configuration file to use
- seeds: the list of seeds to use, each job will run one experiment per seed sequentially
- sweep: dictionary {parameter: list of values} to sweep over
- args: list of arguments to pass to the command, one job will be started for each argument in the list

All slurm files generated are saved to the local `archive` directory and named after their slurm job ID, and commands are also saved in the `job.csv` file for archiving. 

### tmux
The `tmux` field allows to run a job on a host that does not use Slurm by using tmux. It can be used to run multiple jobs in parallel by setting the `parallel` field to True, else it will run one job at a time. 
Similarly to `srun`, it can take multiple args. 
The `cd` field can be used to start a tmux instance from a specific directory.


### copy
The `copy` field allows to copy a file or directory between the remote host and localhost with scp. 
To copy from localhost to remote host, the `mode` field should be set to "push", else set it to "pull" to get the file from remote host. 

## Setup
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
python3 compute.py playbooks/<playbook_name>.yaml
```

