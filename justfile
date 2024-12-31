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


# Copy core dev code to the project on doris
cp-core:
    cp ./aipipeline/prediction/*.py /Volumes/dcline/code/aipipeline/aipipeline/prediction/
    cp ./aipipeline/metrics/*.py /Volumes/dcline/code/aipipeline/aipipeline/metrics/
    cp justfile /Volumes/dcline/code/aipipeline/justfile

# Copy uav dev code to the project on doris
cp-dev-uav:
    cp ./aipipeline/projects/uav/*.py /Volumes/dcline/code/aipipeline/aipipeline/projects/uav/
    cp ./aipipeline/projects/uav/config/* /Volumes/dcline/code/aipipeline/aipipeline/projects/uav/config/

# Copy bio dev code to the project on doris
cp-dev-bio:
    cp ./aipipeline/projects/bio/*.py /Volumes/dcline/code/aipipeline/aipipeline/projects/bio/
    cp ./aipipeline/projects/bio/config/ /Volumes/dcline/code/aipipeline/aipipeline/projects/bio/config/
    cp ./aipipeline/projects/bio/model/*.py /Volumes/dcline/code/aipipeline/aipipeline/projects/bio/model/

# Copy i2map dev code to the project on doris
cp-dev-i2map:
    cp ./aipipeline/projects/i2map/config/* /Volumes/dcline/code/aipipeline/aipipeline/projects/i2map/config/
    cp ./aipipeline/projects/i2mapbulk/config/* /Volumes/dcline/code/aipipeline/aipipeline/projects/i2mapbulk/config/

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
      time conda run -n aipipeline --no-capture-output python3 aipipeline/prediction/vss_reset.py --config ${project_dir}/config/config.yml
    done

# Reset the VSS database, removing all data. Run before init-vss or when creating the database. Run with e.g. `uav`
reset-vss project='uav':
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/{{project}}
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/prediction/vss_reset.py --config $PROJECT_DIR/config/config.yml

# Remove an entry from the VSS database, e.g. j remove-vss i2map --doc \'doc:marine organism:\*\'
remove-vss project='uav' *more_args="":
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/{{project}}
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/prediction/vss_remove.py --config $PROJECT_DIR/config/config.yml {{more_args}}

# Initialize the VSS database for a project
init-vss project='uav' *more_args="":
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/{{project}}
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/prediction/vss_init_pipeline.py --batch-size 1 --config $PROJECT_DIR/config/config.yml {{more_args}}

# Load already computed exemplars into the VSS database
load-vss project='uav' :
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/{{project}}
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/prediction/vss_load_pipeline.py --config $PROJECT_DIR/config/config.yml

# Load cfe ISII mission videos in aipipeline/project/cfe/data/missions-to-process.txt
load-cfe-isiis-videos *more_args="":
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/cfe
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 $PROJECT_DIR/load_isiis_video_pipeline.py \
    --missions $PROJECT_DIR/data/missions-to-process.txt \
    --config $PROJECT_DIR/config/config.yml \
    {{more_args}}
# Cluster mission in aipipeline/projects/uav/data/missions-to-process.txt
cluster-uav *more_args="":
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/uav
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 $PROJECT_DIR/cluster_pipeline.py \
    --missions $PROJECT_DIR/data/missions2process.txt \
    --config $PROJECT_DIR/config/config.yml \
    {{more_args}}

# Detect mission in aipipeline/projects/uav/data/missions-to-process.txt
detect-uav *more_args="":
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/uav
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 $PROJECT_DIR/detect_pipeline.py \
    --missions $PROJECT_DIR/data/missions2process.txt \
    --config $PROJECT_DIR/config/config.yml \
    {{more_args}}

# Detect mission data in aipipeline/projects/uav/data/missions-to-process.txt
detect-uav-test:
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/uav
    export TEST_DIR=./test/projects/uav
    export PYTHONPATH=.
    echo $TEST_DIR/data/trinity-2_20240702T162557_Seacliff/SONY_DSC-RX1RM2 > $TEST_DIR/data/missions-to-process.txt
    time conda run -n aipipeline --no-capture-output python3 $PROJECT_DIR/detect_pipeline.py \
    --missions $TEST_DIR/data/missions-to-process.txt \
    --config $TEST_DIR/config/config_macos.yml

# Load uav mission images in aipipeline/projects/uav/data/missions-to-process.txt
load-uav-images:
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/uav
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 $PROJECT_DIR/load_image_pipeline.py \
    --missions $PROJECT_DIR/data/missions-to-process.txt \
    --config $PROJECT_DIR/config/config.yml

# Load uav detections/clusters in aipipeline/projects/uav/data/missions-to-process.txt
load-uav type="cluster":
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/uav
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 $PROJECT_DIR/load_sdcat_pipeline.py \
    --missions $PROJECT_DIR/data/missions2process.txt \
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

# Download and crop 
download-crop project='uav' *more_args="":
    #!/usr/bin/env bash
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/prediction/download_crop_pipeline.py \
        --config ./aipipeline/projects/{{project}}/config/config.yml \
        {{more_args}}

# Download only
download project='uav':
    #!/usr/bin/env bash
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/prediction/download_pipeline.py \
        --config ./aipipeline/projects/{{project}}/config/config.yml

# Predict images using the VSS database
predict-vss project='uav' image_dir='/tmp/download' *more_args="":
    #!/usr/bin/env bash
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/prediction/vss_predict_pipeline.py \
    --config ./aipipeline/projects/{{project}}/config/config.yml \
    --image-dir {{image_dir}} \
    {{more_args}}

# Run the strided inference on a single video
run-ctenoA-test:
    #!/usr/bin/env bash
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/projects/bio/process.py \
    --config ./aipipeline/projects/bio/config/config.yml \
    --class_name "Ctenophora sp. A" \
    --endpoint-url "http://localhost:8001/predict" \
    --video http://m3.shore.mbari.org/videos/M3/mezzanine/DocRicketts/2022/05/1443/D1443_20220529T135615Z_h265.mp4

# Run the strided inference on a collection of videos in a TSV file
run-ctenoA-prod:
    #!/usr/bin/env bash
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/projects/bio/process.py \
    --config ./aipipeline/projects/bio/config/config.yml \
    --class_name "Ctenophora sp. A" \
    --endpoint-url "http://fastap-fasta-0riu3xafmhua-337062127.us-west-2.elb.amazonaws.com/predict" \
    --tsv ./aipipeline/projects/bio/data/videotable.tsv

# Run the mega strided inference only on a single video
run-mega-inference:
    #!/usr/bin/env bash
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/projects/bio/process.py \
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

# Run the mega strided tracking pipeline on a single video for the bio project for 30 seconds
run-mega-track-bio-video video='/mnt/M3/mezzanine/Ventana/2022/09/4432/V4432_20220914T210637Z_h264.mp4' gpu_id='0':
    #!/usr/bin/env bash
    export PYTHONPATH=deps:deps/biotrack:.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/projects/bio/process.py \
       --config ./aipipeline/projects/bio/config/config.yml \
       --max-frames-tracked 200 --min-score-det 0.1 --min-score-track 0.1 --batch-size 15 --min-frames 10 --version delme \
       --vits-model /mnt/DeepSea-AI/models/m3midwater-vit-b-16 \
       --det-model /mnt/DeepSea-AI/models/megadet \
       --stride-fps 1 --video {{video}} --max-seconds 10 --flush --gpu-id {{gpu_id}}

# Run the mega strided tracking pipeline on an entire dive for the bio project
run-mega-track-bio-dive dive='/mnt/M3/mezzanine/Ventana/2022/09/4432' gpu_id='0':
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
    process_file() { 
     local video="$1"
     echo "Processing $video"
     time conda run -n aipipeline --no-capture-output python3 aipipeline/projects/bio/process.py \
       --config ./aipipeline/projects/bio/config/config.yml \
       --max-frames-tracked 200 --min-score-det 0.1 --batch-size 34 --min-score-track 0.1 --min-frames 5 --version mega-vits-track-gcam \
       --vits-model /mnt/DeepSea-AI/models/m3midwater-vit-b-16 \
       --det-model /mnt/DeepSea-AI/models/megadet \
       --stride 16 --video $video --gpu-id {{gpu_id}}
     } 
    export -f process_file
    # Run 1 video in parallel
    find  "{{dive}}" -name '*.m*' ! -name "._*.m*" -type f | xargs -P 1 -n 1 -I {} bash -c 'process_file "{}"'

# Run the mega strided tracking pipeline on a single video for the i2map project
run-mega-track-i2map-video video='/mnt/M3/master/i2MAP/2019/02/20190204/i2MAP_20190205T102700Z_200m_F031_17.mov' gpu_id='0':
    #!/usr/bin/env bash
    export PYTHONPATH=.:deps/biotrack:.
    time python3 aipipeline/projects/bio/process.py \
     --config ./aipipeline/projects/i2map/config/config.yml \
     --det-model /mnt/DeepSea-AI/models/megadet \
     --vits-model /mnt/DeepSea-AI/models/i2MAP-vit-b-16 \
     --max-frames-tracked 200 --min-score-det 0.0002 --min-score-track 0.5 --min-frames 5 --version megadet-vits-track \
     --stride-fps 15 --max-seconds 60 --imshow --skip-load  \
     --video {{video}} --gpu-id {{gpu_id}}

# Run the mega strided tracking pipeline on a single video to test the pipeline
run-mega-track-test-1min:
    #!/usr/bin/env bash
    export PYTHONPATH=.:/Users/dcline/Dropbox/code/biotrack:.
    time python3 aipipeline/projects/bio/predict.py \
     --config ./aipipeline/projects/bio/config/config.yml \
     --det-model /Volumes/DeepSea-AI/models/megadet \
     --vits-model /Volumes/DeepSea-AI/models/m3midwater-vit-b-16 \
     --max-frames-tracked 200 --min-score-det 0.0002 --min-score-track 0.5 --min-frames 5 --version mega-vits-track-gcam \
     --stride-fps 15 --max-seconds 60 --imshow --skip-load  \
     --video aipipeline/projects/bio/data/V4361_20211006T163256Z_h265_1min.mp4

run-mega-track-test-fastapiyv5:
    #!/usr/bin/env bash
    export PYTHONPATH=.:/Users/dcline/Dropbox/code/biotrack:.
    time python3 aipipeline/projects/bio/predict.py \
     --config ./aipipeline/projects/bio/config/config.yml \
     --vits-model /Volumes/DeepSea-AI/models/m3midwater-vit-b-16 \
     --max-frames-tracked 200 --min-score-det 0.0002 --min-score-track 0.5 --min-frames 5 --version mega-vits-track-gcam \
     --stride-fps 15 --max-seconds 60 --imshow --skip-load  \
     --endpoint-url http://FastAP-FastA-0RIu3xAfMhUa-337062127.us-west-2.elb.amazonaws.com/predict \
     --video aipipeline/projects/bio/data/V4361_20211006T163256Z_h265_1min.mp4

# Generate training data for the CFE project
gen-cfe-data:
  just --justfile {{justfile()}} download-crop cfe --skip-clean True --version Baseline

# Generate training data for the i2map project
gen-i2map-data:
  just --justfile {{justfile()}} download-crop i2map --version Baseline

# Generate training data for the i2map project from the bulk server, run with ENV_FILE=.env.i2map just gen-i2mapbulk-data
gen-i2mapbulk-data:
  just --justfile {{justfile()}} download-crop i2mapbulk --version Baseline
  just --justfile {{justfile()}} download-crop i2mapbulk --version dino_vits8_20240207_022529

# Generate training data for the uav project
gen-uav-data:
    just --justfile {{justfile()}} download-crop i2map --skip-clean True --version Baseline
    just --justfile {{justfile()}} download-crop i2map --skip-clean True --version yolov5x6-uavs-oneclass-uav-vit-b-16
    just --justfile {{justfile()}} download-crop i2map --skip-clean True --version uav-yolov5-30k

# Generate training data stats
gen-stats-csv project='UAV' data='/mnt/ML_SCRATCH/UAV/':
    #!/usr/bin/env bash
    export PYTHONPATH=.
    time conda run -n aipipeline python3 aipipeline/prediction/gen_stats.py --data {{data}} --prefix {{project}}

