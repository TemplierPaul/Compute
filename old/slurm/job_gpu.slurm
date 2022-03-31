#!/bin/bash                                                                                                                                                                                                        
                                                                                                                                                                                                                   
#SBATCH -J GPU
#SBATCH --nodes=1

# Test
# SBATCH --ntasks=2
# SBATCH --ntasks-per-node=2
# SBATCH --time=00:05:00

# Run
#SBATCH --ntasks=24
#SBATCH --ntasks-per-node=24
#SBATCH --time=24:00:00

# GPU
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1

# Big memory
# SBATCH --partition=bigmem

#SBATCH --ntasks-per-core=1
#SBATCH --begin=now
#SBATCH --mail-user=paul.templier@isae-supaero.fr
#SBATCH --mail-type=ALL

# module purge
# module load python/3.7
# conda init bash
# conda activate myenv
# which python

echo '
print("GPU")
import gym
' | python

echo $cmd
$cmd
