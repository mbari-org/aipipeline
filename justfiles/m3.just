# Copy M3 dev code to the project on doris
cp-m3-bio:
    #!/usr/bin/env bash
    cd ..
    cp justfiles/m3.just /Volumes/dcline/code/aipipeline/justfiles/m3.just
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.log' --exclude='*__pycache__' aipipeline/projects/bio/ /Volumes/dcline/code/aipipeline/aipipeline/projects/bio/

# Crop detections from VOC formatted data
crop-m3-voc:
    @echo "Cropping detections from VOC formatted data..."
    time just --justfile {{justfile()}} _base_cmd "aipipeline/prediction/crop_pipeline.py \
        --config aipipeline/projects/bio/config/config.yml \
        --images /mnt/DeepSea-AI/data/M3/images \
        --xml /mnt/DeepSea-AI/data/M3/xml \
        --output_dir /mnt/DeepSea-AI/data/M3/crops"

# Initialize the VSS database
init-vss-m3:
    time just --justfile {{justfile()}} _base_cmd "aipipeline/db/redis/vss/init_pipeline.py \
        --config aipipeline/projects/m3/config/config.yml \
        --skip-download \
        --skip-generate-views \
        --data.download_dir /mnt/DeepSea-AI/data/M3/crops"