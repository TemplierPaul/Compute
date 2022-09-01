#!/bin/bash                                                                                                                                                                                                        
                                                                                                                                                                                                                
#SBATCH -J BERL

#SBATCH -N 1
#SBATCH -n 1

#SBATCH --ntasks-per-node=24
#SBATCH --ntasks-per-core=1
#SBATCH --threads-per-core=1
#SBATCH --time=00:05:00

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

echo CMD echo --env=Pong-v0 --theta_init_bias=0 --xavier_init

echo --env=Pong-v0 --theta_init_bias=0 --xavier_init
    