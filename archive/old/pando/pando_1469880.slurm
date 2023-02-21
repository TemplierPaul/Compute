#!/bin/bash                                                                                                                                                                                                        
                                                                                                                                                                                                                
#SBATCH -J Minatar

#SBATCH -N 1
#SBATCH -n 6

#SBATCH --ntasks-per-core=1
#SBATCH --threads-per-core=1
#SBATCH --time=1-00:00:00

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


wandb enabled
wandb online

echo CMD python3 Rayvolution/simple_rl.py --job=$SLURM_JOB_ID --net=min --episode_frames=27000 --max_frames=10000000 --max_evals=10000000 --save_freq=10 --noise_type=none --job=$SLURM_JOB_ID --env=min-seaquest --rl=munchausen --replay_start_size=4096 --rl_lr=0.05 --epsilon_min=0.2 --epsilon_decay=0.999 --rl_batch_size=4096 --buffer_size=1000000 --seeding=random --wandb=sureli/rayvolution --tag=param_search

for seed in 0
do 
python3 Rayvolution/simple_rl.py --job=$SLURM_JOB_ID --net=min --episode_frames=27000 --max_frames=10000000 --max_evals=10000000 --save_freq=10 --noise_type=none --job=$SLURM_JOB_ID --env=min-seaquest --rl=munchausen --replay_start_size=4096 --rl_lr=0.05 --epsilon_min=0.2 --epsilon_decay=0.999 --rl_batch_size=4096 --buffer_size=1000000 --seeding=random --wandb=sureli/rayvolution --tag=param_search
done