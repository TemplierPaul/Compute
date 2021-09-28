#!/bin/bash                                                                                                                                                                                                        
                                                                                                                                                                                                                   
#SBATCH -J long
#SBATCH --nodes=1

# Test
# SBATCH --ntasks=2
# SBATCH --ntasks-per-node=2
# SBATCH --time=00:05:00

# Long
#SBATCH --partition=long

# Run
#SBATCH --ntasks=24
#SBATCH --ntasks-per-node=24
#SBATCH --time=3-00:00:00

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
print("Long")
import gym
import dqnes
' | python

echo $cmd
$cmd

