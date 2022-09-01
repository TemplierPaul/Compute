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

module purge
module load python/3.7
module load libosmesa/17.2.3
cd /home/disc/p.templier/parallelpy
source pyenv/bin/activate
echo $(which python)
cd


wandb enabled
wandb online

echo CMD python LUCIES/run.py --wandb=sureli/LUCIES_dev --pop=48 --mu=12 --max_evals=500000 --net=min --env=min-asterix --optim=canonical

for seed in 0
do 
python LUCIES/run.py --wandb=sureli/LUCIES_dev --pop=48 --mu=12 --max_evals=500000 --net=min --env=min-asterix --optim=canonical
done