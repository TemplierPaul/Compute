#!/bin/bash                                                                                                                                                                                                        
                                                                                                                                                                                                                
#SBATCH -J BERL

#SBATCH -N 11
#SBATCH -n 396

#SBATCH --ntasks-per-node=36
#SBATCH --ntasks-per-core=1
#SBATCH --threads-per-core=1
#SBATCH --time=1-00:00:00

#SBATCH --mail-user=paul.templier@isae-supaero.fr
#SBATCH --mail-type=ALL

export OMP_NUM_THREADS=1
module purge
module load intel/18.2
module load intelmpi/18.2
module load python/3.6.8
source activate /tmpdir/templier/envs/torchenv
echo $(which python)
cd


wandb enabled
wandb offline

echo CMD srun python BERL/run.py --wandb=sureli/BERL_paper --seed=$seed --job=$SLURM_JOB_ID --save_freq=50 --preset calmip atari openai --tag=weight_decay --pop_per_cpu=1 --net=canonical --env=Pong-v0 --es_wd=0.001 --es_sigma=0.02 --es_lr=0.01 --es_momentum=0.9

for seed in 0 1
do 
srun python BERL/run.py --wandb=sureli/BERL_paper --seed=$seed --job=$SLURM_JOB_ID --save_freq=50 --preset calmip atari openai --tag=weight_decay --pop_per_cpu=1 --net=canonical --env=Pong-v0 --es_wd=0.001 --es_sigma=0.02 --es_lr=0.01 --es_momentum=0.9
done