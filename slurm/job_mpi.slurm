#!/bin/bash                                                                                                                                                                                                        
                                                                                                                                                                                                                   
#SBATCH -J MPI

# SBATCH -N 16
# SBATCH --ntasks-per-node=4

#SBATCH -n 300
#SBATCH --ntasks-per-core=1
#SBATCH --time=01:00:00

#SBATCH --partition=medium

#SBATCH --begin=now
#SBATCH --mail-user=paul.templier@isae-supaero.fr
#SBATCH --mail-type=ALL

# module load python/3.7
# conda init bash
# conda activate myenv

export OMP_NUM_THREADS=1

module purge
module load python/3.7
module load gcc/8.2.0
module load openmpi/4.0.0-gcc8.2
module load mpi4py/3.0.1-openmpi4.0.0-gcc8.2-python3.7

cd /home/disc/p.templier/parallelpy
source pyenv/bin/activate
echo $(which python)
cd

# srun
echo '
print("MPI")
import gym
' | python

echo $cmd
srun $cmd 

