# Copy i2map dev code to the project on doris
cp-dev-i2map:
    #!/usr/bin/env bash
    cd ..
    cp justfiles/i2map.just /Volumes/dcline/code/aipipeline/justfiles/i2map.just
    cp aipipeline/projects/i2map/config/*.yml /Volumes/dcline/code/aipipeline/aipipeline/projects/i2map/config/
    cp aipipeline/projects/i2mapbulk/config/*.yml /Volumes/dcline/code/aipipeline/aipipeline/projects/i2mapbulk/config/
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.log' --exclude='*__pycache__' aipipeline/projects/i2map/ /Volumes/dcline/code/aipipeline/aipipeline/projects/i2map/
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.log' --exclude='*__pycache__' aipipeline/projects/i2mapbulk/ /Volumes/dcline/code/aipipeline/aipipeline/projects/i2mapbulk/

# Run the mega strided pipeline on a single video or entire dive for the i2map project
#run-mega-stride-i2map video='/mnt/M3/mezzanine/Ventana/2023/10/4505/*.mp4':
run-mega-stride-i2map video='/mnt/DeepSea-AI/data/i2MAP/2025/04/i2MAP_20250402T172257Z_301m_F031_5.*' vit_model='/mnt/DeepSea-AI/models/bio/mbari-i2map-vits-b-8-20250216' version='megadetrt-mbari-i2map-vits-b-8-20250216':
    time just --justfile {{justfile()}} _base_cmd "aipipeline/projects/bio/process_video_pipeline.py \
        --config aipipeline/projects/i2map/config/config.yml \
        --skip-track \
        --min-score-det 0.01 \
        --batch-size 0 \
        --min-score-track 0.3 \
        --min-frames 0 \
        --version {{version}} \
        --vits-model {{vit_model}} \
        --det-model /mnt/DeepSea-AI/models/midwater/megadetrt-yolov5 \
        --stride 30 --video {{video}}"

# Run the mega track pipeline on a single video or entire dive for the i2map project
#run-mega-stride-i2map video='/mnt/M3/mezzanine/Ventana/2023/10/4505/*.mp4':
run-mega-track-i2map video='/mnt/DeepSea-AI/data/i2MAP/2025/04/i2MAP_20250402T172257Z_301m_F031_5.*' vit_model='/mnt/DeepSea-AI/models/bio/mbari-i2map-vits-b-8-20250216' version='megadetrt-mbari-i2map-vits-b-8-20250216-track':
    time just --justfile {{justfile()}} _base_cmd "aipipeline/projects/bio/process_video_pipeline.py \
        --config aipipeline/projects/i2map/config/config.yml \
        --max-frames-tracked 300 \
        --min-score-det 0.01 \
        --batch-size 16 \
        --min-score-track 0.1 \
        --min-frames 2 \
        --version {{version}} \
        --vits-model {{vit_model}} \
        --det-model /mnt/DeepSea-AI/models/midwater/megadetrt-yolov5 \
        --stride 1 --video {{video}}" #--save-cotrack-video

# Download i2mpabulk unlabeled data run with ENV_FILE=.env.i2map just download-i2mapbulk-unlabeled
download-i2mapbulk-unlabeled:
    time just --justfile {{justfile()}} _base_cmd "aipipeline/db/tator/download_crop_pipeline.py \
        --config aipipeline/projects/i2mapbulk/config/config.yml \
        --data.download_dir /mnt/ML_SCRATCH/i2mapbulk \
        --data.download_args \'--unverified\' "

# Load i2MAP bulk data run with ENV_FILE=.env.i2map just load-i2mapbulk <path to the cluster_detections.csv file>
load-i2mapbulk data='data':
    time just --justfile {{justfile()}} _base_cmd "aipipeline/projects/i2mapbulk/load_pipeline.py \
        --config aipipeline/projects/i2mapbulk/config/config.yml --data {{data}}"

# Generate training data for the i2map project
gen-i2map-data:
    time just --justfile {{justfile()}} _base_cmd "aipipeline/db/tator/download_crop_pipeline.py \
        --config aipipeline/projects/i2map/config/config.yml \
        --clean \
        --use-cleanvision True \
        --data.download_dir /mnt/ML_SCRATCH/i2map \
        --data.download_args '--version Baseline --generator vars-labelbot --group NMS '"

# Download and cluster data. Run with  just download-cluster i2map
cluster-i2map:
    just --justfile {{justfile()}} cluster i2map --version Baseline \
        --input /mnt/ML_SCRATCH/i2map/Baseline/crops \
        --output /mnt/ML_SCRATCH/i2map/Baseline/clusters

# Generate training data for the i2map project from the bulk server, run with ENV_FILE=.env.i2map just gen-i2mapbulk-data
gen-i2mapbulk-data:
    time just --justfile {{justfile()}} _base_cmd "aipipeline/db/tator/download_crop_pipeline.py \
        --config aipipeline/projects/i2mapbulk/config/config_unknown.yml \
        --clean \
        --use-cleanvision True \
        --gen-multicrop \
        --data.download_dir /mnt/ML_SCRATCH/i2mapbulk \
        --data.download_args '--verified '"

# Cluster bulk unknown data
cluster-i2mapbulk:
    #!/usr/bin/env bash
    export PROJECT_DIR=$PWD/aipipeline/projects/i2mapbulk
    export RAY_TMPDIR=/mnt/ML_SCRATCH/ray/
    export MPLCONFIGDIR=/mnt/ML_SCRATCH/matplotlib
    export RAY_DEDUP_LOGS=0
    cd ~/code/sdcat
    time conda run -n rapids-25.04 sdcat cluster roi --config-ini $PROJECT_DIR/config/sdcat.ini \
            --roi-dir /mnt/ML_SCRATCH/i2mapbulk/crops/Unknown \
            --save-dir /mnt/ML_SCRATCH/i2mapbulk/clusters/Unknown \
            --alpha 1.0 \
            --cluster-selection-epsilon .002 \
            --min-cluster-size 3 \
            --device cuda \
            --use-vits \
            --vits-batch-size 512 \
            --hdbscan-batch-size 50000

# Sweep cluster bulk unknown data
cluster-i2mapbulk-sweep:
    #!/usr/bin/env bash
    export PROJECT_DIR=$PWD/aipipeline/projects/i2mapbulk
    export RAY_TMPDIR=/mnt/ML_SCRATCH/ray/
    export MPLCONFIGDIR=/mnt/ML_SCRATCH/matplotlib
    export RAY_DEDUP_LOGS=0
    cd ~/code/sdcat
    for epsilon in 0. .001 .002 .003; do
        for alpha in 1. 1.1 1.2; do
            for min_cluster in 3 5 7; do
                echo "Running alpha=$alpha epsilon=$epsilon min_cluster=$min_cluster"
                time conda run -n rapids-25.04 sdcat cluster roi --config-ini $PROJECT_DIR/config/sdcat.ini \
                        --roi-dir /mnt/ML_SCRATCH/i2mapbulk/crops/Unknown \
                        --save-dir /mnt/ML_SCRATCH/i2mapbulk/clusters/Unknown \
                        --alpha $alpha \
                        --cluster-selection-epsilon $epsilon \
                        --min-cluster-size $min_cluster \
                        --device cuda \
                        --use-vits \
                        --vits-batch-size 512 \
                        --hdbscan-batch-size 50000 \
                        --skip-visualization
            done
        done
    done
# Transcode i2MAP videos from mov to mp4 for use in Tator
transcode-i2map:
    aipipeline/projects/i2map/mov2mp4.sh

# Generate cluster plots for i2map
gen-cluster-plots-i2map:
    time just --justfile {{justfile()}} _base_cmd "aipipeline/projects/i2mapbulk/cluster_sweep_plot.py"