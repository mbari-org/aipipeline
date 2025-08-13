#!/usr/bin/env just --justfile

# List recipes
list:
    @just --list --unsorted

# Private base recipe for environment setup (underscore prefix makes it private)
_base_cmd *flags:
    #!/usr/bin/env bash
    export PYTHONPATH=deps:deps/biotrack:.
    export MPLCONFIGDIR=/tmp
    time conda run -n aipipeline --no-capture-output python3 {{flags}}

# Setup the environment
install: update_trackers
    conda run -n aipipeline pip install https://github.com/redis/redis-py/archive/refs/tags/v5.0.9.zip
    git clone http://github.com/mbari-org/aidata.git deps/aidata
    git clone https://github.com/facebookresearch/co-tracker deps/co-tracker
    conda run -n aipipeline pip install -r deps/aidata/requirements.txt
    cd deps/co-tracker && conda run -n aipipeline pip install -e .
    cd .. && mkdir checkpoints && cd checkpoints && wget https://huggingface.co/facebook/cotracker3/resolve/main/scaled_offline.pth

# Copy core dev code to the project on doris
cp-core:
    #!/usr/bin/env bash
    cd ..
    cp justfile /Volumes/dcline/code/aipipeline/justfile
    cp requirements.txt /Volumes/dcline/code/aipipeline/requirements.txt
    cp aipipeline/config* /Volumes/dcline/code/aipipeline/aipipeline/
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.log' --exclude='*__pycache__' ./justfiles/  /Volumes/dcline/code/aipipeline/justfiles/
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.log' --exclude='*__pycache__' aipipeline/prediction/  /Volumes/dcline/code/aipipeline/aipipeline/prediction/
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.log' --exclude='*__pycache__' aipipeline/metrics/  /Volumes/dcline/code/aipipeline/aipipeline/metrics/
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.log' --exclude='*__pycache__' aipipeline/db/  /Volumes/dcline/code/aipipeline/aipipeline/db/
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.log' --exclude='*__pycache__' aipipeline/engines/  /Volumes/dcline/code/aipipeline/aipipeline/engines/

# Update the environment. Run this command after checking out any code changes
update_trackers:  
    conda env update_trackers --file environment.yml --prune

# Update environment
update-env:  
  conda env update --file environment.yml --prune

init-labels project='uav' leaf_type_id='19':
    time just --justfile {{justfile()}} _base_cmd "aipipeline/prediction/leaf_init.py \
    --config aipipeline/projects/{{project}}/config/config.yml \
    --labels aipipeline/projects/{{project}}/config/labels.yml  \
    --type-id {{leaf_type_id}}"

# Compute saliency for downloaded VOC data and update the Tator database
compute-saliency project='uav' *more_args="":
    time just --justfile {{justfile()}} _base_cmd "aipipeline/prediction/saliency_pipeline.py \
    --config aipipeline/projects/{{project}} \
    {{more_args}}"

# Generate training data stats from downloaded data. Aggregate stats for nested directories
gen-stats-csv project='UAV' data='/mnt/ML_SCRATCH/UAV/':
    time just --justfile {{justfile()}} _base_cmd "aipipeline/prediction/gen_stats.py --data {{data}} --prefix {{project}}"

# Load clusters for any project, e.g. just load-cluster uav /mnt/ML_SCRATCH/UAV/2024-10-19/cluster.csv. Assumes images/boxes for the project are already loaded
load-cluster project="uav" data='data' version="Baseline" *more_args="":
    time conda run -n aipipeline --no-capture-output aidata load clusters \
        --config aipipeline/projects/{{project}}/config/config.yml \
        --input {{data}} --version {{version}} \
        --token $TATOR_TOKEN {{more_args}}"