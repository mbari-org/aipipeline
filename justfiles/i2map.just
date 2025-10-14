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

# Download i2mpabulk unverified data
download-i2map-unverified:
    time just --justfile {{justfile()}} _base_cmd "aipipeline/db/tator/download_crop_pipeline.py \
        --config aipipeline/projects/i2map-/config/config.yml \
        --data.download_dir /mnt/ML_SCRATCH/i2mapu \
        --data.download_args '--unverified --version Baseline --generator vars-labelbot --group NMS' "

# Download i2mpabulk unlabeled data run with ENV_FILE=.env.i2map just download-i2mapbulk-unlabeled
download-i2mapbulk-unlabeled:
    time just --justfile {{justfile()}} _base_cmd "aipipeline/db/tator/download_crop_pipeline.py \
        --config aipipeline/projects/i2mapbulk/config/config.yml \
        --data.download_dir /mnt/ML_SCRATCH/i2mapbulku \
        --data.download_args '--unverified' "

# Download i2mpabulk unlabeled data run with ENV_FILE=.env.i2map just download-i2mapbulk-baseline
download-i2mapbulk-baseline:
    time just --justfile {{justfile()}} _base_cmd "aipipeline/db/tator/download_crop_pipeline.py \
        --config aipipeline/projects/i2mapbulk/config/config.yml \
        --data.download_dir /mnt/ML_SCRATCH/i2mapbulkb \
        --data.download_args '--version Baseline' "


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
        --data.download_args '--voc --verified --version Baseline --generator vars-labelbot --group NMS ' \
        --labels 'Acanthamunnopsis milleri' 'Aegina' 'Aegina citrea' 'Aegina rosea' \
        'Aegina sp. 1' 'Agalmatidae' 'Amphipoda' 'Annatiara affinis' \
        'Apolemiidae' 'Appendicularia' 'Atolla' 'Bathochordaeus' \
        'Bathochordaeus sinker' 'Bathochordaeus sinkers' 'Bathochordaeus stygius' \
        'Beroe' 'Beroe cucumis' 'Bolinopsis' 'Bolinopsis infundibulum' \
        'Calycophorae' 'Chaetognatha' 'Chiroteuthis calyx' 'Chuniphyes' \
        'Colobonema sericeum' 'Copepoda' 'Cranchiidae' 'Crustacea' \
        'Ctenophora' 'Cydippida' 'Cydippida sp. A' 'Cystisoma' \
        'Desmophyes annectens' 'Earleria corachloeae' 'Euchirella bitumida' \
         'Euphausiacea1' 'Euphysa' 'Eusergestes similis' \
         'Eutonina indicans' 'Forskalia' 'Gonatus' 'Haliscera conica' \
         'Halitrephes' 'Hastigerinella digitata' 'Hormiphora californensis' \
         'Krill molt' 'Lensia' 'Lensia conoidea' 'Medusae' \
         'Mertensiidae' 'Mitrocoma cellularia' 'Modeeria rotunda' \
         'Myctophidae' 'Nanomia' 'Nanomia bijuga' 'Nanomia 2' \
         'Octogonade mediterranea' 'Oikopleuridae' 'Pasiphaea' \
         'Periphylla periphylla' 'Phronima' 'Physonectae' \
         'Poeobius meseres' 'Prayidae' 'Ptychogena lactea' \
         'Radiozoa' 'Resomia ornicephala' 'Rhopalonema' \
         'Salpa fusiformis' 'Salpidae' 'Scina' 'Sergestid molt' \
         'Siphonophorae' 'Solmissus' 'Solmundella bitentaculata' \
         'sinker' 'Stellamedusa ventana' 'Teuthoidea' \
         'Thalassocalyce inconstans' 'Tomopteridae' 'Tuscaroridae' \
         'Vitreosalpa gemini' 'Vogtia' 'Zoarcidae'"

# Download and cluster data. Run with just download-cluster i2map
cluster-i2map:
    just --justfile {{justfile()}} cluster i2map --version Baseline \
        --input /mnt/ML_SCRATCH/i2map/Baseline/crops \
        --output /mnt/ML_SCRATCH/i2map/Baseline/clusters

# Generate training data for the i2map project from the bulk server, run with ENV_FILE=.env.i2map just gen-i2mapbulk-data
gen-i2mapbulk-data:
    time just --justfile {{justfile()}} _base_cmd "aipipeline/db/tator/download_crop_pipeline.py \
        --config aipipeline/projects/i2mapbulk/config/config.yml \
        --clean \
        --use-cleanvision True \
        --data.download_dir /mnt/ML_SCRATCH/i2mapbulk \
        --data.download_args '--voc --verified ' \
        --labels 'Acanthamunnopsis milleri' 'Aegina' 'Aegina citrea' 'Aegina rosea' \
        'Aegina sp. 1' 'Agalmatidae' 'Amphipoda' 'Annatiara affinis' \
        'Apolemiidae' 'Appendicularia' 'Atolla' 'Bathochordaeus' \
        'Bathochordaeus sinker' 'Bathochordaeus sinkers' 'Bathochordaeus stygius' \
        'Beroe' 'Beroe cucumis' 'Bolinopsis' 'Bolinopsis infundibulum' \
        'Calycophorae' 'Chaetognatha' 'Chiroteuthis calyx' 'Chuniphyes' \
        'Colobonema sericeum' 'Copepoda' 'Cranchiidae' 'Crustacea' \
        'Ctenophora' 'Cydippida' 'Cydippida sp. A' 'Cystisoma' \
        'Desmophyes annectens' 'Earleria corachloeae' 'Euchirella bitumida' \
         'Euphausiacea1' 'Euphysa' 'Eusergestes similis' \
         'Eutonina indicans' 'Forskalia' 'Gonatus' 'Haliscera conica' \
         'Halitrephes' 'Hastigerinella digitata' 'Hormiphora californensis' \
         'Krill molt' 'Lensia' 'Lensia conoidea' 'Medusae' \
         'Mertensiidae' 'Mitrocoma cellularia' 'Modeeria rotunda' \
         'Myctophidae' 'Nanomia' 'Nanomia bijuga' 'Nanomia 2' \
         'Octogonade mediterranea' 'Oikopleuridae' 'Pasiphaea' \
         'Periphylla periphylla' 'Phronima' 'Physonectae' \
         'Poeobius meseres' 'Prayidae' 'Ptychogena lactea' \
         'Radiozoa' 'Resomia ornicephala' 'Rhopalonema' \
         'Salpa fusiformis' 'Salpidae' 'Scina' 'Sergestid molt' \
         'Siphonophorae' 'Solmissus' 'Solmundella bitentaculata' \
         'sinker' 'Stellamedusa ventana' 'Teuthoidea' \
         'Thalassocalyce inconstans' 'Tomopteridae' 'Tuscaroridae' \
         'Vitreosalpa gemini' 'Vogtia' 'Zoarcidae'"

# Initialize the VSS database for the i2MAP bulk project, run with ENV_FILE=.env.i2map just init-i2mapbulk-vss
init-i2mapbulk-vss:
  #!/usr/bin/env bash
  export PROJECT_DIR=./aipipeline/projects/i2mapbulk
  export PYTHONPATH=.
  time conda run -n aipipeline --no-capture-output python3 aipipeline/db/redis/vss/init_pipeline.py \
        --config $PROJECT_DIR/config/config.yml \
        --data.download_dir /mnt/ML_SCRATCH/i2mapbulk  \
        --data.download_args "--verified " \
        --clean

# Remove ambiguous i2map exemplars VSS database
clean-i2map-vss:
    time just --justfile {{justfile()}} remove-vss i2map --doc \'doc:marine organism:\*\'
    time just --justfile {{justfile()}} remove-vss i2map --doc \'doc:marine snow:\*\'
    time just --justfile {{justfile()}} remove-vss i2map --doc \'doc: mix Pasiphaea and krill:\*\'
    time just --justfile {{justfile()}} remove-vss i2map --doc \'doc: Unknown:\*\'


# Initialize the VSS database for the i2MAP bulk project
init-i2map-vss:
  #!/usr/bin/env bash
  export PROJECT_DIR=./aipipeline/projects/i2map
  export PYTHONPATH=.
  time conda run -n aipipeline --no-capture-output python3 aipipeline/db/redis/vss/init_pipeline.py \
        --config $PROJECT_DIR/config/config.yml \
        --data.download_dir /mnt/ML_SCRATCH/i2map  \
        --data.download_args "--verified --version Baseline --generator vars-labelbot --group NMS " \
        --clean

# Cluster bulk unknown data
cluster-i2mapbulk:
    #!/usr/bin/env bash
    export PROJECT_DIR=$PWD/aipipeline/projects/i2mapbulk
    export RAY_TMPDIR=/mnt/ML_SCRATCH/ray/
    export MPLCONFIGDIR=/mnt/ML_SCRATCH/matplotlib
    export RAY_DEDUP_LOGS=0
    cd ~/code/sdcat
    time conda run -n rapids-25.04 sdcat cluster roi --config-ini $PROJECT_DIR/config/sdcat.ini \
            --roi-dir /mnt/ML_SCRATCH/i2mapbulku/crops \
            --save-dir /mnt/ML_SCRATCH/i2mapbulku/clusters \
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
                        --roi-dir /mnt/ML_SCRATCH/i2mapbulku/crops \
                        --save-dir /mnt/ML_SCRATCH/i2mapbulku/clusters \
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
# Load vss generated i2mapbulk data run with ENV_FILE=.env.i2map just load-i2mapbulk-vss
load-i2mapbulk-vss:
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/i2mapbulk
    export PYTHONPATH=.
    find /mnt/DeepSea-AI/data/i2MAP/processed/vss -type f -name "*.json" &> $PROJECT_DIR/i2mapbulkjson.txt
    find /mnt/DeepSea-AI/data/M3/processed/vss -type f -name "*.json" &>  $PROJECT_DIR/m3mapbulkjson.txt
    cd $PROJECT_DIR
    conda run -n aipipeline --no-capture-output python3 download_baseline.py --project_id 1 --box_type 5 --image_type 3 --output_csv tator_i2mapbulk_baseline.csv
    conda run -n aipipeline --no-capture-output python3 load_vss.py \
                  --input_json_paths i2mapbulkjson.txt \-
                  --save_path /tmp/i2mapbulkvss_top3 \
                  --tator_loaded_csv tator_i2mapbulk_baseline.csv \
                  --version mbari-i2map-vits-b8-20251008-vss

    conda run -n aipipeline --no-capture-output python3 load_vss.py \
                  --input_json_paths m3mapbulkjson.txt \
                  --save_path /tmp/m3mapbulkvss_top3 \
                  --tator_loaded_csv tator_i2mapbulk_baseline.csv \
                  --version mbari-m3-vits-b8-20251011-vss
load-i2map-vss:
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/i2map
    export PYTHONPATH=.
    find /mnt/DeepSea-AI/data/i2MAP/processed/vss -type f -name "*.json" &> $PROJECT_DIR/i2mapjson.txt
    cd $PROJECT_DIR
    conda run -n aipipeline --no-capture-output python3 download_baseline.py --project_id 3 --box_type 3 --image_type 5 --output_csv tator_i2map_baseline.csv
    conda run -n aipipeline --no-capture-output python3 load_vss.py \
                  --input_json_paths i2mapjson.txt \
                  --save_path /tmp/i2mapvss_top3 \
                  --tator_loaded_csv tator_i2map_baseline.csv \
                  --version mbari-i2map-vits-b8-20251008-vss
