#!/bin/bash                                                                                                                                                                                                        
                                                                                                                                                                                                                
#SBATCH -J BERL

#SBATCH -N 2
#SBATCH -n 48

#SBATCH --ntasks-per-node=24
#SBATCH --ntasks-per-core=1
#SBATCH --threads-per-core=1
#SBATCH --time=1-00:00:00
#SBATCH --partition=short

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

echo CMD python LUCIES/run.py --wandb=sureli/ERL_paper --pop=48 --mu=12 --max_evals=500000 --net=min --env=min-seaquest --im --optim=sepcma

for seed in 0
do 
python LUCIES/run.py --wandb=sureli/ERL_paper --pop=48 --mu=12 --max_evals=500000 --net=min --env=min-seaquest --im --optim=sepcma
done