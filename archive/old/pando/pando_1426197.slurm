#!/bin/bash                                                                                                                                                                                                        
                                                                                                                                                                                                                
#SBATCH -J Procgen

#SBATCH -N 1
#SBATCH -n 1

#SBATCH --ntasks-per-node=24
#SBATCH --ntasks-per-core=1
#SBATCH --threads-per-core=1
#SBATCH --time=1-00:00:00

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

echo CMD python3 sentinel.py --freq=10 --headless 

python3 sentinel.py --freq=10 --headless 