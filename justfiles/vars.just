# Copy M3 dev code to the project on doris
cp-vars:
    #!/usr/bin/env bash
    cd ..
    cp justfiles/vars.just /Volumes/dcline/code/aipipeline/justfiles/vars.just
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.log' --exclude='*__pycache__' aipipeline/projects/vars/ /Volumes/dcline/code/aipipeline/aipipeline/projects/vars/

gen-vars-data:
    just --justfile {{justfile()}} download-crop vars  \
        --skip-clean \
        --data.download_dir /mnt/DeepSea-AI/data/VARS \
        --data.download_args "'--verified --crop-roi --resize 224 --voc'"

# Crop detections from VOC formatted data
crop-vars-voc:
    @echo "Cropping detections from VOC formatted data..."
    time just --justfile {{justfile()}} _base_cmd "aipipeline/prediction/crop_pipeline.py \
        --config aipipeline/projects/bio/config/config.yml \
        --images /mnt/DeepSea-AI/data/VARS/images \
        --xml /mnt/DeepSea-AI/data/VARS/xml \
        --output_dir /mnt/DeepSea-AI/data/M3/crops"

# Initialize the VSS database for VARS
init-vss-vars:
    time just --justfile {{justfile()}} _base_cmd "aipipeline/db/redis/vss/init_pipeline.py \
        --config aipipeline/projects/vars/config/config.yml \
        --skip-download \
        --skip-generate-views \
        --min-detections 25000 \
        --batch-size 512 \
        --data.download_dir /mnt/DeepSea-AI/data/VARS/crops"