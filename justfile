#!/usr/bin/env just --justfile

# Source the .env file
set dotenv-load := true

# List recipes
list:
    @just --list --unsorted

# Setup the environment
install:
    conda env create -f environment.yml
    python -m pip install --upgrade pip
    python -m pip install https://github.com/redis/redis-py/archive/refs/tags/v5.0.9.zip
    git submodule update --init --recursive

# Update the environment. Run this command after checking out any code changes
update:
    conda env update --file environment.yml --prune

# Reset the VSS database, removing all data. Run befpre init-vss or when creating the database. Run with e.g. `uav`
reset-vss project='uav':
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/{{project}}
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/prediction/vss_reset.py --config $PROJECT_DIR/config/config.yml

# Initialize the VSS database for the UAV project
init-vss project='uav':
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/{{project}}
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/prediction/vss_init_pipeline.py --config $PROJECT_DIR/config/config.yml

# Cluster mission in aipipeline/projects/uav/data/missions2process.txt file
cluster-uav:
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/uav
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 $PROJECT_DIR/cluster-_pipeline.py --missions $PROJECT_DIR/data/missions2process.txt

# Detect mission in aipipeline/projects/uav/data/missions2process.txt file
detect-uav:
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/uav
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 $PROJECT_DIR/detect_pipeline.py --missions $PROJECT_DIR/data/missions2process.txt

# Detect mission data in aipipeline/projects/uav/data/missions2process.txt file on Mac
detect-uav-test:
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/uav
    export TEST_DIR=./test/projects/uav
    export PYTHONPATH=.
    echo $TEST_DIR/data/trinity-2_20240702T162557_Seacliff/SONY_DSC-RX1RM2 > $TEST_DIR/data/missions2process.txt
    time conda run -n aipipeline --no-capture-output python3 $PROJECT_DIR/detect_pipeline.py --missions $TEST_DIR/data/missions2process.txt --config $TEST_DIR/config/config_macos.yml

