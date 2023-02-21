#!/bin/bash         
#SBATCH -J Optim

#SBATCH --nodes=1
#SBATCH --ntasks=1

#SBATCH --ntasks-per-node=1

#SBATCH --cpus-per-task=24

#SBATCH --time=01:00:00

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




echo CMD python3 Rayvolution/simple.py --pop=48 --mu=24 --job=$SLURM_JOB_ID --es_seed=$seed --max_frames=100000 --max_evals=100000 --save_freq=0 --env=himmelblau --optim=canonical --sampling=dynamic --batch_rs=5 --eval_budget=5 --noise=500 --wandb=sureli/rayvolution --tag=noisy

for seed in 0 1 2 3 4 5 6 7 8 9
do 
python3 Rayvolution/simple.py --pop=48 --mu=24 --job=$SLURM_JOB_ID --es_seed=$seed --max_frames=100000 --max_evals=100000 --save_freq=0 --env=himmelblau --optim=canonical --sampling=dynamic --batch_rs=5 --eval_budget=5 --noise=500 --wandb=sureli/rayvolution --tag=noisy
done