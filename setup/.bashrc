# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi

# Uncomment the following line if you don't like systemctl's auto-paging feature:
# export SYSTEMD_PAGER=

# User specific aliases and functions
export PS1="\[\e[0;32m\]\u\[\e[m\e[0;36m\]@\h:\[\e[m\e[0;33m\]\w$\[\e[m\] "

#module load python/3.6.8
#module load julia/1.5.3
#source activate /tmpdir/templier/envs/torchenv

NAME=$(whoami)
# PROJECT=p21001

export WANDB_CACHE_DIR="/tmpdir/$NAME/wandb/.cache"

alias python=python3
alias activate="module load python/3.6.8 && source activate /tmpdir/$NAME/envs/torchenv"
alias jobs="watch squeue -u $NAME -o \'%.8i %.4j %.6M %.6C %D %R\'"
alias tologs="cd /tmpdir/$NAME/slurm_logs"
alias run="~/Compute/run.sh"
alias pull="git stash; git fsck && git gc --prune=now; git pull"
alias sync="~/sync_wandb.sh"
alias memory="du -shc -- {.[!.],..?,}*"
alias q="python3 ~/sentinel.py"
alias pip="python3 -m pip"