#!/bin/bash
#SBATCH -J Hetero
#SBATCH --mail-user=paul.templier@isae-supaero.fr
#SBATCH --mail-type=ALL


# CPU as worker nodes
#SBATCH --cpus-per-task=24 --ntasks=2 --nodes=2 --ntasks-per-node=1 --partition=gpucpu
#SBATCH hetjob
# GPU as main node
#SBATCH --cpus-per-task=6 --ntasks=1 --gres=gpu:1 --nodes=1 --ntasks-per-node=1 --partition=gpucpu

#SBATCH --time=1-00:00:00


module purge
module load python/3.7
module load libosmesa/17.2.3
module load cuda/11.6
cd /home/disc/p.templier/parallelpy
source pyenv/bin/activate
echo $(which python)
cd


wandb enabled
wandb online


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



echo CMD python3 Rayvolution/simple.py --job=$SLURM_JOB_ID --net=min --episode_frames=100000 --max_frames=5000000 --max_evals=10000000 --pop=96 --mu=48  --max_evals=10000000 --save_freq=10 --noise_type=none --buffer_size=3000000 --job=$SLURM_JOB_ID --cuda --env=min-space_invaders --rl=munchausen --rl_steps=1000 --rl_lr=0.001 --rl_batch_size=4096 --sgd_update --backprop_steps=1000 --actor_injection=0 --sigma=1 --es_seed=42 --optim=sepcma --seeding=random --wandb=sureli/rayvolution --tag=minatar

for seed in 0
do 
python3 Rayvolution/simple.py --job=$SLURM_JOB_ID --net=min --episode_frames=100000 --max_frames=5000000 --max_evals=10000000 --pop=96 --mu=48  --max_evals=10000000 --save_freq=10 --noise_type=none --buffer_size=3000000 --job=$SLURM_JOB_ID --cuda --env=min-space_invaders --rl=munchausen --rl_steps=1000 --rl_lr=0.001 --rl_batch_size=4096 --sgd_update --backprop_steps=1000 --actor_injection=0 --sigma=1 --es_seed=42 --optim=sepcma --seeding=random --wandb=sureli/rayvolution --tag=minatar
done
echo  "JOB FINISHED"
sleep 5
ray stop --force
echo "RAY STOPPED"
