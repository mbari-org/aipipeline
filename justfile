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
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.log' --exclude='*__pycache__' ./aipipeline/prediction/  /Volumes/dcline/code/aipipeline/aipipeline/prediction/
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.log' --exclude='*__pycache__' ./aipipeline/metrics/  /Volumes/dcline/code/aipipeline/aipipeline/metrics/

# Copy cfe dev code to the project on doris
cp-dev-cfe:
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.png' --exclude='*.log' --exclude='*__pycache__' ./aipipeline/projects/cfe/ /Volumes/dcline/code/aipipeline/aipipeline/projects/cfe/

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
# Load planktivore ROI images
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
# Cluster mission in aipipeline/projects/uav/data/missions-to-process.txt
cluster-uav *more_args="":
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/uav
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 $PROJECT_DIR/cluster_pipeline.py \
    --missions $PROJECT_DIR/data/missions-to-process.txt \
    --config $PROJECT_DIR/config/config.yml \
    {{more_args}}

# Detect mission in aipipeline/projects/uav/data/missions-to-process.txt
detect-uav *more_args="":
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/uav
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 $PROJECT_DIR/detect_pipeline.py \
    --missions $PROJECT_DIR/data/missions-to-process.txt \
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

# Download and crop with defaults for project; download with custom args e.g. download-crop i2map --config ./aipipeline/projects/i2map/config/config_unknown.yml
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
    time conda run -n aipipeline --no-capture-output python3 aipipeline/projects/bio/run_strided_infer.py \
    --config ./aipipeline/projects/bio/config/config.yml \
    --class_name "Ctenophora sp. A" \
    --endpoint-url "http://localhost:8001/predict" \
    --video http://m3.shore.mbari.org/videos/M3/mezzanine/DocRicketts/2022/05/1443/D1443_20220529T135615Z_h265.mp4

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

# Run the mega strided tracking pipeline on a single video for the bio project for 30 seconds
run-mega-track-bio-video video='/mnt/M3/mezzanine/Ventana/2022/09/4432/V4432_20220914T210637Z_h264.mp4' gpu_id='0':
    #!/usr/bin/env bash
    export PYTHONPATH=deps:deps/biotrack:.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/projects/bio/process.py \
       --config ./aipipeline/projects/bio/config/config.yml \
       --max-frames-tracked 200 --min-score-det 0.1 --min-score-track 0.1 --batch-size 60 --min-frames 1 --version delme \
       --vits-model /mnt/DeepSea-AI/models/M3/mbari-m3-vits-b-8-20250202/ \
       --det-model /mnt/DeepSea-AI/models/FathomNet/megaladon --skip-load \
       --stride 1 --video {{video}} --max-seconds 1 --flush --gpu-id {{gpu_id}}

# Run the mega strided tracking pipeline on a single video for the bio project for 30 seconds
run-m video='/mnt/M3/mezzanine/Ventana/2022/09/4432/V4432_20220914T210637Z_h264.mp4' gpu_id='0':
    #!/usr/bin/env bash
    export PYTHONPATH=deps:deps/biotrack:.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/projects/bio/process.py \
       --config ./aipipeline/projects/bio/config/config.yml \
       --max-frames-tracked 200 --min-score-det 0.1 --min-score-track 0.1 --batch-size 15 --min-frames 20 --version delme \
       --vits-model /mnt/DeepSea-AI/models/i2MAP/mbari-i2map-m3s-vits-b-8nt-20250216 \
       --det-model /mnt/DeepSea-AI/models/midwater/megadetrt-yolov5 --skip-load --create-video --imshow \
       --stride 4 --video {{video}} --max-seconds 5 --flush --gpu-id {{gpu_id}}

# Run the mega strided pipeline on a videos in a dive for the bio project
run-mega-bio-dive dive='/mnt/M3/mezzanine/Ventana/2023/10/4505/V4505_20231019T180422Z_h265.mp4' gpu_id='0':
    #!/usr/bin/env bash
    export PYTHONPATH=deps:deps/biotrack:.
    export MPLCONFIGDIR=/tmp
    process_file() {
        local video="$1"
        echo "Processing $video"
        time conda run -n aipipeline --no-capture-output python3 aipipeline/projects/bio/process.py \
        --config ./aipipeline/projects/bio/config/config.yml \
        --skip-track --min-score-det 0.1 --batch-size 60 --min-score-track 0.1 --min-frames 0 --min-depth 200 --max-depth 2000 --version ctenophora-sp-a-mega-vits \
        --vits-model /mnt/DeepSea-AI/models/bio/mbari-m3ctnA-vits-b16-20250331 \
        --class-name "Ctenophora sp. A" \
        --det-model /mnt/DeepSea-AI/models/midwater/megadetrt-yolov5 \
        --stride 60 --video $video --gpu-id {{gpu_id}}
        }
    export -f process_file
    find  "{{dive}}" -name '*.m*' ! -name "._*.m*" -type f | xargs -P 1 -n 1 -I {} bash -c 'process_file "{}"'

#./models/mbari_452k_yolov10
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
       --det-model /mnt/DeepSea-AI/models/midwater/megadetrt-yolov5 \
       --stride 16 --video $video --gpu-id {{gpu_id}}
     } 
    export -f process_file
    # Run 1 video in parallel
    find  "{{dive}}" -name '*.m*' ! -name "._*.m*" -type f | xargs -P 1 -n 1 -I {} bash -c 'process_file "{}"'

# Run the mega strided tracking pipeline on a single video for the i2map project
#     --det-model /mnt/DeepSea-AI/models/FathomNet/megalodon/ \
#run-mega-track-i2map-video video='/mnt/M3/master/i2MAP/2019/02/20190204/i2MAP_20190205T102700Z_200m_F031_17.mov' gpu_id='0':
run-mega-track-i2map-video video='/mnt/M3/master/i2MAP/2024/11/20241119/i2MAP_20241119T165914Z_200m_F031_4.mov' gpu_id='0':
    #!/usr/bin/env bash
    export PYTHONPATH=.:deps/biotrack:.
    time python3 aipipeline/projects/bio/process.py \
     --det-model /mnt/DeepSea-AI/models/midwater/megadetrt-yolov5 \
     --config ./aipipeline/projects/i2map/config/config.yml \
     --vits-model /mnt/DeepSea-AI/models/i2MAP/mbari-i2map-vits-b-8-20250216 \
     --max-frames-tracked 200 --min-score-det 0.1 --min-score-track 0.1 --min-frames 2 --version metadetrt-vits-track-ft \
     --stride 1 --skip-load --batch-size 30 --create-video --max-seconds 1 \
     --video {{video}} --gpu-id {{gpu_id}}

# Run the mega strided pipeline on a videos in a dive for the i2map project
run-mega-stride-i2map-dive dive='/mnt/M3/mezzanine/Ventana/2023/10/4505/' gpu_id='0':
    #!/usr/bin/env bash
    export PYTHONPATH=deps:deps/biotrack:.
    export MPLCONFIGDIR=/tmp
    process_file() {
        local video="$1"
        echo "Processing $video"
        time conda run -n aipipeline --no-capture-output python3 aipipeline/projects/bio/process.py \
        --config ./aipipeline/projects/i2map/config/config.yml \
        --skip-track --min-score-det 0.1 --batch-size 60 --min-score-track 0.1 --min-frames 0 --version megadet-vits \
        --vits-model /mnt/DeepSea-AI/models/i2MAP/mbari-i2map-vits-b-8-20250216 \
        --det-model /mnt/DeepSea-AI/models/midwater/megadetrt-yolov5 \
        --stride 120 --video $video --gpu-id {{gpu_id}}
        }
    export -f process_file
    find  "{{dive}}" -name '*.m*' ! -name "._*.m*" -type f | xargs -P 1 -n 1 -I {} bash -c 'process_file "{}"'

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

# Run inference and cluster on i2MAP bulk data run with ENV_FILE=.env.i2map just cluster-i2mapbulk
cluster-i2mapbulk:
    #!/usr/bin/env bash
    export PYTHONPATH=.
    export MPLCONFIGDIR=/tmp
    time conda run -n aipipeline --no-capture-output python3 aipipeline/prediction/cluster_pipeline.py \
    --config ./aipipeline/projects/i2mapbulk/config/config_unknown.yml \
    --data aipipeline/projects/i2mapbulk/data/bydepth.txt

# Run sweep for planktivore data. Example just cluster-ptvr-swp /mnt/ML_SCRATCH/Planktivore/aidata-export-03-low-mag-square /mnt/ML_SCRATCH/Planktivore/cluster/aidata-export-03-low-mag-square
cluster-ptvr-sweep roi_dir='/mnt/ML_SCRATCH/Planktivore/aidata-export-03-low-mag-square' save_dir='/mnt/ML_SCRATCH/Planktivore/cluster/aidata-export-03-low-mag-square' device='cuda:0':
    #!/usr/bin/env bash
    export PYTHONPATH=.
    for alpha in 1.0 1.1; do
        for min_cluster in 2 10; do
          echo "Running alpha=$alpha min_samples=$min_samples min_cluster=$min_cluster"
            just --justfile {{justfile()}} cluster-ptvr-images \
                    --roi-dir {{roi_dir}} \
                    --save-dir {{save_dir}} \
                    --alpha $alpha \
                    --min-sample-size 1 \
                    --min-cluster-size $min_cluster \
                    --device {{device}} \
                    --use-vits
            done
    done
# Load i2MAP bulk data run with ENV_FILE=.env.i2map just load-i2mapbulk <path to the cluster_detections.csv file>
load-i2mapbulk data='data':
    #!/usr/bin/env bash
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/projects/i2mapbulk/load_pipeline.py \
    --config ./aipipeline/projects/i2mapbulk/config/config_unknown.yml --data {{data}}

# Download i2mpabulk unlabeled data run with ENV_FILE=.env.i2map just download-i2mapbulk-unlabeled
download-i2mapbulk-unlabeled:
  just --justfile {{justfile()}} download-crop i2mapbulk --config ./aipipeline/projects/i2mapbulk/config/config_unknown.yml

# Generate training data for the bio project
gen-bio-data image_dir="":
    #!/usr/bin/env bash
    export PYTHONPATH=.
    just --justfile {{justfile()}} download-crop bio --skip-clean True
    time conda run -n aipipeline --no-capture-output python3 aipipeline/prediction/clean_pipeline.py \
        --config ./aipipeline/projects/bio/config/config.yml --image-dir /mnt/ML_SCRATCH/901103-biodiversity/crops
    time conda run -n aipipeline --no-capture-output python3 aipipeline/prediction/clean_pipeline.py \
        --config ./aipipeline/projects/bio/config/config.yml --image-dir /mnt/ML_SCRATCH/M3/crops

# Generate training data for the CFE project
gen-cfe-data:
  just --justfile {{justfile()}} download-crop cfe --skip-clean True

# Generate training data for the i2map project
gen-i2map-data:
  just --justfile {{justfile()}} download-crop i2map --skip-clean True --use-cleanvision True

# Generate training data for the i2map project from the bulk server, run with ENV_FILE=.env.i2map just gen-i2mapbulk-data
gen-i2mapbulk-data:
  just --justfile {{justfile()}} download-crop i2mapbulk --skip-clean True --use-cleanvision True

# Generate training data for the uav project
gen-uav-data:
  just --justfile {{justfile()}} download-crop uav --skip-clean True

# Generate training data stats
gen-stats-csv project='UAV' data='/mnt/ML_SCRATCH/UAV/':
    #!/usr/bin/env bash
    export PYTHONPATH=.
    time conda run -n aipipeline python3 aipipeline/prediction/gen_stats.py --data {{data}} --prefix {{project}}
# Transcode i2MAP videos
transcode-i2map:
    aipipeline/projects/i2map/mov2mp4.sh
