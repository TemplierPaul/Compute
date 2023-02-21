#!/bin/bash

#SBATCH --nodes=3
#SBATCH --ntasks=3
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=24
#SBATCH --time=00:05:00
#SBATCH --begin=now
#SBATCH --mail-type=FAIL,END
#SBATCH --job-name=test
#SBATCH -o slurm.out # STDOUT
#SBATCH -e slurm.err # STDERR
#MODULE LOAD 
module load gcc
module load python/3.8  

redis_password=$(uuidgen)
export redis_password

nodes=$(scontrol show hostnames "$SLURM_JOB_NODELIST") # Getting the node names
nodes_array=($nodes)

node_1=${nodes_array[0]}
ip=$(srun --nodes=1 --ntasks=1 -w "$node_1" hostname --ip-address) # making redis-address

# if we detect a space character in the head node IP, we'll
# convert it to an ipv4 address. This step is optional.
# if [[ "$ip" == *" "* ]]; then
#   IFS=' ' read -ra ADDR <<< "$ip"
#   if [[ ${#ADDR[0]} -gt 16 ]]; then
#     ip=${ADDR[1]}
#   else
#     ip=${ADDR[0]}
#   fi
#   echo "IPV6 address detected. We split the IPV4 address as $ip"
# fi

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

# ===== Call your code below =====
python3 -u script.py "$SLURM_CPUS_PER_TASK"
