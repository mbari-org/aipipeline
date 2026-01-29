# Copy cfe dev code to the project on doris
cp-dev-cfe:
    #!/usr/bin/env bash
    cd ..
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.png' --exclude='*.log' --exclude='*__pycache__' ./aipipeline/projects/cfe/ /Volumes/dcline/code/aipipeline/aipipeline/projects/cfe/
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.png' --exclude='*.log' --exclude='*__pycache__' ./aipipeline/projects/cfedeploy/ /Volumes/dcline/code/aipipeline/aipipeline/projects/cfedeploy/
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.log' --exclude='*__pycache__' ./justfiles/  /Volumes/dcline/code/aipipeline/justfiles/

# Generate training data for the CFE project
gen-cfe-data:
  just --justfile {{justfile()}} download-crop cfe --clean --gen-multicrop \
        --data.download_dir /mnt/ML_SCRATCH/isiis \
        --data.download_args "'--verified --version Baseline'"

# Generate data for the CFE project from the deployment version cfe_isiis_dino_v7-20250916
gen-cfe-dino_v7:
  just --justfile {{justfile()}} download-crop cfedeploy --clean --gen-multicrop \
        --data.download_dir /mnt/ML_SCRATCH/isiis \
        --data.download_args "'--voc --version cfe_isiis_dino_v7-20250916 '"

# Merge absolute media paths for CFE ISII RC mission with downloaded localizations.csv
merge-media-cfe-isiis-rc:
    time just --justfile {{justfile()}} _base_cmd "aipipeline/projects/cfedeploy/merge_media_path.py"

# Fast crop ROI for CFE ISIIs mission videos
fast-crop-cfe-isiis-rc:
    time just --justfile {{justfile()}} _base_cmd "aipipeline/projects/cfedeploy/fast_crop_roi.py"

# Load cfe ISII mission videos. Run with e.g. just load-cfe-isiis-videos hawaii-video.txt or just load-cfe-isiis-videos rachelcarson-video.txt. Populate files in project/cfedeploy/data first
load-cfe-isiis-videos missions="":
    time just --justfile {{justfile()}} _base_cmd "aipipeline/projects/cfedeploy/load_isiis_video_pipeline.py \
        --config $PROJECT_DIR/config/config.yml" \
        --missions $PROJECT_DIR/data/{{missions}}

# Load cfe ISII mission localizations that have been classified. Run with e.g. just load-cfe-isiis-loc-classified /mnt/CFElab/Data_analysis/ISIIS/20240206_RachelCarson_detections/det_filtered/csv/ 14 Baseline
load-cfe-isiis-loc-classified data_dir="" stride="14" version="Baseline":
    time just --justfile {{justfile()}} _base_cmd "aipipeline/projects/cfedeploy/load_isiis_loc_pipeline.py \
        --config aipipeline/projects/cfedeploy/config/config.yml" \
        --data {{data_dir}} \
        --stride {{stride}} \
        --version {{version}}

# Load cfe ISII mission localizations. Run with e.g. just load-cfe-isiis-loc /mnt/CFElab/Data_analysis/ISIIS/20240206_RachelCarson_detections/det_filtered/csv/ 14
load-cfe-isiis-loc data_dir="" stride="14" version="Baseline":
    time just --justfile {{justfile()}} _base_cmd "aipipeline/projects/cfedeploy/load_isiis_loc_pipeline.py \
        --config aipipeline/projects/cfedeploy/config/config.yml" \
        --data {{data_dir}} \
        --stride {{stride}} \
        --label Unknown \
        --version {{version}}

# Cluster CFE ISIIS hawaii mission frames. Cleans first, then clusters
cluster-cfe-isiis roi_dir="/mnt/ML_SCRATCH/cfe/Hawaii_detections/det_filtered_reduction/crops/" save_dir="/mnt/ML_SCRATCH/cfe/Hawaii_detections/det_filtered_reduction/cluster/ ":
    time just --justfile {{justfile()}} _base_cmd "aipipeline/prediction/clean_pipeline.py \
        --config aipipeline/projects/cfedeploy/config/config.yml \
        --image-dir {{roi_dir}}"

# Cluster CFE ISIIS hawaii mission frames. First pass with trained local model
cluster-cfe-isiis-hawaii-p1:
    #!/usr/bin/env bash
    conda activate rapids-25.04
    export PYTHONPATH=.
    export RAY_TMPDIR=/mnt/ML_SCRATCH/ray/
    export MPLCONFIGDIR=/mnt/ML_SCRATCH/matplotlib
    export DET_DIR=/mnt/CFElab/Data_archive/Images/ISIIS/COOK/Videos2frames/Hawaii_detections/det_filtered_reduction
    # Run the first pass clustering with the local model
    sdcat cluster detections \
        --det-dir $DET_DIR \
        --save-dir /mnt/ML_SCRATCH/cfe/Hawaii_detections/det_filtered_reduction \
        --config-ini /u/dcline/code/aipipeline/aipipeline/projects/cfedeploy/config/sdcat_cfe_isiis_final-20250509.ini \
        --vits-batch-size 512 \
        --hdbscan-batch-size 50000 \
        --device cuda \
        --use-vits \
        --use-cuhdbscan --skip-visualization
    echo "First pass clustering complete. Now copy the cluster run output in $DET_DIR to a directory and use with the cluster-cfe-isiis-hawaii-p2 recipe


cluster-cfe-isiis-hawaii-p2 p1_dir="":
    #!/usr/bin/env bash
    conda activate rapids-25.04
    export PYTHONPATH=.
    export RAY_TMPDIR=/mnt/ML_SCRATCH/ray/
    export MPLCONFIGDIR=/mnt/ML_SCRATCH/matplotlib
    # Run the first pass clustering with the local model
    sdcat cluster detections \
        --det-dir {{p1_dir}} \
        --save-dir /mnt/ML_SCRATCH/cfe/Hawaii_detections/det_filtered_reduction \
        --config-ini aipipeline/projects/cfedeploy/config/sdcat_fb_dino-vits8.ini \
        --vits-batch-size 512 \
        --hdbscan-batch-size 50000 \
        --device cuda \
        --use-vits

# run sweep for ISIIS data. Example just cluster-isiis-sweep /mnt/ML_SCRATCH/cfe/Hawaii_detections/det_filtered_reduction/denoise_s2 /mnt/ML_SCRATCH/cfe/Hawaii_detections/det_filtered_reduction
cluster-isiis-sweep det_dir='/mnt/ML_SCRATCH/cfe/Hawaii_detections/det_filtered_reduction/denoise_s2/' save_dir='/mnt/ML_SCRATCH/cfe/Hawaii_detections/det_filtered_reduction':
    #!/usr/bin/env bash
    export PROJECT_DIR=$PWD/aipipeline/projects/cfedeploy
    export RAY_TMPDIR=/mnt/ML_SCRATCH/ray/
    export MPLCONFIGDIR=/mnt/ML_SCRATCH/matplotlib
    export RAY_DEDUP_LOGS=0
    cd ~/code/sdcat
    for epsilon in 0. .001 .002 .003; do
        for alpha in 1. 1.1 1.2; do
            for min_cluster in 3 5 7; do
                echo "Running alpha=$alpha epsilon=$epsilon min_cluster=$min_cluster"
                time conda run -n rapids-25.04 python -m sdcat cluster detections --config-ini $PROJECT_DIR/config/sdcat.ini \
                        --det-dir {{det_dir}} \
                        --save-dir {{save_dir}} \
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

# Initialize the VSS database with CFE ISIIS downloaded data from CFE lab Baseline_v3
# This populates the vector database with the crops from Baseline_v3, up to 2000 images per class
init-vss-cfe-isiis:
    mkdir /tmp/Baseline_v3 || true
    cp -r /mnt/CFElab/Data_analysis/ISIIS/Baseline_v3/crops /tmp/Baseline_v3
    time conda run -n aipipeline --no-capture-output python3 aipipeline/db/redis/vss/init_pipeline.py \
        --config aipipeline/projects/cfe/config/config.yml \
        --skip-download \
        --skip-generate-views \
        --data.download_dir /tmp/Baseline_v3

# Transcode CFE ISIIS videos from mov to mp4 for use in Tator from Rachel Carson
transcode-cfe-isiis-rc:
    time just --justfile {{justfile()}} _base_cmd "aipipeline/projects/cfedeploy/mov2mp4.py \
        --input "/mnt/CFElab/Data_archive/Images/ISIIS/RAW/20240206_RachelCarson/2024-02-06 10-00-17.043/" \
        --output "/mnt/DeepSea-AI/data/ISIIS/20240206_RachelCarson/2024-02-06 10-00-17.043/" \
        --gop 30"

# Transcode CFE ISIIS videos from mov to mp4 for use in Tator from Hawaii
transcode-cfe-isiis-hawaii:
    time just --justfile {{justfile()}} _base_cmd "aipipeline/projects/cfedeploy/avi2mp4.py \
        --input "/mnt/CFElab/Data_archive/Images/ISIIS/RAW/20250401_Hawaii" \
        --output "/mnt/DeepSea-AI/data/ISIIS/20250401_Hawaii" \
        --gop 30"

# Fix off-by-one errors in CFE ISIIS Rachel Carson detections
fix-cfe-isiis-rc-offbyone:
    python3 aipipeline/projects/cfedeploy/simplify_csv.py  /tmp/rc_2024_02_cfe_isiis_dino_v7-20250916.csv -O /tmp/rc_2024_02_cfe_isiis_dino_v7-20250916_S.csv
    cd aipipeline/projects/cfedeploy && ./update_frames /tmp/rc_2024_02_cfe_isiis_dino_v7-20250916.csv -O /tmp/rc_2024_02_cfe_isiis_dino_v7-20250916_S.csv