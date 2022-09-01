#!/bin/bash                                                                                                                                                                                                        
                                                                                                                                                                                                                
#SBATCH -J BERL

#SBATCH -N 2
#SBATCH -n 48

#SBATCH --ntasks-per-node=24
#SBATCH --ntasks-per-core=1
#SBATCH --threads-per-core=1
#SBATCH --time=1-00:00:00

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

echo CMD srun python BERL/run.py $cmd --wandb=sureli/BERL_paper --seed=0 --job=$SLURM_JOB_ID --save_freq=50 --preset pando mujoco openai --tag=new_openai_02 --es_sigma=0.02 --pop_per_cpu=2 --net=mujoco-light --env=InvertedDoublePendulum-v2

for seed in 0 1 2 3 4 5
do 
srun python BERL/run.py $cmd --wandb=sureli/BERL_paper --seed=0 --job=$SLURM_JOB_ID --save_freq=50 --preset pando mujoco openai --tag=new_openai_02 --es_sigma=0.02 --pop_per_cpu=2 --net=mujoco-light --env=InvertedDoublePendulum-v2
done