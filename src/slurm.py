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
