# Utility script to add velella localization classified by VSS
#
# First run to find all JSON files that contain Velella_velella predictions:
# find /mnt/DeepSea-AI/data/Planktivore/processed/vss_lm/ -type f -name "*.json" | xargs grep Velella_velella &> Velella_velella.txt
#
# Then run this script, e.g.
# python load_velella_vss.py --input_file Velella_velella.txt --save_path /mnt/DeepSea-AI/data/Planktivore/processed/vss_lm/Velella_velella_top3
# --tator_loaded_csv /mnt/DeepSea-AI/data/Planktivore/processed/vss_lm/tator_loaded_images.csv --section Velella-low-mag
#
import argparse
import os
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
log_filename = f"load_rare_vss{now:%Y%m%d}.log"
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
    parser = argparse.ArgumentParser(description="Process VSS predictions.")
    parser.add_argument(
        "--input_json_paths",
        type=str,
        default="high-mag-input.txt",
        help="Path to the input text file with full paths to the JSON prediction files (one per line)"
    )
    parser.add_argument(
        "--tator_loaded_csv",
        type=str,
        required=True,
        help="Path to the previously loaded data to avoid duplicates"
    )
    args = parser.parse_args()
    section = "rare-high-mag"
    rare_classes = ["Detonula_Cerataulina_Lauderia",
                    "Thalassiosira",
                    "Dinoflagellate",
                    "Thalassionema",
                    "Polykrikos",
                    "Ceratium",
                    "Truncated",
                    "Guinardia_Dactyliosolen",
                    "Tiarina",
                    "Dictyocha",
                    "Eucampia",
                    "Strombidium",
                    "Cylindrotheca",
                    "Alexandrium"]

    # Read in tator_loaded_csv
    tator_loaded_df = pd.read_csv(args.tator_loaded_csv)
    tator_loaded_images = list(tator_loaded_df['(media) $name'].values)
    # Truncate to the last 30 characters
    tator_loaded_images = [name[-30:].replace("-", "_") for name in tator_loaded_images]

    # Load the text file with the paths
    with open(args.input_json_paths, "r") as file:
        paths = file.readlines()

    # Remove duplicates
    paths = list(set(paths))

    # Read the JSON files with predictions and format into SDCAT compatible format
    sdcat_formatted_data = []
    num_found = 0
    files = []
    save_path = Path("/mnt/DeepSea-AI/data/Planktivore/processed/vss_lm/rare_classes_high_mag")
    save_path.mkdir(parents=True, exist_ok=True)
    images_to_load =  save_path / "images.txt"
    with images_to_load.open("w") as image_file:
        for path in paths:
            try:
                path = path.strip()
                with open(path, "r") as json_file:
                    data = json.load(json_file)
                    all_predictions = data.get("predictions")
                    all_scores = data.get("scores")
                    filenames = data.get("filenames")
                    i = 0
                    for filename, predictions, scores in zip(filenames, all_predictions, all_scores):
                        avg_score = sum(scores) / len(scores)
                        name = Path(filename).name
                        # Check the last 30 characters of the filename to see if it is already loaded
                        name_match = name[-30:]
                        name_match = name_match.replace("-", "_")
                        if name_match in tator_loaded_images:
                            print(f"Skipping {filename} because it is already loaded")
                            continue

                        # If the top two predictions are in the list to mine and their scores are both < 0.25, save the image and add to sdcat formatted data
                        if predictions[0] in rare_classes and predictions[1] in rare_classes and scores[0] < 0.25 and scores[1] < 0.25:
                            if name not in tator_loaded_images:
                                # print(f"Found {filename} with all predictions {predictions} and scores {scores}")
                                image_path = filename
                                image_file.write(f"{image_path}\n")
                                num_found += 1
                                with Image.open(image_path) as img:
                                    image_width, image_height = img.size
                                sdcat_formatted_data.append({
                                    "image_width": image_width,
                                    "image_height": image_height,
                                    "image_path": image_path,
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
                logger.error(f"Error processing {path}: {e}")
                continue

    print(f"Found {num_found} potentially rare classes.")
    df = pd.DataFrame.from_records(sdcat_formatted_data)

    # Drop any duplicate rows; duplicates have the same image_path
    df = df.drop_duplicates(subset=["image_path"])
    df.to_csv(save_path / "rare_classes.csv", index=False)

    # Load the SDCAT formatted data into Tator using aidata commands

    # Find the unique image paths and load the media
    image_paths = df['image_path'].values
    project = "902004-Planktivore"
    version = "mbari-ptvr-vits-b8-20250826-vss"
    config = "https://docs.mbari.org/internal/ai/projects/config/config_planktivore_hm.yml"

    # # Load the images
    args = [
        "load",
        "images",
        "--input",
        str(images_to_load),
        "--config",
        config,
        "--token",
        TATOR_TOKEN,
        "--section",
        section,
    ]
    command = "aidata " + " ".join(args)
    logger.info(f"Running {command}")
    subprocess.run(command, shell=True)

    # Now load the boxes
    args = [
        "load",
        "boxes",
        "--input",
        str(save_path),
        "--config",
        config,
        "--token",
        TATOR_TOKEN,
        "--version",
        version
    ]
    command = "aidata " + " ".join(args)
    logger.info(f"Running {command}")
    subprocess.run(command, shell=True)

    time_end = time.time()
    logger.info(f"total processing time: {time_end - time_start}")
