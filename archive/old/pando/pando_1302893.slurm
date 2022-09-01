#!/bin/bash                                                                                                                                                                                                        
                                                                                                                                                                                                                
#SBATCH -J BERL

#SBATCH -N 8
#SBATCH -n 192

#SBATCH --ntasks-per-node=24
#SBATCH --ntasks-per-core=1
#SBATCH --threads-per-core=1
#SBATCH --time=1-00:00:00
#SBATCH --partition=medium

#SBATCH --mail-user=paul.templier@isae-supaero.fr
#SBATCH --mail-type=ALL

export OMP_NUM_THREADS=1
module purge
module load python/3.7
module load gcc/8.2.0 
module load openmpi/4.0.0-gcc8.2
module load mpi4py/3.0.1-openmpi4.0.0-gcc8.2-python3.7
module load libosmesa/17.2.3
cd /home/disc/p.templier/parallelpy
source pyenv/bin/activate
echo $(which python)
cd


wandb enabled
wandb online

echo CMD srun python BERL/run.py --wandb=sureli/ERL_paper --seed=$seed --job=$SLURM_JOB_ID --save_freq=50 --pop_per_cpu=2 --max_frames=500000000 --env=bossfight --preset pando procgen openai --tag=procgen --n_evaluations=5

for seed in 0
do 
srun python BERL/run.py --wandb=sureli/ERL_paper --seed=$seed --job=$SLURM_JOB_ID --save_freq=50 --pop_per_cpu=2 --max_frames=500000000 --env=bossfight --preset pando procgen openai --tag=procgen --n_evaluations=5
done