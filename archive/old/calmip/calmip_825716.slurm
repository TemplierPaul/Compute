#!/bin/bash                                                                                                                                                                                                        
                                                                                                                                                                                                                
#SBATCH -J BERL

#SBATCH -N 5
#SBATCH -n 180

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
cd


wandb enabled
wandb offline

echo CMD srun python BERL/run.py --wandb=sureli/ERL_paper --seed=$seed --job=$SLURM_JOB_ID --save_freq=50 --pop_per_cpu=2 --max_frames=500000000 --env=leaper --preset calmip procgen openai --tag=procgen --n_evaluations=1

for seed in 0
do 
srun python BERL/run.py --wandb=sureli/ERL_paper --seed=$seed --job=$SLURM_JOB_ID --save_freq=50 --pop_per_cpu=2 --max_frames=500000000 --env=leaper --preset calmip procgen openai --tag=procgen --n_evaluations=1
done