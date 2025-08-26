# aipipeline, Apache-2.0 license
# Filename: aipiipeline/prediction/load_pipeline.py
# Description: Run the VSS initialization pipeline
import json
import time
from collections import defaultdict
from datetime import datetime

import dotenv
import os
from pathlib import Path
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from typing import Dict
import logging

from aipipeline.config_args import parse_override_args
from aipipeline.config_setup import extract_labels_config, setup_config
from aipipeline.db.redis.vss.exemplars import load_exemplars
from aipipeline.prediction.library import compute_stats

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.DEBUG)
# and log to file
now = datetime.now()
log_filename = f"vss_init_pipeline_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Secrets
dotenv.load_dotenv()
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
TATOR_TOKEN = os.getenv("TATOR_TOKEN")

def get_labels(config_dict: Dict) -> Dict:
    labels = extract_labels_config(config_dict)
    return labels

# Beam pipeline
def run_pipeline(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Load exemplars into the VSS database")
    example_project = Path(__file__).resolve().parent.parent / "projects" / "uav" / "config" / "config.yml"
    parser.add_argument("--config", required=True, help=f"Config file path, e.g. {example_project}")
    args, other_args = parser.parse_known_args(argv)
    options = PipelineOptions(other_args)
    conf_files, config_dict = setup_config(args.config, silent=True)
    config_dict = parse_override_args(config_dict, other_args)
    download_dir = config_dict["data"]["download_dir"]

    # Find the nested directory called "crops" in processed_data and get its parent directory - this is where everything is stored
    base_path = None
    for f in Path(download_dir).rglob("crops"):
        logger.info(f"Found crops directory {f}")
        base_path = f.parent.as_posix()
        break

    if base_path is None:
        logger.error(f"Cannot find crops directory in {download_dir}?")
        exit(1)

    # Find the file stats.txt and read it as a json file
    stats_file = Path(f"{base_path}/crops/stats.json")
    if not stats_file.exists():
        logger.error(f"Cannot find {stats_file}. Exiting.")
        exit(1)

    data = []
    with stats_file.open("r") as f:
        stats = json.load(f)
        logger.info(f"Found stats: {stats}")
        total_labels = stats["total_labels"]
        labels = list(total_labels.keys())
        logger.info(f"Found labels: {labels}")
        for label, count in total_labels.items():
            if count == 0:
                logger.info(f"Skipping label {label} with 0 crops")
                continue
            logger.info(f"Found {count} crops for label {label}")
            data.append((label,f"{base_path}/cluster/{label}") )
        logger.debug(data)

    with beam.Pipeline(options=options) as p:
        (
            p
            | "Create labels" >> beam.Create([data])
            | "Load exemplars" >> beam.Map(load_exemplars, conf_files=conf_files)
            | "Log results" >> beam.Map(logger.info)
        )


if __name__ == "__main__":
    run_pipeline()
