import math


def make_slurm(task, server, args="", save="custom.slurm"):
    config = server.get_config(task["config"])

    nodes = math.ceil(config["cpus"] / server.cpus_per_node)
    cpus = nodes * server.cpus_per_node if nodes > 1 else config["cpus"]

    sbatch = f"""#!/bin/bash                                                                                                                                                                                                        
                                                                                                                                                                                                                
#SBATCH -J {task["job_name"]}

#SBATCH -N {nodes}
#SBATCH -n {cpus}

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
"""
    if server.wandb:
        save_wandb = server.save_path.replace("slurm_logs", "wandb_files")
        sbatch += f"""
export WANDB_DIR="{save_wandb}"
wandb enabled
wandb {server.wandb}
"""
    sbatch += f"""\n
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


def make_ray_slurm(task, server, args="", save="custom.slurm"):
    config = server.get_config(task["config"])

    nodes = math.ceil(config["cpus"] / server.cpus_per_node)
    # cpus = nodes * server.cpus_per_node if nodes > 1 else config["cpus"]
    cpus = server.cpus_per_node

    sbatch = f"""#!/bin/bash         
#SBATCH -J {task["job_name"]}

#SBATCH --nodes={nodes}
#SBATCH --ntasks={nodes}

#SBATCH --cpus-per-task={cpus}

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
"""
    if server.wandb:
        save_wandb = server.save_path.replace("slurm_logs", "wandb_files")
        sbatch += f"""
export WANDB_DIR="{save_wandb}"
wandb enabled
wandb {server.wandb}
"""
    # Ray with Slurm
    sbatch += """
redis_password=$(uuidgen)
export redis_password

nodes=$(scontrol show hostnames "$SLURM_JOB_NODELIST") # Getting the node names
nodes_array=($nodes)

node_1=${nodes_array[0]}
ip=$(srun --nodes=1 --ntasks=1 -w "$node_1" hostname --ip-address) # making redis-address

port=6379
ip_head=$ip:$port
export ip_head
echo "IP Head: $ip_head"

echo "STARTING HEAD at $node_1"
srun --nodes=1 --ntasks=1 -w "$node_1" \
  ray start --head --node-ip-address="$ip" --port=$port --redis-password="$redis_password" --block &
sleep 30

worker_num=$((SLURM_JOB_NUM_NODES - 1)) #number of nodes other than the head node
for ((i = 1; i <= worker_num; i++)); do
  node_i=${nodes_array[$i]}
  echo "STARTING WORKER $i at $node_i"
  srun --nodes=1 --ntasks=1 -w "$node_i" ray start --address "$ip_head" --redis-password="$redis_password" --block &
  sleep 5
done

ray status


"""

    sbatch += f"""

echo CMD {task["cmd"]} {args}

"""

    if "seeds" in task:
        sbatch += f"""for seed in {task["seeds"]}
do 
{task["cmd"]} {args}
done"""
    else:
        sbatch += f"""{task["cmd"]} {args}"""

    sbatch += """
echo  "JOB FINISHED"
sleep 5
ray stop --force
echo "RAY STOPPED"
"""

    if save != False:
        with open(save, "w") as f:
            f.write(sbatch)
    return sbatch

def make_ray_hetero_slurm(task, server, args="", save="custom.slurm"):
    config = server.get_config(task["config"])

    nodes = math.ceil(config["cpus"] / server.cpus_per_node)
    # cpus = nodes * server.cpus_per_node if nodes > 1 else config["cpus"]
    cpus = server.cpus_per_node
    gpus = config["gpu"]
    if gpus is None or gpus == 0:
        return make_ray_slurm(task, server, args, save)

    sbatch = f"""#!/bin/bash
#SBATCH -J {task["job_name"]}"""

    # email
    if config["mail"]:
        sbatch += f"\n#SBATCH --mail-user={config['mail-user']}"
        sbatch += "\n#SBATCH --mail-type=ALL"
    
    sbatch += f"""\n

# CPU as main nodes
#SBATCH --cpus-per-task={cpus} --ntasks={nodes} --nodes={nodes} --ntasks-per-node=1 --partition={config['partition']} --time={config["time"]}
#SBATCH hetjob
# GPU as worker node
#SBATCH --cpus-per-task=6 --ntasks=1 --gres=gpu:{gpus} --nodes=1 --ntasks-per-node=1 --partition=gpucpu --time={config["time"]}
"""

    # Initialize modules

    if server.wandb:
        save_wandb = server.save_path.replace("slurm_logs", "wandb_files")
        sbatch += f"""
export WANDB_DIR="{save_wandb}"
wandb enabled
wandb {server.wandb}
"""

    # Ray with Slurm
    sbatch += """

echo "Head group - $SLURM_JOB_NODELIST_HET_GROUP_0"
echo "Worker group - $SLURM_JOB_NODELIST_HET_GROUP_1"

redis_password=$(uuidgen)
export redis_password

gpu_nodes=$(scontrol show hostnames "$SLURM_JOB_NODELIST_HET_GROUP_1") # Getting the node names
gpu_nodes_array=($gpu_nodes)
echo "GPU nodes: $gpu_nodes"

cpu_nodes=$(scontrol show hostnames "$SLURM_JOB_NODELIST_HET_GROUP_0") # Getting the node names
cpu_nodes_array=($cpu_nodes)
echo "CPU nodes: $cpu_nodes"

node_1=${cpu_nodes_array[0]} # getting the first cpu node
echo "Head node: $node_1"
ip=$(srun --nodes=1 --ntasks=1 -w "$node_1" hostname --ip-address) # making redis-address

port=6379
ip_head=$ip:$port
export ip_head
echo "IP Head: $ip_head"

echo "STARTING HEAD at $node_1"
srun --het-group=0 --nodes=1 --ntasks=1 -w "$node_1"   ray start --head --node-ip-address="$ip" --port=$port --redis-password="$redis_password" --block &
sleep 15

# cpu_num as the length of the cpu_nodes_array
cpu_num=${#cpu_nodes_array[@]}

echo "CPU workers: $cpu_num"
for ((i = 1; i < cpu_num; i++)); do
  node_i=${cpu_nodes_array[$i]}
  echo "STARTING CPU WORKER $i at $node_i"
  srun --het-group=0 --nodes=1 --ntasks=1 -w "$node_i" ray start --address "$ip_head" --redis-password="$redis_password" --block &
  sleep 5
done

echo "GPU worker"
node_i=${gpu_nodes_array[0]}
echo "STARTING GPU WORKER at $node_i"
srun --het-group=1 --nodes=1 --ntasks=1 -w "$node_i" ray start --address "$ip_head" --redis-password="$redis_password" --block &
sleep 5

ray status 

"""
    sbatch += f"""

echo CMD {task["cmd"]} {args}

"""

    if "seeds" in task:
        sbatch += f"""for seed in {task["seeds"]}
do 
{task["cmd"]} {args}
done"""
    else:
        sbatch += f"""{task["cmd"]} {args}"""

    sbatch += """
echo  "JOB FINISHED"
sleep 5
ray stop --force
echo "RAY STOPPED"
"""

    if save != False:
        with open(save, "w") as f:
            f.write(sbatch)
    return sbatch