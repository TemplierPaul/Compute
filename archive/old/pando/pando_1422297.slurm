#!/bin/bash                                                                                                                                                                                                        
                                                                                                                                                                                                                
#SBATCH -J Atari

#SBATCH -N 16
#SBATCH -n 384

#SBATCH --ntasks-per-node=24
#SBATCH --ntasks-per-core=1
#SBATCH --threads-per-core=1
#SBATCH --time=1-00:00:00
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

echo CMD python LUCIES/run.py --net=canonical --pop=800 --mu=50 --episode_frames=27000 --stack_frames=4 --wandb=sureli/LUCIES_dev --max_evals=5000000 --eval_budget=5 --env=Alien-v0 --optim=sepcma --game_seed=-1

for seed in 0
do 
python LUCIES/run.py --net=canonical --pop=800 --mu=50 --episode_frames=27000 --stack_frames=4 --wandb=sureli/LUCIES_dev --max_evals=5000000 --eval_budget=5 --env=Alien-v0 --optim=sepcma --game_seed=-1
done