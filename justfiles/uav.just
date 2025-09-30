# Copy uav dev code to the project on doris
cp-dev-uav:
    #!/usr/bin/env bash
    cd ..
    cp justfiles/uav.just /Volumes/dcline/code/aipipeline/justfiles/uav.just
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.pt*' --exclude='*.log' --exclude='*__pycache__' ./aipipeline/projects/uav/ /Volumes/dcline/code/aipipeline/aipipeline/projects/uav/

# Cluster mission in aipipeline/projects/uav/data/missions-to-process.txt
cluster-uav *more_args="":
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/uav
    export PYTHONPATH=.
    time just --justfile {{justfile()}} _base_cmd "--config aipipeline/projects/uav/cluster_pipeline.py \
        --missions aipipeline/projects/uav/data/missions-to-process.txt \
        --config aipipeline/projects/uav/config/config.yml \
        {{more_args}}"

# Detect mission in aipipeline/projects/uav/data/hawaii-video.txt
detect-uav *more_args="":
    time just --justfile {{justfile()}} _base_cmd "aipipeline/projects/uav/detect_pipeline.py \
    --missions aipipeline/projects/uav/data/missions-to-process.txt \
        --config aipipeline/projects/uav/config/config.yml \
        {{more_args}}"

# Load uav mission images in aipipeline/projects/uav/data/missions-to-process.txt
load-uav-images:
    time just --justfile {{justfile()}} _base_cmd "aipipeline/projects/uav/load_image_pipeline.py \
        --missions aipipeline/projects/cfe/data/missions-to-process.txt \
        --config aipipeline/projects/cfe/config/config.yml"

# Load uav detections/clusters in aipipeline/projects/uav/data/missions-to-process.txt
load-uav type="cluster|detect":
    time just --justfile {{justfile()}} _base_cmd "aipipeline/projects/uav/load_sdcat_pipeline.py \
        --missions aipipeline/projects/uav/data/missions-to-process.txt \
        --config aipipeline/projects/uav/config/config.yml \
        --type {{type}}"

# Fix UAV metadata lat/lon/alt
fix-uav-metadata:
    time just --justfile {{justfile()}} _base_cmd "aipipeline/projects/uav/fix_metadata.py"

# Generate training data for the uav project
gen-uav-data:
  just --justfile {{justfile()}} download-crop uav \
        --clean \
        --gen-multicrop \
        --data.processed_path /mnt/ML_SCRATCH/uav \
        --data.download_args "'--verified --disable-ssl-verify --version yolo11x-oneclass-uav-vits-b-8-20250202'"
  echo "Done. Data is in /mnt/ML_SCRATCH/uav"
