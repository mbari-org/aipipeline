# Copy planktivore dev code to the project on doris
cp-dev-ptvr:
    #!/usr/bin/env bash
    cd ..
    cp justfiles/ptvr.just /Volumes/dcline/code/aipipeline/justfiles/ptvr.just
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.parquet' --exclude='*.log' --exclude='*__pycache__' aipipeline/projects/planktivore/ /Volumes/dcline/code/aipipeline/aipipeline/projects/planktivore/
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.parquet' --exclude='*.log' --exclude='*__pycache__' aipipeline/projects/planktivore-lm/ /Volumes/dcline/code/aipipeline/aipipeline/projects/planktivore-lm/
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.parquet' --exclude='*.log' --exclude='*__pycache__' aipipeline/projects/planktivore-hm/ /Volumes/dcline/code/aipipeline/aipipeline/projects/planktivore-hm/

# Load planktivore ROI images, e.g. just load-ptvr-images /mnt/DeepSea-AI/data/Planktivore/raw/aidata-export-02 --section aidata-export-02
load-ptvr-images images='tmp/roi' *more_args="":
    time aidata load images \
        --config aipipeline/projects/planktivore/config/config.yml \
        --input {{images}} \
        --token $TATOR_TOKEN \
        --dry-run {{more_args}}

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
    time just --justfile {{justfile()}} _base_cmd "aipipeline/projects/cfe/adjust_roi_ifcb.py \
        --input_dir /mnt/ML_SCRATCH/ifcb/raw/{{collection}} \
        --output_dir /mnt/ML_SCRATCH/ifcb/raw/{{collection}}-square/crops
    time just --justfile {{justfile()}} _base_cmd  ".aipipeline/projects/cfe/gen_ifcb_stats.py \
        --input_dir /mnt/ML_SCRATCH/ifcb/raw/{{collection}}-square/crops"

# Rescale planktivore ROI images, e.g. just rescale-ptvr-images aidata-export-03-low-mag
rescale-ptvr-images collection="aidata-export-03-low-mag":
    time just --justfile {{justfile()}} _base_cmd "aipipeline/projects/planktivore/adjust_roi.py \
        --input_dir /mnt/DeepSea-AI/data/Planktivore/raw/{{collection}} \
        --output_dir /mnt/DeepSea-AI/data/Planktivore/raw/{{collection}}-square"

# Download and rescale planktivore ROI images, e.g. just download-rescale-ptvr-images aidata-export-03-low-mag
download-rescale-ptvr-images collection="aidata-export-03-low-mag":
    time just --justfile {{justfile()}} _base_cmd "aipipeline/prediction/download_pipeline.py \
        --config aipipeline/projects/planktivore/config/{{collection}}.yml"
    just --justfile {{justfile()}} rescale-ptvr-images {{collection}}

# Run sweep for planktivore data. Example just cluster-ptvr-swp /mnt/ML_SCRATCH/Planktivore/aidata-export-03-low-mag-square /mnt/ML_SCRATCH/Planktivore/cluster/aidata-export-03-low-mag-square
cluster-ptvr-sweep roi_dir='/mnt/ML_SCRATCH/Planktivore/aidata-export-03-low-mag-square' save_dir='/mnt/ML_SCRATCH/Planktivore/cluster/aidata-export-03-low-mag-square' device='cuda':
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/planktivore
    export PYTHONPATH=.
    echo "Running clean pipeline"
    time just --justfile {{justfile()}} _base_cmd "aipipeline/prediction/clean_pipeline.py \
                            --config $PROJECT_DIR/config/config.yml \
                            --image-dir {{roi_dir}}"
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

# Generate training data for the planktivore low mag
gen-ptvr-lowmag-data:
  just --justfile {{justfile()}} download-crop planktivore --clean --gen-multicrop --data.download_dir /mnt/ML_SCRATCH/Planktivore/velella --data.download_args "'--verified --section Velella-low-mag --version Baseline'"
  just --justfile {{justfile()}} download-crop planktivore --clean --gen-multicrop --data.download_dir /mnt/ML_SCRATCH/Planktivore/lowmag --data.download_args "'--verified --version mbari-ifcb2014-vitb16-20250318_20250320_002422'"

# Load velella low mag data into Tator
load-ptvr-lowmag-velella:
  time conda run -n aipipeline --no-capture-output python3 aipipeline/projects/bio/load_velella_vss.py

# Load VSS mined planktivore low mag data into Tator
load-ptrv-high-mag-vss:
  #!/usr/bin/env bash
  export PROJECT_DIR=./aipipeline/projects/planktivore-hm
  export PYTHONPATH=.
  find /mnt/DeepSea-AI/data/Planktivore/processed/vss_hm -name "*.json" > $PROJECT_DIR/vss_files.txt
  time conda run -n aipipeline --no-capture-output python3 $PROJECT_DIR/load_rare_vss.py \
    --tator_loaded_csv $PROJECT_DIR/tator_verified_data_section_aidata-export-02-high-mag.csv \
    --input_json_paths $PROJECT_DIR/vss_files.txt
# Generate training data for the planktivore low mag
gen-ptvr-highmag-data:
  just --justfile {{justfile()}} download-crop planktivore-hm --clean --gen-multicrop --data.download_dir /mnt/ML_SCRATCH/Planktivore/highmag1 --data.download_args "'--verified --version mbari-ifcb2014-vitb16-20250318_20250320_025000,mbari-ptvr-vits-b8-20250513_20250526_130025'"

# Initialize the VSS database for the planktivore low mag data
init-ptvr-lowmag-vss:
  #!/usr/bin/env bash
  export PROJECT_DIR=./aipipeline/projects/planktivore-lm
  export PYTHONPATH=.
  time conda run -n aipipeline --no-capture-output python3 aipipeline/projects/planktivore/init_vss_pipeline.py\
        --config $PROJECT_DIR/config/config.yml \
        --data.download_dir /mnt/ML_SCRATCH/ptrv_lm  \
        --data.download_args "--verified --section Velella-low-mag --version Baseline" \
        --clean
  time conda run -n aipipeline --no-capture-output python3 aipipeline/projects/planktivore/init_vss_pipeline.py\
        --config $PROJECT_DIR/config/config.yml \
        --data.download_dir /mnt/ML_SCRATCH/ptrv_lm  \
        --data.download_args "--verified --version mbari-ifcb2014-vitb16-20250318_20250320_002422" \
        --clean
  rm -r mnt/ML_SCRATCH/ptrv_lm

# Initialize the VSS database for the planktivore high mag data
init-ptvr-highmag-vss:
  #!/usr/bin/env bash
  export PROJECT_DIR=./aipipeline/projects/planktivore-hm
  export PYTHONPATH=.
  time conda run -n aipipeline --no-capture-output python3 aipipeline/projects/planktivore/init_vss_pipeline.py\
        --config $PROJECT_DIR/config/config.yml \
        --data.download_dir /mnt/ML_SCRATCH/ptrv_hm  \
        --data.download_args "--verified --version mbari-ifcb2014-vitb16-20250318_20250320_025000" \
        --clean
  time conda run -n aipipeline --no-capture-output python3 aipipeline/projects/planktivore/init_vss_pipeline.py\
        --config $PROJECT_DIR/config/config.yml \
        --data.download_dir /mnt/ML_SCRATCH/ptrv_hm  \
        --data.download_args "--verified --version mbari-ptvr-vits-b8-20250513_20250526_130025" \
        --clean
  time conda run -n aipipeline --no-capture-output python3 aipipeline/projects/planktivore/init_vss_pipeline.py\
        --config $PROJECT_DIR/config/config.yml \
        --data.download_dir /mnt/ML_SCRATCH/ptrv_hm  \
        --data.download_args "--verified --version Baseline --labels alexandrium" \
  rm -r mnt/ML_SCRATCH/ptrv_hm


predict-vss-ptrv parquet="/mnt/DeepSea-AI/data/Planktivore/raw/2025_April-Ahi-Planktivore/April_2025_Ahi_highmag.parquet":
  #!/usr/bin/env bash
  export PROJECT_DIR=./aipipeline/projects/planktivore-hm
  export PYTHONPATH=.
  parquet="{{parquet}}"
  # Get the base name without directory and extension
  flat_name="${parquet##*/}" # Remove directory path
  image_listing="${flat_name}-images.txt"
  echo time conda run -n aipipeline --no-capture-output python3 aipipeline/projects/planktivore/export_filenames_from_parquet.py \
        --input_parquet {{ parquet }} \
        --output_text $image_listing

# Add depth and time to the planktivore parquet files. This is needed for downstream processing.
# Mount LRAVU directory to /mnt/LRAVU on doris before running, e.g.
# sudo mount -t smb3 //atlas.shore.mbari.org/LRAUV /mnt/ML_SCRATCH/LRAUV -o username=dcline,dir_mode=0777,file_mode=0666,vers=3.0,ro
# Run by year, e.g. just add-depth-time-ptvr 2025
# Be deafult, skips over already processed files - to disable add --no-skip, e.g. just add-depth-time-ptvr "2025" "--no-skip"
# Create environment first with
#    conda create -n pandas-parquet \
#      -c conda-forge \
#      python=3.12 \
#      pandas==3.0.0 \
#      xarray \
#      netcdf4 -y
add-depth-time-ptvr year="2025" *more_args="":
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/planktivore
    export PYTHONPATH=.
    time conda run -n pandas-parquet --no-capture-output python $PROJECT_DIR/add_depth_time_parquet.py {{year}} {{more_args}}