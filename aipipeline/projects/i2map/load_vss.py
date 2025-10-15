# Utility script to load localizations classified by VSS into Tator
#
# First run to find all JSON files that contain predictions:
# find /mnt/DeepSea-AI/data/i2map/processed/vss -type f -name "*.json" &> i2mapjson.txt
# find /mnt/DeepSea-AI/data/m3/processed/vss -type f -name "*.json" &>  m3mapbulkjson.txt
#
# And export all the Baseline data in i2map to a CSV file
# python download_baseline.py
#
# Then run this script, e.g.
# python load_vss.py --input_json_paths i2mapjson.txt --save_path /tmp/i2mapvss_top3 --tator_loaded_csv tator_i2map_baseline.csv --version mbari-i2map-vits-b8-20251008-vss
# python load_vss.py --input_json_paths m3mapbulkjson.txt --save_path /tmp/m3mapbulkvss_top3 --tator_loaded_csv tator_i2map_baseline.csv --version mbari-m3-vits-b8-20251011-vss
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

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)
# and log to file
now = datetime.now()
log_filename = f"i2map_load_vss{now:%Y%m%d}.log"
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
    parser.add_argument(
        "--save_path",
        type=str,
        required=True,
        help="Path to save the intermediate SDCAT formatted CSV file"
    )
    parser.add_argument(
        "--version",
        type=str,
        help="Version string to use when loading boxes into Tator"
    )
    args = parser.parse_args()

    # Read in tator_loaded_csv
    tator_loaded_df = pd.read_csv(args.tator_loaded_csv)
    tator_loaded_df.set_index('id', inplace=True)

    image_width = 2048
    image_height = 1080

    # Load the text file with the paths
    with open(args.input_json_paths, "r") as file:
        paths = file.readlines()

    # Read the JSON files with predictions and format into SDCAT compatible format
    sdcat_formatted_data = []
    num_found = 0
    files = []
    save_path = Path(args.save_path)
    save_path.mkdir(parents=True, exist_ok=True)
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
                    media_id = int(Path(filename).stem)
                    try:
                        row = tator_loaded_df.loc[int(media_id)]
                    except KeyError:
                        logger.warning(f"Could not find media_id {media_id} in tator_loaded_df")
                        continue

                    image_path = filename
                    num_found += 1
                    logger.info(f"Processing media_id {media_id}")
                    sdcat_formatted_data.append({
                        "image_width": image_width,
                        "image_height": image_height,
                        "image_path": row["image_path"],
                        "media_id": media_id, # Use the media_id just for sanity checking
                        "score": 1.0-scores[0], # scores from VSS are reported as distance to the class, so we invert them
                        "score_s": 1.0-scores[1],
                        "label": predictions[0],
                        "label_s": predictions[1],
                        "x": row['x'],
                        "y": row['y'],
                        "xx": row['x'] + row['width'],
                        "xy": row['y'] + row['height'],
                        "cluster": -1
                    })
        except Exception as e:
            logger.error(f"Error processing {path}: {e}")
            continue

    print(f"Found {num_found} images with predictions out of {len(paths)} files")
    df = pd.DataFrame.from_records(sdcat_formatted_data)

    # Drop any duplicate rows; duplicates have the same media_id, x, y, xx, xy, and label
    df.drop_duplicates(subset=['media_id', 'x', 'y', 'xx', 'xy', 'label'], inplace=True)
    logger.info(f"{len(df)} rows after dropping duplicates")
    df.to_csv(save_path / "i2mapvss.csv", index=False)

    # Read back the CSV and remove
    df = pd.read_csv(save_path / "i2mapvss.csv")

    import pdb; pdb.set_trace()
    logger.info(f"{len(df)} rows to load into Tator")

    # Load the SDCAT formatted data into Tator using aidata commands
    version = args.version
    config = "https://docs.mbari.org/internal/ai/projects/config/config_i2map.yml"

    # Load the boxes
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
    logger.info(f"total loading time: {time_end - time_start}")