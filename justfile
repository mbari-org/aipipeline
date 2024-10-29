#!/usr/bin/env just --justfile

# Source the .env file
set dotenv-load := true

# List recipes
list:
    @just --list --unsorted

# Setup the environment
install: update
    git submodule update --init --recursive
    conda run -n aipipeline pip install https://github.com/redis/redis-py/archive/refs/tags/v5.0.9.zip
    conda run -n aipipeline pip install submodules/aidata/requirements.txt
    mkdir checkpoints && cd checkpoints && wget https://huggingface.co/facebook/cotracker3/resolve/main/scaled_offline.pth
    cd submodules/co-tracker && conda run -n aipipeline pip install -e .

# Update the environment. Run this command after checking out any code changes
update:
    conda env update --file environment.yml --prune

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
    time conda run -n aipipeline --no-capture-output python3 aipipeline/prediction/vss_init_pipeline.py --config $PROJECT_DIR/config/config.yml {{more_args}}

# Load already computed exemplars into the VSS database
load-vss project='uav' :
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/{{project}}
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/prediction/vss_load_pipeline.py --config $PROJECT_DIR/config/config.yml

# Cluster mission in aipipeline/projects/uav/data/missions2process.txt, add --vss to classify clusters with vss
cluster-uav *more_args="":
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/uav
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 $PROJECT_DIR/cluster_pipeline.py \
    --missions $PROJECT_DIR/data/missions2process.txt \
    --config $PROJECT_DIR/config/config.yml \
    {{more_args}}

# Detect mission in aipipeline/projects/uav/data/missions2process.txt
detect-uav *more_args="":
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/uav
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 $PROJECT_DIR/detect_pipeline.py \
    --missions $PROJECT_DIR/data/missions2process.txt \
    --config $PROJECT_DIR/config/config.yml \
    {{more_args}}

# Detect mission data in aipipeline/projects/uav/data/missions2process.txt
detect-uav-test:
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/uav
    export TEST_DIR=./test/projects/uav
    export PYTHONPATH=.
    echo $TEST_DIR/data/trinity-2_20240702T162557_Seacliff/SONY_DSC-RX1RM2 > $TEST_DIR/data/missions2process.txt
    time conda run -n aipipeline --no-capture-output python3 $PROJECT_DIR/detect_pipeline.py \
    --missions $TEST_DIR/data/missions2process.txt \
    --config $TEST_DIR/config/config_macos.yml

# Load uav mission images in aipipeline/projects/uav/data/missions2process.txt
load-uav-images:
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/uav
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 $PROJECT_DIR/load_image_pipeline.py \
    --missions $PROJECT_DIR/data/missions2process.txt \
    --config $PROJECT_DIR/config/config.yml

# Load uav detections/clusters in aipipeline/projects/uav/data/missions2process.txt
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
    export PYTHONPATH=.:submodules/aidata
    time conda run -n aipipeline --no-capture-output python3 $PROJECT_DIR/fix_metadata.py

# Compute saliency for downloaded VOC data and update the Tator database
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

# Download and crop Unknown detections
download-crop-unknowns project='uav' label='Unknown' download_dir='/tmp/download':
    #!/usr/bin/env bash
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/prediction/download_crop_pipeline.py \
        --config ./aipipeline/projects/{{project}}/config/config_unknown.yml \
        --skip_clean True \
        --label {{label}} \
        --download_dir {{download_dir}}

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
    --image_dir {{image_dir}} \
    {{more_args}}

# Run the strided inference on a single video
run-ctenoA-test:
    #!/usr/bin/env bash
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/projects/bio/run_strided_inference.py \
    --config ./aipipeline/projects/bio/config/config.yml \
    --class_name "Ctenophora sp. A" \
    --endpoint_url "http://localhost:8001/predict" \
    --video http://m3.shore.mbari.org/videos/M3/mezzanine/DocRicketts/2022/05/1443/D1443_20220529T135615Z_h265.mp4

# Run the strided inference on a collection of videos in a TSV file
run-ctenoA-prod:
    #!/usr/bin/env bash
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/projects/bio/run_strided_inference.py \
    --config ./aipipeline/projects/bio/config/config.yml \
    --class_name "Ctenophora sp. A" \
    --endpoint_url "http://fastap-fasta-0riu3xafmhua-337062127.us-west-2.elb.amazonaws.com/predict" \
    --tsv ./aipipeline/projects/bio/data/videotable.tsv