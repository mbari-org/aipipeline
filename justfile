#!/usr/bin/env just --justfile

# copy the default .env file
## Source the .env file and support an alternative name
set dotenv-load := true
set dotenv-filename := x'${ENV_FILE:-.env}'

# List recipes
list:
    @just --list --unsorted

# Setup the environment
install: update_trackers
    conda run -n aipipeline pip install https://github.com/redis/redis-py/archive/refs/tags/v5.0.9.zip
    git clone http://github.com/mbari-org/aidata.git deps/aidata
    git clone https://github.com/facebookresearch/co-tracker deps/co-tracker
    conda run -n aipipeline pip install -r deps/aidata/requirements.txt
    cd deps/co-tracker && conda run -n aipipeline pip install -e .
    cd .. && mkdir checkpoints && cd checkpoints && wget https://huggingface.co/facebook/cotracker3/resolve/main/scaled_offline.pth

# Copy the default .env file to the project
cp-env:
  @cp .env.mantis .env
# Update the environment. Run this command after checking out any code changes
update_trackers:
    conda env update_trackers --file environment.yml --prune
# Update environment
update-env:
  conda env update --file environment.yml --prune
# Copy core dev code to the project on doris
cp-core:
    cp justfile /Volumes/dcline/code/aipipeline/justfile
    cp requirements.txt /Volumes/dcline/code/aipipeline/requirements.txt
    cp aipipeline/config* /Volumes/dcline/code/aipipeline/aipipeline/
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.log' --exclude='*__pycache__' ./aipipeline/prediction/  /Volumes/dcline/code/aipipeline/aipipeline/prediction/
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.log' --exclude='*__pycache__' ./aipipeline/metrics/  /Volumes/dcline/code/aipipeline/aipipeline/metrics/
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.log' --exclude='*__pycache__' ./aipipeline/db/  /Volumes/dcline/code/aipipeline/aipipeline/db/
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.log' --exclude='*__pycache__' ./aipipeline/engines/  /Volumes/dcline/code/aipipeline/aipipeline/engines/

# Copy cfe dev code to the project on doris
cp-dev-cfe:
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.png' --exclude='*.log' --exclude='*__pycache__' ./aipipeline/projects/cfe/ /Volumes/dcline/code/aipipeline/aipipeline/projects/cfe/
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.png' --exclude='*.log' --exclude='*__pycache__' ./aipipeline/projects/cfedeploy/ /Volumes/dcline/code/aipipeline/aipipeline/projects/cfedeploy/

# Copy planktivore dev code to the project on doris
cp-dev-ptvr:
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.pt*' --exclude='*.log' --exclude='*__pycache__' ./aipipeline/projects/planktivore/ /Volumes/dcline/code/aipipeline/aipipeline/projects/planktivore/

# Copy uav dev code to the project on doris
cp-dev-uav:
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.pt*' --exclude='*.log' --exclude='*__pycache__' ./aipipeline/projects/uav/ /Volumes/dcline/code/aipipeline/aipipeline/projects/uav/

# Copy bio dev code to the project on doris
cp-dev-bio:
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.log' --exclude='*__pycache__' ./aipipeline/projects/bio/ /Volumes/dcline/code/aipipeline/aipipeline/projects/bio/
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.log' --exclude='*__pycache__' ./deps/biotrack/biotrack/ /Volumes/dcline/code/aipipeline/deps/biotrack/biotrack/

# Copy i2map dev code to the project on doris
cp-dev-i2map:
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.log' --exclude='*__pycache__' ./aipipeline/projects/i2map/ /Volumes/dcline/code/aipipeline/aipipeline/projects/i2map/
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.log' --exclude='*__pycache__' ./aipipeline/projects/i2mapbulk/ /Volumes/dcline/code/aipipeline/aipipeline/projects/i2mapbulk/

# Initialize labels for quick lookup, e.g. just init-labels uav 19
init-labels project='uav' leaf_type_id='19':
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/{{project}}
    conda run -n aipipeline python3 aipipeline/prediction/leaf_init.py \
    --config $PROJECT_DIR/config/config.yml \
    --labels $PROJECT_DIR/config/labels.yml  \
    --type-id {{leaf_type_id}}
# Generate a tsne plot of the VSS database
plot-tsne-vss project='uav':
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/{{project}}
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/metrics/plot_tsne_vss.py --config $PROJECT_DIR/config/config.yml

optimize-vss project='uav' *more_args="":
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/{{project}}
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/metrics/optimize_vss.py \
    --config $PROJECT_DIR/config/config.yml \
    {{more_args}}

# Calculate the accuracy of the VSS database; run after download, then optimize
calc-acc-vss project='uav':
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/{{project}}
    export PYTHONPATH=.:/u/mldevops/code/aidata
    time conda run -n aipipeline --no-capture-output python3 aipipeline/metrics/calc_accuracy_vss.py --config $PROJECT_DIR/config/config.yml

# Reset the VSS database, removing all data. Proceed with caution!!
reset-vss-all:
    #!/usr/bin/env bash
    export PYTHONPATH=.
    projects=(uav cfe bio i2map)
    for project in ${projects[@]}; do
      project_dir=./aipipeline/projects/$project
      time conda run -n aipipeline --no-capture-output python3 aipipeline/db/redis/vss/reset.py --config ${project_dir}/config/config.yml
    done

# Reset the VSS database, removing all data. Run before init-vss or when creating the database. Run with e.g. `uav`
reset-vss project='uav':
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/{{project}}
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/db/redis/vss/reset.py --config $PROJECT_DIR/config/config.yml

# Remove an entry from the VSS database, e.g. j remove-vss i2map --doc \'doc:marine organism:\*\'
remove-vss project='uav' *more_args="":
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/{{project}}
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/db/redis/vss/remove.py --config $PROJECT_DIR/config/config.yml {{more_args}}

# Initialize the VSS database for a project
init-vss project='uav' *more_args="":
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/{{project}}
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/db/redis/vss/init_pipeline.py --batch-size 1 --skip-clean True --config $PROJECT_DIR/config/config.yml {{more_args}}

# Load already computed exemplars into the VSS database
load-vss project='uav' :
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/{{project}}
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/db/redis/vss/load_pipeline.py --config $PROJECT_DIR/config/config.yml

# Load cfe ISII mission videos. Run with e.g. just load-cfe-isiis-videos hawaii-video.txt or just load-cfe-isiis-videos rachelcarson-video.txt. Populate files in project/cfedeploy/data first
load-cfe-isiis-videos missions="":
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/cfedeploy
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 $PROJECT_DIR/load_isiis_video_pipeline.py \
    --missions $PROJECT_DIR/data/{{missions}} \
    --config $PROJECT_DIR/config/config.yml

# Load cfe ISII mission detections/clusters. Run with e.g. just load-cfe-isiis-sdcat /mnt/CFElab/Data_analysis/ISIIS/20240206_RachelCarson_detections/det_filtered/csv/ 14
load-cfe-isiis-sdcat data_dir="" stride="14" version="Baseline":
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/cfedeploy
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 $PROJECT_DIR/load_isiis_sdcat_pipeline.py \
    --data {{data_dir}} --stride {{stride}}  --label Unknown  --version {{version}} \
    --config $PROJECT_DIR/config/config.yml

# Cluster CFE ISIIS hawaii mission frames. Cleans first, then clusters
cluster-cfe-isiis roi_dir="/mnt/ML_SCRATCH/cfe/Hawaii_detections/det_filtered_reduction/crops/" save_dir="/mnt/ML_SCRATCH/cfe/Hawaii_detections/det_filtered_reduction/cluster/ ":
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/cfedeploy
    export PYTHONPATH=.
    echo "Running clean pipeline"
    time conda run -n aipipeline --no-capture-output python3 \
                            aipipeline/prediction/clean_pipeline.py \
                            --config $PROJECT_DIR/config/config.yml \
                            --image-dir {{roi_dir}}

# Cluster CFE ISIIS hawaii mission frames. First pass with trained local model
cluster-cfe-isiis-hawaii-p1:
    #!/usr/bin/env bash
    conda activate rapids-25.04
    export PROJECT_DIR=./aipipeline/projects/cfedeploy
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
    export PROJECT_DIR=./aipipeline/projects/cfedeploy
    export PYTHONPATH=.
    export RAY_TMPDIR=/mnt/ML_SCRATCH/ray/
    export MPLCONFIGDIR=/mnt/ML_SCRATCH/matplotlib
    # Run the first pass clustering with the local model
    sdcat cluster detections \
    --det-dir {{p1_dir}} \
    --save-dir /mnt/ML_SCRATCH/cfe/Hawaii_detections/det_filtered_reduction \
    --config-ini $PROJECT_DIR/config/sdcat_fb_dino-vits8.ini \
    --vits-batch-size 512 \
    --hdbscan-batch-size 50000 \
    --device cuda \
    --use-vits

# Load planktivore ROI images, e.g. just load-ptvr-images /mnt/DeepSea-AI/data/Planktivore/raw/aidata-export-02 --section aidata-export-02
load-ptvr-images images='tmp/roi' *more_args="":
    time aidata load images \
    --config ./aipipeline/projects/planktivore/config/config.yml \
    --input {{images}} \
    --token $TATOR_TOKEN \
    --dry-run {{more_args}}

# Cluster planktivore ROI images
cluster-ptvr-images *more_args="":
    time conda run -n aipipeline --no-capture-output sdcat cluster roi \
    --config-ini ./aipipeline/projects/planktivore/config/sdcat.ini \
    --device cuda:1 {{more_args}}

# Load planktivore ROI clusters, e.g. just load-ptvr-clusters aidata-export-03-low-mag tmp/roi/cluster.csv
load-ptvr-clusters clusters='tmp/roi/cluster.csv' *more_args="":
  cp {{clusters}} test.csv
  sed -i 's|/mnt/ML_SCRATCH/Planktivore/aidata-export-03-low-mag-square/|/mnt/DeepSea-AI/data/Planktivore/cluster/raw/aidata-export-03-low-mag/|g' test.csv
  time conda run -n aipipeline --no-capture-output aidata load boxes \
        --config ./aipipeline/projects/planktivore/config/config_lowmag.yml \
        --input test.csv \
        --token $TATOR_TOKEN {{more_args}}

# Rescale planktivore ROI images, e.g. just rescale-ptvr-images aidata-export-03-low-mag
rescale-ifcb-images collection="2014":
    time conda run -n aipipeline --no-capture-output python ./aipipeline/projects/cfe/adjust_roi_ifcb.py \
    --input_dir /mnt/ML_SCRATCH/ifcb/raw/{{collection}} \
    --output_dir /mnt/ML_SCRATCH/ifcb/raw/{{collection}}-square/crops
    time conda run -n aipipeline --no-capture-output python ./aipipeline/projects/cfe/gen_ifcb_stats.py \
    --input_dir /mnt/ML_SCRATCH/ifcb/raw/{{collection}}-square/crops

# Rescale planktivore ROI images, e.g. just rescale-ptvr-images aidata-export-03-low-mag
rescale-ptvr-images collection="aidata-export-03-low-mag":
    time conda run -n aipipeline --no-capture-output python ./aipipeline/projects/planktivore/adjust_roi.py \
    --input_dir /mnt/DeepSea-AI/data/Planktivore/raw/{{collection}} \
    --output_dir /mnt/DeepSea-AI/data/Planktivore/raw/{{collection}}-square

# Download and rescale planktivore ROI images, e.g. just download-rescale-ptvr-images aidata-export-03-low-mag
download-rescale-ptvr-images collection="aidata-export-03-low-mag":
    time conda run -n aipipeline --no-capture-output python aipipeline/prediction/download_pipeline.py \
        --config ./aipipeline/projects/planktivore/config/{{collection}}.yml
    just --justfile {{justfile()}} rescale-ptvr-images {{collection}}

# Cluster mission in aipipeline/projects/uav/data/hawaii-video.txt
cluster-uav *more_args="":
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/uav
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 $PROJECT_DIR/cluster_pipeline.py \
    --missions $PROJECT_DIR/data/missions-to-process.txt \
    --config $PROJECT_DIR/config/config.yml \
    {{more_args}}

# Detect mission in aipipeline/projects/uav/data/hawaii-video.txt
detect-uav *more_args="":
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/uav
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 $PROJECT_DIR/detect_pipeline.py \
    --missions $PROJECT_DIR/data/missions-to-process.txt \
    --config $PROJECT_DIR/config/config.yml \
    {{more_args}}

# Detect mission data in aipipeline/projects/uav/data/hawaii-video.txt
detect-uav-test:
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/uav
    export TEST_DIR=./test/projects/uav
    export PYTHONPATH=.
    echo $TEST_DIR/data/trinity-2_20240702T162557_Seacliff/SONY_DSC-RX1RM2 > $TEST_DIR/data/hawaii-video.txt
    time conda run -n aipipeline --no-capture-output python3 $PROJECT_DIR/detect_pipeline.py \
    --missions $TEST_DIR/data/hawaii-video.txt \
    --config $TEST_DIR/config/config_macos.yml

# Load uav mission images in aipipeline/projects/uav/data/hawaii-video.txt
load-uav-images:
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/uav
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 $PROJECT_DIR/load_image_pipeline.py \
    --missions $PROJECT_DIR/data/hawaii-video.txt \
    --config $PROJECT_DIR/config/config.yml

# Load uav detections/clusters in aipipeline/projects/uav/data/hawaii-video.txt
load-uav type="cluster":
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/uav
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 $PROJECT_DIR/load_sdcat_pipeline.py \
    --missions $PROJECT_DIR/data/missions-to-process.txt \
    --config $PROJECT_DIR/config/config.yml \
    --type {{type}}

# Fix UAV metadata lat/lon/alt
fix-uav-metadata:
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/uav
    export PYTHONPATH=.:deps/aidata
    time conda run -n aipipeline --no-capture-output python3 $PROJECT_DIR/fix_metadata.py

# Compute saliency for downloaded VOC data and update_trackers the Tator database
compute-saliency project='uav' *more_args="":
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/{{project}}
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/prediction/saliency_pipeline.py \
    --config $PROJECT_DIR/config/config.yml \
    {{more_args}}

# Crop detections from VOC formatted downloads
crop project='uav' *more_args="":
    #!/usr/bin/env bash
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/prediction/crop_pipeline.py \
        --config ./aipipeline/projects/{{project}}/config/config.yml \
        {{more_args}}

# Download and crop with defaults for project e.g. download-crop i2map
download-crop project='uav' *more_args="":
    #!/usr/bin/env bash
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/db/tator/download_crop_pipeline.py \
        --config ./aipipeline/projects/{{project}}/config/config.yml \
        {{more_args}}

# Download only
download project='uav':
    #!/usr/bin/env bash
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/db/tator/download_crop_pipeline.py \
        --config ./aipipeline/projects/{{project}}/config/config.yml

# Cluster only
cluster project='uav' *more_args="":
    #!/usr/bin/env bash
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/db/tator/download_crop_pipeline.py \
        --config ./aipipeline/projects/{{project}}/config/config.yml \
        {{more_args}}
# Predict images using the VSS database
predict-vss project='uav' image_dir='/tmp/download' *more_args="":
    #!/usr/bin/env bash
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/db/redis/vss/predict_load_pipeline.py \
    --config ./aipipeline/projects/{{project}}/config/config.yml \
    --image-dir {{image_dir}} \
    {{more_args}}

# Predict and save using the VSS database
predict-vss-save project='planktivore' *more_args="--output-csv /tmp/predict-vss.csv --batch-size 64 --resize":
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/{{project}}
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/db/redis/vss/predict_save_pipeline.py \
    --config $PROJECT_DIR/config/config.yml {{more_args}}

# Predict velella test images using the VSS database and save the results
predict-vss-velella:
    just --justfile {{justfile()}} predict-vss-save planktivore --resize --batch-size 64 \
    --output-csv /tmp/predict-vss-velella.csv \
    --input  /mnt/ML_SCRATCH/Planktivore/lowmag/mbari-ifcb2014-vitb16-20250318_20250320_002422/crops/

# Run the strided inference on a collection of videos in a TSV file
run-ctenoA-prod:
    #!/usr/bin/env bash
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/projects/bio/cluster.py \
    --config ./aipipeline/projects/bio/config/config.yml \
    --class_name "Ctenophora sp. A" \
    --endpoint-url "http://fastap-fasta-0riu3xafmhua-337062127.us-west-2.elb.amazonaws.com/predict" \
    --tsv ./aipipeline/projects/bio/data/videotable.tsv

# Run the mega strided inference only on a single video
run-mega-inference:
    #!/usr/bin/env bash
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/projects/bio/cluster.py \
    --config ./aipipeline/projects/bio/config/config.yml \
    --class_name "animal" \
    --class-remap "{\"animal\":\"marine organism\"}" \
    --flush \
    --skip-vss \
    --skip-load \
    --remove-vignette \
    --min-confidence 0.2 \
    --max-seconds 300 \
    --stride 1 \
    --endpoint_url http://FastAP-FastA-0RIu3xAfMhUa-337062127.us-west-2.elb.amazonaws.com/predict \
    --video /mnt/M3/mezzanine/Ventana/2020/12/4318/V4318_20201208T203419Z_h264.mp4

# Run the mega strided pipeline on a videos in a dive for the bio project
run-mega-stride-bio video='/mnt/M3/mezzanine/Ventana/2023/10/4505/V4505_20231019T180422Z_h265.mp4':
    #!/usr/bin/env bash
    export PYTHONPATH=deps:deps/biotrack:.
    export MPLCONFIGDIR=/tmp
    time conda run -n aipipeline --no-capture-output python3 aipipeline/projects/bio/process_video_pipeline.py \
    --config ./aipipeline/projects/bio/config/config.yml \
    --skip-track --min-score-det 0.01 --batch-size 1 --min-score-track 0.05 --min-frames 0 --min-depth 200 --max-depth 2000 --version ctenophora-sp-a-mega-vits \
    --vits-model /mnt/DeepSea-AI/models/bio/mbari-m3ctnA-vits-b16-20250331 \
    --class-name "Ctenophora sp. A" \
    --det-model /mnt/DeepSea-AI/models/midwater/megadetrt-yolov5 \
    --stride 60 --video '{{video}}'

#./models/mbari_452k_yolov10
# Run the mega strided tracking pipeline on an entire dive for the bio project
run-mega-track-bio video='/mnt/M3/mezzanine/Ventana/2022/09/4432/*.mp4':
    #!/usr/bin/env bash
    export PYTHONPATH=deps:deps/biotrack:.
    export MPLCONFIGDIR=/tmp
    #DIRECTORY=/mnt/M3/mezzanine/Ventana/2022/09/4432/
    #DIRECTORY=/mnt/M3/mezzanine/DocRicketts/2015/03/720/
    #DIRECTORY=/mnt/M3/mezzanine/Ventana/2022/10/4433
    #DIRECTORY=/mnt/M3/mezzanine/Ventana/2022/09/4431
    #DIRECTORY=/mnt/M3/mezzanine/DocRicketts/2022/05/1443
    #DIRECTORY=/mnt/M3/mezzanine/DocRicketts/2022/05/1443
    #DIRECTORY=/mnt/M3/mezzanine/Ventana/2020/12/4315
    time conda run -n aipipeline --no-capture-output python3 aipipeline/projects/bio/process_video_pipeline.py \
       --config ./aipipeline/projects/bio/config/config.yml \
       --max-frames-tracked 200 --min-score-det 0.1 --batch-size 34 --min-score-track 0.1 --min-frames 5 --version mega-vits-track-gcam \
       --vits-model /mnt/DeepSea-AI/models/m3midwater-vit-b-16 \
       --det-model /mnt/DeepSea-AI/models/midwater/megadetrt-yolov5 \
       --stride 16 --video '{{video}}'

# Run the mega strided pipeline on a single video or entire dive for the i2map project
#run-mega-stride-i2map video='/mnt/M3/mezzanine/Ventana/2023/10/4505/*.mp4':
run-mega-stride-i2map video='/mnt/DeepSea-AI/data/i2MAP/2025/04/i2MAP_20250402T172257Z_301m_F031_5.mp4' vit_model='/mnt/DeepSea-AI/models/bio/mbari-i2map-vits-b-8-20250216' version='megadetrt-mbari-i2map-vits-b-8-20250216':
    #!/usr/bin/env bash
    export PYTHONPATH=deps:deps/biotrack:.
    export MPLCONFIGDIR=/tmp
    time conda run -n aipipeline --no-capture-output python3 aipipeline/projects/bio/process_video_pipeline.py \
    --config ./aipipeline/projects/i2map/config/config.yml \
    --skip-track --min-score-det 0.01 --batch-size 0 --min-score-track 0.3 --min-frames 0 \
    --version {{version}} \
    --vits-model {{vit_model}} \
    --det-model /mnt/DeepSea-AI/models/midwater/megadetrt-yolov5 \
    --stride 30 --video '{{video}}'

# Run the mega track pipeline on a single video or entire dive for the i2map project
#run-mega-stride-i2map video='/mnt/M3/mezzanine/Ventana/2023/10/4505/*.mp4':
run-mega-track-i2map video='/mnt/DeepSea-AI/data/i2MAP/2025/04/i2MAP_20250402T172257Z_301m_F031_5.mp4' vit_model='/mnt/DeepSea-AI/models/bio/mbari-i2map-vits-b-8-20250216' version='megadetrt-mbari-i2map-vits-b-8-20250216-track':
    #!/usr/bin/env bash
    export PYTHONPATH=deps:deps/biotrack:.
    export MPLCONFIGDIR=/tmp
    time conda run -n aipipeline --no-capture-output python3 aipipeline/projects/bio/process_video_pipeline.py \
    --config ./aipipeline/projects/i2map/config/config.yml \
    --max-frames-tracked 300 --min-score-det 0.01 --batch-size 16 --min-score-track 0.1 --min-frames 2 \
    --version {{version}} \
    --vits-model {{vit_model}} \
    --det-model /mnt/DeepSea-AI/models/midwater/megadetrt-yolov5 \
    --stride 1 --video '{{video}}'
     #--save-cotrack-video

# Run the mega strided tracking pipeline on a single video to test the pipeline
run-mega-track-test-1min:
    #!/usr/bin/env bash
    export PYTHONPATH=.:/Users/dcline/Dropbox/code/biotrack:.
    time python3 aipipeline/projects/bio/predict.py \
     --config ./aipipeline/projects/bio/config/config.yml \
     --det-model /mnt/DeepSea-AI/models/midwater/megadet \
     --vits-model /mnt/DeepSea-AI/models/m3midwater-vit-b-16 \
     --max-frames-tracked 200 --min-score-det 0.0002 --min-score-track 0.5 --min-frames 5 --version mega-vits-track-gcam \
     --stride 8 --max-seconds 60 --imshow --skip-load  \
     --video aipipeline/projects/bio/data/V4361_20211006T163256Z_h265_1min.mp4

# Run the mega strided tracking pipeline on a single video for the bio project with FastAPI
run-mega-track-test-fastapiyv5:
    #!/usr/bin/env bash
    export PYTHONPATH=.:/Users/dcline/Dropbox/code/biotrack:.
    time python3 aipipeline/projects/bio/predict.py \
     --config ./aipipeline/projects/bio/config/config.yml \
     --vits-model /mnt/DeepSea-AI/models/m3midwater-vit-b-16 \
     --max-frames-tracked 200 --min-score-det 0.0002 --min-score-track 0.5 --min-frames 5 --version mega-vits-track-gcam \
     --stride 15 --max-seconds 60 --imshow --skip-load  \
     --endpoint-url http://FastAP-FastA-0RIu3xAfMhUa-337062127.us-west-2.elb.amazonaws.com/predict \
     --video aipipeline/projects/bio/data/V4361_20211006T163256Z_h265_1min.mp4

# Run the mega strided tracking pipeline on a single video for the cfe project
run-mega-track-isiis-video video='/mnt/CFElab/Data_archive/Images/ISIIS/COOK/VideosMP4/20250401_Hawaii/20250405_scuba/2025-04-05 10-07-06.063/CFE_ISIIS-001-2025-04-05 10-07-06.063.mp4':
    #!/usr/bin/env bash
    export PYTHONPATH=.:deps/biotrack:.
    time python3 aipipeline/projects/bio/process_video_pipeline.py \
     --det-model /mnt/DeepSea-AI/models/midwater/megadetrt-yolov5 \
     --config ./aipipeline/projects/cfe/config/config.yml \
     --vits-model /mnt/DeepSea-AI/models/i2MAP/mbari-i2map-vits-b-8-20250216 \
     --max-frames-tracked 300 --min-score-det 0.01 --min-score-track 0.01 --min-frames 2 --version metadetrt-vits-track-ft \
     --stride 1 --skip-load --batch-size 30 --create-video --max-seconds 1 \
     --video '{{video}}'

# Run inference and cluster on i2MAP bulk data run with ENV_FILE=.env.i2map just cluster-i2mapbulk
cluster-i2mapbulk:
    #!/usr/bin/env bash
    export PYTHONPATH=.
    export MPLCONFIGDIR=/tmp
    time conda run -n aipipeline --no-capture-output python3 aipipeline/db/tator/download_crop_pipeline.py \
    --config ./aipipeline/projects/i2mapbulk/config/config_unknown.yml \
    --data aipipeline/projects/i2mapbulk/data/bydepth.txt

# Download and cluster data. Run with  just download-cluster i2map or just download-cluster megart-mbari-i2map-vits-b-8-2025 to cluster a particular version
download-cluster project="i2map" version="Baseline" *more_args="":
    just --justfile {{justfile()}} download-crop {{project}} --version {{version}} {{more_args}}
    echo "/mnt/ML_SCRATCH/{{project}}/{{version}}/crops/,/mnt/ML_SCRATCH/{{project}}/{{version}}/clusters/" > /tmp/{{version}}-clu.txt
    just --justfile {{justfile()}} cluster {{project}} --version {{version}} --data /tmp/{{version}}-clu.txt

# Run vss search  to planktivore data
vss-search-ptvr image_dir="":
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/planktivore
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
    if [ ! -f $image_listing ]; then
        echo "Finding images in {{image_dir}}"
        find {{image_dir}} -name '*.jpg' > $image_listing
    else
        echo "Using existing file $image_listing"
    fi
    time conda run -n aipipeline --no-capture-output python3 $PROJECT_DIR/vss_search_pipeline.py --config $PROJECT_DIR/config/config.yml  --image_list $image_listing
# Run sweep for planktivore data. Example just cluster-ptvr-swp /mnt/ML_SCRATCH/Planktivore/aidata-export-03-low-mag-square /mnt/ML_SCRATCH/Planktivore/cluster/aidata-export-03-low-mag-square
cluster-ptvr-sweep roi_dir='/mnt/ML_SCRATCH/Planktivore/aidata-export-03-low-mag-square' save_dir='/mnt/ML_SCRATCH/Planktivore/cluster/aidata-export-03-low-mag-square' device='cuda':
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/planktivore
    export PYTHONPATH=.
    echo "Running clean pipeline"
    time conda run -n aipipeline --no-capture-output python3 \
                            aipipeline/prediction/clean_pipeline.py \
                            --config $PROJECT_DIR/config/config.yml \
                            --image-dir {{roi_dir}}
    for min_sample in 2; do
        for min_cluster in 3 5 7 20; do
          echo "Running alpha=1 min_sample=$min_sample min_cluster=$min_cluster"
            time conda run -n rapids-25.04 sdcat cluster roi --config-ini $PROJECT_DIR/config/sdcat.ini \
                    --roi-dir {{roi_dir}} \
                    --save-dir {{save_dir}} \
                    --alpha 1 \
                    --min-sample-size $min_sample \
                    --min-cluster-size $min_cluster \
                    --device {{device}} \
                    --use-vits \
                    --vits-batch-size 512 \
                    --hdbscan-batch-size 50000
            done
    done
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
# Load i2MAP bulk data run with ENV_FILE=.env.i2map just load-i2mapbulk <path to the cluster_detections.csv file>
load-i2mapbulk data='data':
    #!/usr/bin/env bash
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/projects/i2mapbulk/load_pipeline.py \
    --config ./aipipeline/projects/i2mapbulk/config/config_unknown.yml --data {{data}}

# Load clusters for any project, e.g. just update-cluster uav /mnt/ML_SCRATCH/UAV/2024-10-19/cluster.csv. Assumes images/boxes for the project are already loaded
load-cluster project="uav" data='data' version="Baseline" *more_args="":
    time conda run -n aipipeline --no-capture-output aidata load clusters \
        --config ./aipipeline/projects/{{project}}/config/config.yml \
        --input {{data}} --version {{version}} \
        --token $TATOR_TOKEN {{more_args}}

# Download i2mpabulk unlabeled data run with ENV_FILE=.env.i2map just download-i2mapbulk-unlabeled
download-i2mapbulk-unlabeled:
    just --justfile {{justfile()}} download-crop i2mapbulk --config ./aipipeline/projects/i2mapbulk/config/config_unknown.yml --download-args "'--unverified'"

# Replace m3 urls with mantis
replace-m3-urls:
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/bio
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 ./aipipeline/projects/bio/maintenance/replace_tm3.py

# Generate training data for the bio project
gen-bio-data image_dir="":
    #!/usr/bin/env bash
    export PYTHONPATH=.
    just --justfile {{justfile()}} download-crop bio --skip-clean True --gen-multicrop --verified
    time conda run -n aipipeline --no-capture-output python3 aipipeline/prediction/clean_pipeline.py \
        --config ./aipipeline/projects/bio/config/config.yml --image-dir /mnt/ML_SCRATCH/901103-biodiversity/crops
    time conda run -n aipipeline --no-capture-output python3 aipipeline/prediction/clean_pipeline.py \
        --config ./aipipeline/projects/bio/config/config.yml --image-dir /mnt/ML_SCRATCH/M3/crops

# Generate training data for the CFE project
gen-cfe-data:
  just --justfile {{justfile()}} download-crop cfe --clean --gen-multicrop --data.download_args "'--verified'"

# Generate training data for the i2map project
gen-i2map-data:
  just --justfile {{justfile()}} download-crop i2map --clean --use-cleanvision True --data.download_args "'--version Baseline  --generator vars-labelbot --group NMS'"

# Generate training data for the i2map project from the bulk server, run with ENV_FILE=.env.i2map just gen-i2mapbulk-data
gen-i2mapbulk-data:
  just --justfile {{justfile()}} download-crop i2mapbulk --clean --use-cleanvision True --gen-multicrop --data.download_args "'--verified'"

# Generate training data for the uav project
gen-uav-data:
  just --justfile {{justfile()}} download-crop uav --clean --gen-multicrop --data.download_args "'--verified --version yolo11x-oneclass-uav-vits-b-8-20250202'"

# Generate training data stats
gen-stats-csv project='UAV' data='/mnt/ML_SCRATCH/UAV/':
    #!/usr/bin/env bash
    export PYTHONPATH=.
    time conda run -n aipipeline python3 aipipeline/prediction/gen_stats.py --data {{data}} --prefix {{project}}

# Generate training data for the planktivore low mag
gen-ptvr-lowmag-data:
  just --justfile {{justfile()}} download-crop planktivore --clean --gen-multicrop --data.processed_path /mnt/ML_SCRATCH/Planktivore/velella --data.download_args "'--verified --section Velella-low-mag --version Baseline'"
  just --justfile {{justfile()}} download-crop planktivore --clean --gen-multicrop --data.processed_path /mnt/ML_SCRATCH/Planktivore/lowmag --data.download_args "'--verified --section aidata-export-03-low-mag --version mbari-ifcb2014-vitb16-20250318_20250320_002422'"

# Initialize the VSS database for the planktivore low mag data
init-ptvr-lowmag-vss:
  just --justfile {{justfile()}} init-vss planktivore --data.processed_path /mnt/ML_SCRATCH/Planktivore/velella --data.download_args "'--verified --section Velella-low-mag --version Baseline'"
  just --justfile {{justfile()}} init-vss planktivore --data.processed_path /mnt/ML_SCRATCH/Planktivore/lowmag --data.download_args "'--verified --section aidata-export-03-low-mag --version mbari-ifcb2014-vitb16-20250318_20250320_002422'"

# Transcode i2MAP videos from mov to mp4 for use in Tator
transcode-i2map:
    aipipeline/projects/i2map/mov2mp4.sh
# Transcode CFE ISIIS videos from mov to mp4 for use in Tator from Rachel Carson
transcode-cfe-isiis-rc:
    time conda run -n aipipeline --no-capture-output python3 aipipeline/projects/cfedeploy/mov2mp4.py \
    --input "/mnt/CFElab/Data_archive/Images/ISIIS/RAW/20240206_RachelCarson/2024-02-06 10-00-17.043/" \
    --output "/mnt/DeepSea-AI/data/ISIIS/20240206_RachelCarson/2024-02-06 10-00-17.043/" \
    --gop 30
# Transcode CFE ISIIS videos from mov to mp4 for use in Tator from Hawaii
transcode-cfe-isiis-hawaii:
    time conda run -n aipipeline --no-capture-output python3 aipipeline/projects/cfedeploy/avi2mp4.py \
    --input "/mnt/CFElab/Data_archive/Images/ISIIS/RAW/20250401_Hawaii" \
    --output "/mnt/DeepSea-AI/data/ISIIS/20250401_Hawaii" \
    --gop 30