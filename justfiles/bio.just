# Copy bio dev code to the project on doris
cp-dev-bio:
    #!/usr/bin/env bash
    cd ..
    cp justfiles/bio.just /Volumes/dcline/code/aipipeline/justfiles/bio.just
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.log' --exclude='*__pycache__' aipipeline/projects/bio/ /Volumes/dcline/code/aipipeline/aipipeline/projects/bio/
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.log' --exclude='*__pycache__' deps/biotrack/biotrack/ /Volumes/dcline/code/aipipeline/deps/biotrack/biotrack/

# Run the mega strided pipeline on a videos in a dive for the bio project
run-mega-stride-bio video='/mnt/M3/mezzanine/Ventana/2023/10/4505/V4505_20231019T180422Z_h265.mp4':
    time just --justfile {{justfile()}} _base_cmd "aipipeline/projects/bio/process_video_pipeline.py \
    --config aipipeline/projects/bio/config/config.yml \
    --skip-track --min-score-det 0.01 --batch-size 1 --min-score-track 0.05 --min-frames 0 --min-depth 200 --max-depth 2000 --version ctenophora-sp-a-mega-vits \
    --vits-model /mnt/DeepSea-AI/models/bio/mbari-m3ctnA-vits-b16-20250331 \
    --class-name 'Ctenophora sp. A' \
    --det-model /mnt/DeepSea-AI/models/midwater/megadetrt-yolov5 \
    --stride 60 --video '{{video}}'"

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
    time just --justfile {{justfile()}} _base_cmd "aipipeline/projects/bio/process_video_pipeline.py \
       --config aipipeline/projects/bio/config/config.yml \
       --max-frames-tracked 200 --min-score-det 0.1 --batch-size 34 --min-score-track 0.1 --min-frames 5 --version mega-vits-track-gcam \
       --vits-model /mnt/DeepSea-AI/models/m3midwater-vit-b-16 \
       --det-model /mnt/DeepSea-AI/models/midwater/megadetrt-yolov5 \
       --stride 16 --video '{{video}}'"

# Run the mega strided tracking pipeline on a single video to test the pipeline
run-mega-track-test-1min:
   time just --justfile {{justfile()}} _base_cmd "aipipeline/projects/bio/predict.py \
     --config aipipeline/projects/bio/config/config.yml \
     --det-model /mnt/DeepSea-AI/models/midwater/megadet \
     --vits-model /mnt/DeepSea-AI/models/m3midwater-vit-b-16 \
     --max-frames-tracked 200 --min-score-det 0.0002 --min-score-track 0.5 --min-frames 5 --version mega-vits-track-gcam \
     --stride 8 --max-seconds 60 --imshow --skip-load  \
     --video aipipeline/projects/bio/data/V4361_20211006T163256Z_h265_1min.mp4"

# Run the mega strided tracking pipeline on a single video for the bio project with FastAPI
run-mega-track-test-fastapiyv5:
    time just --justfile {{justfile()}} _base_cmd "aipipeline/projects/bio/predict.py \
     --config aipipeline/projects/bio/config/config.yml \
     --vits-model /mnt/DeepSea-AI/models/m3midwater-vit-b-16 \
     --max-frames-tracked 200 --min-score-det 0.0002 --min-score-track 0.5 --min-frames 5 --version mega-vits-track-gcam \
     --stride 15 --max-seconds 60 --imshow --skip-load  \
     --endpoint-url http://FastAP-FastA-0RIu3xAfMhUa-337062127.us-west-2.elb.amazonaws.com/predict \
     --video aipipeline/projects/bio/data/V4361_20211006T163256Z_h265_1min.mp4"

# Generate training data for the bio project
gen-bio-data: 
   time just --justfile {{justfile()}} _base_cmd "aipipeline/db/tator/download_crop_pipeline.py \
        --config aipipeline/projects/bio/config/config.yml \
        --skip-clean True \
        --data.download_dir /mnt/ML_SCRATCH/bio \
        --data.download_args '--verified --voc --version Baseline,mega-vits-track-gcam,mbari-i2map-vits-b8-20251008-vss '"

run-ctenoA-prod:
    echo "Running strided inference on multiple videos from TSV"
    time just --justfile {{justfile()}} _base_cmd "aipipeline/projects/bio/cluster.py \
    --config aipipeline/projects/bio/config/config.yml \
    --class_name "Ctenophora sp. A" \
    --endpoint-url "http://fastap-fasta-0riu3xafmhua-337062127.us-west-2.elb.amazonaws.com/predict" \
    --tsv aipipeline/projects/bio/data/videotable.tsv"

# Run the mega strided inference only on a single video
run-mega-inference:
    time just --justfile {{justfile()}} _base_cmd "aipipeline/projects/bio/cluster.py \
    --config aipipeline/projects/bio/config/config.yml \
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
    --video /mnt/M3/mezzanine/Ventana/2020/12/4318/V4318_20201208T203419Z_h264.mp4"

# Replace m3 urls with mantis
replace-m3-urls:
    time just --justfile {{justfile()}} _base_cmd "aipipeline/projects/bio/maintenance/replace_tm3.py"



# Transcode M3 videos from mov to mp4 for use in Tator. Keyframe every 2 seconds
# Example just transcode-bio /mnt/M3/master/DocRicketts/2022/05/1443/ /mnt/DeepSea-AI/data/DocRicketts/2022/05/1443/
transcode-bio input_dir='/mnt/M3/master/DocRicketts/2018/05/1023/' output_dir='/mnt/DeepSea-AI/data/DocRicketts/2018/05/1023/':
    time just --justfile {{justfile()}} _base_cmd "aipipeline/projects/i2map/mov2mp4.py --input {{input_dir}} --output {{output_dir}} --gop 60"
# Download Ctenophora sp. A training data only
gen-ctenoA-data:
    #!/usr/bin/env bash
    export PYTHONPATH=deps:deps/biotrack:.
    export MPLCONFIGDIR=/tmp
    time conda run -n aipipeline --no-capture-output python3 \
        aipipeline/db/tator/download_crop_pipeline.py \
        --config aipipeline/projects/bio/config/config.yml \
        --clean \
        --data.download_dir /mnt/ML_SCRATCH/bio_ctenoA \
        --data.download_args '--voc --labels "Ctenophora sp. A"'
    aidata transform voc --base-path /mntai/ML_SCRATCH/bio_ctenoA/ --crop-size 728 --crop-overlap 0.2 --min-visibility 0.