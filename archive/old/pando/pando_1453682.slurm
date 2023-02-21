#!/bin/bash                                                                                                                                                                                                        
                                                                                                                                                                                                                
#SBATCH -J Optim

#SBATCH -N 1
#SBATCH -n 24

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

echo CMD python3 Rayvolution/simple.py --pop=24 --mu=12 --job=$SLURM_JOB_ID --max_frames=100000 --max_evals=100000 --save_freq=0 --env=rosen --noise_factor=1000 --optim=canonical --noise=5 --noise_type=gaussian --sampling=mc --es_seed=3 --eval_budget=5 --batch_rs=1 --mc_samples=25 --wandb=sureli/rayvolution --tag=noise_factor

for seed in 0
do 
python3 Rayvolution/simple.py --pop=24 --mu=12 --job=$SLURM_JOB_ID --max_frames=100000 --max_evals=100000 --save_freq=0 --env=rosen --noise_factor=1000 --optim=canonical --noise=5 --noise_type=gaussian --sampling=mc --es_seed=3 --eval_budget=5 --batch_rs=1 --mc_samples=25 --wandb=sureli/rayvolution --tag=noise_factor
done