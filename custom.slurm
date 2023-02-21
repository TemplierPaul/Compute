#!/bin/bash         
#SBATCH -J Pytest

#SBATCH --nodes=1
#SBATCH --ntasks=1

#SBATCH --cpus-per-task=24

#SBATCH --time=02:00:00
#SBATCH --partition=debug

#SBATCH --mail-user=paul.templier@isae-supaero.fr
#SBATCH --mail-type=ALL

module purge
module load python/3.7
module load libosmesa/17.2.3
module load cuda/11.6
cd /home/disc/p.templier/parallelpy
source pyenv/bin/activate
echo $(which python)
cd


export WANDB_DIR="/scratch/disc/p.templier/wandb_files"
wandb enabled
wandb online

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
srun --nodes=1 --ntasks=1 -w "$node_1"   ray start --head --node-ip-address="$ip" --port=$port --redis-password="$redis_password" --block &
sleep 30

worker_num=$((SLURM_JOB_NUM_NODES - 1)) #number of nodes other than the head node
for ((i = 1; i <= worker_num; i++)); do
  node_i=${nodes_array[$i]}
  echo "STARTING WORKER $i at $node_i"
  srun --nodes=1 --ntasks=1 -w "$node_i" ray start --address "$ip_head" --redis-password="$redis_password" --block &
  sleep 5
done

ray status




echo CMD pytest -v --disable-pytest-warnings --color=yes Rayvolution/tests 

for seed in 0
do 
pytest -v --disable-pytest-warnings --color=yes Rayvolution/tests 
done
echo  "JOB FINISHED"
sleep 5
ray stop --force
echo "RAY STOPPED"
