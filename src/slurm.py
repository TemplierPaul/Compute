import math


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


def make_ray_slurm(task, server, args="", save="custom.slurm"):
    config = server.get_config(task["config"])

    nodes = math.ceil(config["cpus"] / server.cpus_per_node)
    cpus = nodes * server.cpus_per_node if nodes > 1 else config["cpus"]

    sbatch = f"""#!/bin/bash         
#SBATCH -J {task["job_name"]}

#SBATCH --nodes={nodes}
#SBATCH --ntasks={nodes}

#SBATCH --ntasks-per-node=1

#SBATCH --cpus-per-task={server.cpus_per_node}

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

    if save != False:
        with open(save, "w") as f:
            f.write(sbatch)
    return sbatch
