# Copy this to justfiles/uav.just
cp-dev-vss:
    #!/usr/bin/env bash
    cd ..
    cp justfiles/vss.just /Volumes/dcline/code/aipipeline/justfiles/vss.just
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.log' --exclude='*__pycache__' aipipeline/db/  /Volumes/dcline/code/aipipeline/aipipeline/db/

# Generate a tsne plot of the VSS database
plot-tsne-vss project='uav':
    time just --justfile {{justfile()}} _base_cmd "aipipeline/metrics/plot_tsne_vss.py \
        --config aipipeline/projects/{{project}}/config/config.yml"

optimize-vss project='uav' *more_args="":
    echo "Optimizing VSS DB for {{project}} with {{more_args}}"
    time just --justfile {{justfile()}} _base_cmd "aipipeline/metrics/optimize_vss.py \
        --config aipipeline/projects/{{project}}/config/config.yml \
        {{more_args}}"

# Calculate the accuracy of the VSS database; run after download, then optimize
calc-acc-vss project='uav':
    time just --justfile {{justfile()}} _base_cmd "aipipeline/metrics/calc_accuracy_vss.py \
        --config aipipeline/projects/{{project}}/config/config.yml"

# Reset the VSS database, removing all data. Proceed with caution!!
reset-vss-all:
    #!/usr/bin/env bash
    echo "Resetting all VSS data"
    projects=(uav cfe bio i2map)
    for project in ${projects[@]}; do
      project_dir=./aipipeline/projects/$project
      time just --justfile {{justfile()}} _base_cmd "aipipeline/db/redis/vss/reset.py \
        --config ${project_dir}/config/config.yml"
    done

# Reset the VSS database, removing all data. Run before init-vss or when creating the database. Run with e.g. `uav`
reset-vss project='uav':
    time just --justfile {{justfile()}} _base_cmd "aipipeline/db/redis/vss/reset.py \
        --config aipipeline/projects/{{project}}/config/config.yml"

# Remove an entry from the VSS database, e.g. j remove-vss i2map --doc \'doc:marine organism:\*\'
remove-vss project='uav' *more_args="":
    echo "Removing entry from VSS DB for {{project}} with {{more_args}}"
    time just --justfile {{justfile()}} _base_cmd "aipipeline/db/redis/vss/remove.py \
        --config aipipeline/projects/{{project}}/config/config.yml \
        {{more_args}}"

# Initialize the VSS database for a project, e.g. just init-vss uav
init-vss project='uav' *more_args="":
    time just --justfile {{justfile()}} _base_cmd "aipipeline/db/redis/vss/init_pipeline.py \
        --config aipipeline/projects/{{project}}/config/config.yml \
        --batch-size 1 \
        --skip-clean True \
        {{more_args}}"

# Load already computed exemplars into the VSS database
load-vss project='uav' :
    time just --justfile {{justfile()}} _base_cmd "aipipeline/db/redis/vss/load_pipeline.py \
        --config aipipeline/projects/{{project}}/config/config.yml"

# Predict images using the VSS service and load the results into Tator
predict-vss-load project='uav' image_dir='/tmp/download' *more_args="":
    time just --justfile {{justfile()}} _base_cmd "aipipeline/db/redis/vss/predict_load_pipeline.py \
    --config ./aipipeline/projects/{{project}}/config/config.yml \
    --image-dir {{image_dir}} \
    {{more_args}}"

predict-vss-by-dir project='uav' image_dir='/tmp/download' *more_args="":
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/{{project}}

    export PYTHONPATH=.
    ##############################################
    # Predict images using the VSS service, processing images
    # in subdirectories one at a time to limit memory use
    image_dir="{{image_dir}}"
    echo "Finding subdirectories in {{image_dir}}"
    subdirs=$(ls -d {{image_dir}}/*/)
    for subdir in $subdirs; do
        echo "Processing subdirectory $subdir"
        time just --justfile {{justfile()}} predict-vss {{project}} $subdir {{more_args}}
    done

# Predict images using the VSS service. Run with e.g. just predict-vss planktivore-lm /mnt/ML_SCRATCH/Planktivore/aidata-export-03-low-mag-square. Results are archived to /mnt/DeepSea-AI/data/
predict-vss project='uav' image_dir="/tmp/download" *more_args="":
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/{{project}}
    export PYTHONPATH=.
    ##############################################
    # Create a unique name for the image directory listing file and
    # search the images first and then run the search pipeline
    # This is because the beam file match pipeline incurs some overhead
    # This is simply faster for millions of images
    image_dir="{{image_dir}}"
    flat_name="${image_dir//\//-}" # Replace all slashes with dashes
    flat_name="${flat_name#-}" # Remove leading dash if it exists
    image_listing="${flat_name}-images.txt"
    if [ ! -f "$image_listing" ] || [ ! -s "$image_listing" ]; then
        echo "Finding images in {{image_dir}}"
        find {{image_dir}} -name '*.png' >> $image_listing
    else
        echo "Using existing file $image_listing"
    fi
    time just --justfile {{justfile()}} _base_cmd "aipipeline/db/redis/vss/predict_pipeline.py \
    --config aipipeline/projects/{{project}}/config/config.yml \
    --input $image_listing \
    --batch-size 512 \
    {{more_args}}"

