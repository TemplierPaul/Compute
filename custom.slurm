#!/bin/bash                                                                                                                                                                                                        
                                                                                                                                                                                                                
#SBATCH -J BERL

#SBATCH -N 1
#SBATCH -n 1

#SBATCH --ntasks-per-node=36
#SBATCH --ntasks-per-core=1
#SBATCH --threads-per-core=1
#SBATCH --time=00:05:00

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

echo CMD sleep 5 && echo hello $HOSTNAME run_2

for seed in 0
do 
sleep 5 && echo hello $HOSTNAME run_2
done