# Utility script to load classes assigned by VSS
#
import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import json
import logging
import time

import pandas as pd
from PIL import Image

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)
# and log to file
now = datetime.now()
log_filename = f"load_vss{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

TATOR_TOKEN = os.getenv("TATOR_TOKEN")

if not TATOR_TOKEN:
    logger.error("TATOR_TOKEN environment variable not set")
    sys.exit(1)

if __name__ == "__main__":
    time_start = time.time()
    parser = argparse.ArgumentParser(description="Process VSS prediction for Planktivore Low-Magnification Camera.")
    parser.add_argument(
        "--save_path",
        type=str,
        default="/mnt/DeepSea-AI/data/Planktivore/processed/vss_lm/",
        help="Directory to save results"
    )
    parser.add_argument(
        "--input_path",
        default="/mnt/DeepSea-AI/data/Planktivore/processed/vss_lm/",
        type=str,
        help="Path to the raw json files with VSS predictions"
    )
    args = parser.parse_args()

    save_path = Path(args.save_path)
    save_path.mkdir(parents=True, exist_ok=True)

    input_path = Path(args.input_path)

    # Read the JSON files with Velella_velella predictions in the top 3 with < 0.33 score and format into SDCAT compatible format
    sdcat_formatted_data = []
    for path in input_path.rglob("*.json"):
        with open(path, "r") as file:
            data = json.load(file)
            all_predictions = data.get("predictions")
            all_scores = data.get("scores")
            filenames = data.get("filenames")
            i = 0
            for i, filename in enumerate(filenames):
                predictions = all_predictions[i]
                scores = all_scores[i]
                avg_score = sum(scores) / len(scores)

                # Keep files where the average score is < 0.2 or all predictions are the same
                if avg_score < 0.2 or all(p == predictions[0] for p in predictions):
                    print(f"Found {filename} with all predictions {predictions} and scores {scores}")
                    try:
                        with Image.open(filename) as img:
                            image_width, image_height = img.size
                        sdcat_formatted_data.append({
                            "image_width": image_width,
                            "image_height": image_height,
                            "image_path": filename,
                            "score": 1.0-scores[0], # scores from VSS are reported as distance to the class, so we invert them
                            "score_s": 1.0-scores[1],
                            "label": predictions[0],
                            "label_s": predictions[1],
                            "x": 0.0,
                            "y": 0.0,
                            "xx": 1.0,
                            "xy": 1.0,
                            "cluster": -1
                        })
                    except Exception as e:
                        logger.error(f"Error processing {filename}: {e}")
                        continue

    df = pd.DataFrame.from_records(sdcat_formatted_data)
    # Drop any duplicate rows; duplicates have the same image_path
    df = df.drop_duplicates(subset=["image_path"])
    df.to_csv(save_path / "ptr_lm_vss_predictions_sdcat.csv", index=False)
    logger.info(f"Saved {len(df)} unique predictions to {save_path / 'ptr_lm_vss_predictions_sdcat.csv'}")

    # Load the SDCAT formatted data into Tator using aidata commands

    # Find the unique image paths and load the media
    # image_paths = df['image_path'].values
    # project = "902004-Planktivore"
    # version = "Baseline"
    # config = "https://docs.mbari.org/internal/ai/projects/config/config_planktivore_lm.yml"
    #
    # # Load the images
    # args = [
    #     "load",
    #     "images",
    #     "--input",
    #     str(save_path),
    #     "--config",
    #     config,
    #     "--token",
    #     TATOR_TOKEN,
    #     "--section",
    #     args.section,
    # ]
    # command = "aidata " + " ".join(args)
    # logger.info(f"Running {command}")
    # subprocess.run(command, shell=True)
    #
    # # Now load the boxes
    # args = [
    #     "load",
    #     "boxes",
    #     "--input",
    #     str(save_path),
    #     "--config",
    #     config,
    #     "--token",
    #     TATOR_TOKEN,
    #     "--version",
    #     version
    # ]
    # command = "aidata " + " ".join(args)
    # logger.info(f"Running {command}")
    # subprocess.run(command, shell=True)
    #
    # time_end = time.time()
    # logger.info(f"total processing time: {time_end - time_start}")
