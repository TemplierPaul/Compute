#!/bin/bash                                                                                                                                                                                                        
                                                                                                                                                                                                                
#SBATCH -J BERL

#SBATCH -N 6
#SBATCH -n 216

#SBATCH --ntasks-per-node=36
#SBATCH --ntasks-per-core=1
#SBATCH --threads-per-core=1
#SBATCH --time=06:00:00

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

echo CMD echo hellp args1 --test=test1

for seed in 0 1 2
do 
echo hellp args1 --test=test1
done