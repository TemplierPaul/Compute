#!/bin/bash         
#SBATCH -J Atari

#SBATCH --nodes=8
#SBATCH --ntasks=8

#SBATCH --ntasks-per-node=1

#SBATCH --cpus-per-task=24

#SBATCH --time=06:00:00
#SBATCH --partition=medium

#SBATCH --mail-user=paul.templier@isae-supaero.fr
#SBATCH --mail-type=ALL

module purge
module load python/3.7
module load libosmesa/17.2.3
cd /home/disc/p.templier/parallelpy
source pyenv/bin/activate
echo $(which python)
cd


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




echo CMD python LUCIES/run.py --net=canonical --pop=800 --mu=50 --episode_frames=27000 --stack_frames=4 --wandb=sureli/LUCIES_dev --max_evals=5000000 --eval_budget=5 --env=Pong-v0 --optim=sepcma --game_seed=0

for seed in 0
do 
python LUCIES/run.py --net=canonical --pop=800 --mu=50 --episode_frames=27000 --stack_frames=4 --wandb=sureli/LUCIES_dev --max_evals=5000000 --eval_budget=5 --env=Pong-v0 --optim=sepcma --game_seed=0
done