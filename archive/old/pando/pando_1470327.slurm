#!/bin/bash                                                                                                                                                                                                        
                                                                                                                                                                                                                
#SBATCH -J Gym

#SBATCH -N 1
#SBATCH -n 6

#SBATCH --ntasks-per-core=1
#SBATCH --threads-per-core=1
#SBATCH --time=1-00:00:00
#SBATCH --partition=gpu

#SBATCH --mail-user=paul.templier@isae-supaero.fr
#SBATCH --mail-type=ALL
#SBATCH --gres=gpu:1

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

echo CMD python3 Rayvolution/simple_rl.py --save_freq=10 --noise_type=none --job=$SLURM_JOB_ID --env=LunarLander-v2 --max_frames=1000000 --rl=munchausen --replay_start_size=4096 --rl_lr=0.001 --epsilon_min=0.2 --epsilon_decay=0.999 --rl_batch_size=4096 --buffer_size=1000000 --seeding=random --wandb=sureli/rayvolution --tag=param_search

for seed in 0
do 
python3 Rayvolution/simple_rl.py --save_freq=10 --noise_type=none --job=$SLURM_JOB_ID --env=LunarLander-v2 --max_frames=1000000 --rl=munchausen --replay_start_size=4096 --rl_lr=0.001 --epsilon_min=0.2 --epsilon_decay=0.999 --rl_batch_size=4096 --buffer_size=1000000 --seeding=random --wandb=sureli/rayvolution --tag=param_search
done