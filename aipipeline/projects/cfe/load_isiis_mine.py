import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)
# and log to file
now = datetime.now()
log_filename = f"load_isiis_mine{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

TATOR_TOKEN = os.getenv("TATOR_TOKEN")

if not TATOR_TOKEN:
    logger.error("TATOR_TOKEN environment variable not set")
    sys.exit(1)

if __name__ == "__main__":
    import time

    time_start = time.time()

    out_path = Path.cwd() / 'output'
    (out_path / 'csv').mkdir(parents=True, exist_ok=True)
    (out_path / 'crop').mkdir(parents=True, exist_ok=True)

    # Read in all the csv files into a pandas dataframe
    # This will be used to filter the images that need to be processed
    df_all = pd.DataFrame()
    for f in (out_path / 'csv').rglob("*.csv"):
        logger.info(f"Reading {f}")
        if pd.read_csv(f).shape[0] == 0:
            logger.info(f"Skipping {f} as it is empty")
            continue
        df = pd.read_csv(f)
        df_all = pd.concat([df_all, df], ignore_index=True)

    # Find the unique image paths and load the media
    image_paths = df_all['image_path'].unique()
    project = "902111-CFE"
    section = "mine_depth_v1"
    config = "https://docs.mbari.org/internal/ai/projects/config/config_cfe_deploy.yml"

    # Load the images
    for image_path in image_paths:
        args = [
            "load",
            "images",
            "--input",
            f"'{image_path}'",
            "--config",
            config,
            "--token",
            TATOR_TOKEN,
            "--section",
            section,
        ]
        command = "python -m aidata " + " ".join(args)
        logger.info(f"Running {command}")
        subprocess.run(command, shell=True)

    # Now load the boxes
    args = [
        "load",
        "boxes",
        "--input",
        out_path / 'csv',
        "--config",
        config,
        "--token",
        TATOR_TOKEN,
    ]
    command = "python -m aidata " + " ".join(args)
    logger.info(f"Running {command}")
    subprocess.run(command, shell=True)

    time_end = time.time()
    logger.info(f"total processing time: {time_end - time_start}")
