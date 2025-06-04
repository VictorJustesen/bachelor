#!/bin/bash
# LSF Batch Job Script for running automl.py

### General LSF options ###

# -- specify queue -- 
#BSUB -q gpuv100

# -- Set the job Name --
#BSUB -J bachelor_rigorous

# -- ask for number of cores (default: 1) -- 
#BSUB -n 4  # Using 4 cores, auto-sklearn n_jobs=-1 will use these

# -- Request GPU resources --
#BSUB -gpu "num=1:mode=exclusive_process" # auto-sklearn primarily uses CPU; GPU might be idle unless XGBoost is GPU-enabled and selected.

# -- specify that the cores must be on the same host -- 
#BSUB -R "span[hosts=1]"

# -- specify that we need memory per core/slot -- 
#BSUB -R "rusage[mem=8GB]" # Increased to 8GB per core (Total 32GB for n=4)

# -- specify that we want the job to get killed if it exceeds memory per core/slot -- 
#BSUB -M 9GB # Increased max memory per core (Total 40GB for n=4)

# -- Set walltime limit: hh:mm --
#BSUB -W 08:00 # Increased to 4 hours (3 splits * 1 hour/split + buffer)

# -- Specify the output and error file. %J is the job-id -- 
#BSUB -o logs/automl_%J.out
#BSUB -e logs/automl_%J.err

# -- set the email address -- 
##BSUB -u s224296@dtu.dk  # Use your actual email
# Send email on job start (-B) and job end/failure (-N)
##BSUB -B
##BSUB -N


mkdir -p logs
mkdir -p results

echo "=========================================================="
echo "Job Started on $(hostname)"
echo "Job ID: $LSB_JOBID"
echo "Working Directory: $(pwd)"
echo "Requested Cores: $LSB_DJOB_NUMPROC"
echo "Allocated Hosts: $LSB_HOSTS"
echo "Queue: $LSB_QUEUE"
echo "Start Time: $(date)"
echo "=========================================================="

echo "Loading required modules..."
module purge 

source ~/.bashrc
module load cuda/11.8      
echo "Modules loaded:"
module list


echo "Activating  environment"
conda activate bachelor
echo "Conda environment: $CONDA_DEFAULT_ENV"
if [ -z "$CONDA_DEFAULT_ENV" ] || [ "$CONDA_DEFAULT_ENV" != "bachelor" ]; then
    echo "ERROR: Failed to activate conda environment 'bachelor'."
    exit 1
fi
echo "Python path: $(which python)"



cd ~/school/bachelor/scraping|| exit 1
echo "Working directory set to: $(pwd)"

echo "Running"

python -u new2.py

# Capture the exit status of the python script
status=$?
if [ $status -ne 0 ]; then
    echo "ERROR failed with exit status $status"
    exit $status
fi

echo "finished successfully."

exit 0
