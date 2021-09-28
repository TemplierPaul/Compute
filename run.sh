# !/bin/sh
cd

type="none"

path="/home/disc/p.templier/Compute"

save_path="/scratch/disc/p.templier/slurm_logs"
out="$save_path/slurm.%j.out"
err="$save_path/slurm.%j.err"

echo "Starting CPU experiments"
while IFS= read -r line || [ -n "$line" ]
do
        if [ -n "$line" ] && [ ${line:0:2} == "##" ]
        then
        type="${line:3:10}"
        type="${type,,}"
        echo "$type"
        fi

        case $type in
                cpu)
                slurm_file="$path/slurm/job_cpu.slurm"
                ;;
                long)
                slurm_file="$path/slurm/job_long_cpu.slurm"
                ;;
                gpu)
                slurm_file="$path/slurm/job_gpu.slurm"
                ;;
                light)
                slurm_file="$path/slurm/job_light_cpu.slurm"
                ;;
                dqn)
                slurm_file="$path/slurm/job_light_gpu.slurm"
                ;;
                none)
                slurm_file=""
                ;;
                *)
                echo "unknown"
                ;;
        esac

        if [ -n "$line" ] && [ ${line::1} != "#" ] && ( [ $1 == $type ] || [ $1 == "all" ] )
        then
        # echo "$slurm_file"
        echo "STARTING > $line"
        sbatch --export=ALL,cmd="$line" --error=$err --output=$out "$slurm_file"
        fi
done < "$path/joblist.txt"