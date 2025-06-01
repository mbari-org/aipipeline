# aipipeline, Apache-2.0 license
# Filename: aipiipeline/prediction/load_pipeline.py
# Description: Run the VSS initialization pipeline
import json
import time
from datetime import datetime

import dotenv
import os
from pathlib import Path
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from typing import Dict, List
import logging

from aipipeline.engines.docker import run_docker
from aipipeline.config_setup import extract_labels_config, setup_config, CONFIG_KEY
from aipipeline.engines.subproc import run_subprocess
from aipipeline.prediction.library import (
    get_short_name,
    gen_machine_friendly_label,
)

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


# Load exemplars into Vector Search Server
def load_exemplars(labels: List[tuple[str, str]], config_dict=Dict, conf_files=Dict) -> str:
    project = str(config_dict["tator"]["project"])
    short_name = get_short_name(project)

    logger.info(labels)
    num_loaded = 0
    for label, save_dir in labels:
        machine_friendly_label = gen_machine_friendly_label(label)
        # Grab the most recent file
        all_exemplars = list(Path(save_dir).rglob("*_exemplars.csv"))
        exemplar_file = sorted(all_exemplars, key=os.path.getmtime, reverse=True)[0] if all_exemplars else None

        if exemplar_file is None:
            logger.info(f"No exemplar file found for {label}")
            exemplar_count = 0
        else:
            with open(exemplar_file, "r") as f:
                exemplar_count = len(f.readlines())

        if exemplar_count < 10 or exemplar_file is None:
            all_detections = list(Path(save_dir).rglob("*_detections.csv"))
            exemplar_file = sorted(all_detections, key=os.path.getmtime, reverse=True)[0] if all_detections else None

            if exemplar_file is None:
                logger.info(f"No detections file found for {label}")
                continue

            with open(exemplar_file, "r") as f:
                exemplar_count = len(f.readlines())
            logger.info(f"To few exemplars, using detections file {exemplar_file} instead")

        logger.info(f"Loading {exemplar_count} exemplars for {label} as {machine_friendly_label} from {exemplar_file}")
        args_list = [
            "aidata",
            "load",
            "exemplars",
            "--input",
            f"'{exemplar_file}'",
            "--label",
            f"'{label}'",
            "--device",
            "cuda:0",
            "--password",
            REDIS_PASSWORD,
            "--config",
            conf_files[CONFIG_KEY],
            "--token",
            TATOR_TOKEN,
        ]
        n = 3  # Number of retries
        delay_secs = 30  # Delay between retries

        for attempt in range(1, n + 1):
            try:
                result = run_subprocess(args_list=args_list)
                if result != 0:
                    logger.error(f"Error loading exemplars to VSS: {result}")
                    return f"Failed to load exemplars to VSS: {result}"
                logger.info(f"Loaded cluster exemplars for {label} from {exemplar_file}")
                num_loaded += 1
            except Exception as e:
                logger.error(f"Failed to load v exemplars for {label}: {e}")
                return f"Failed to load v exemplars for {label}: {e}"

    return f"Loaded {num_loaded} labels"

def get_labels(config_dict: Dict) -> Dict:
    labels = extract_labels_config(config_dict)
    return labels

# Beam pipeline
def run_pipeline(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Load exemplars into the VSS database")
    example_project = Path(__file__).resolve().parent.parent / "projects" / "uav" / "config" / "config.yml"
    parser.add_argument("--config", required=True, help=f"Config file path, e.g. {example_project}")
    args, unknown_args = parser.parse_known_args(argv)

    conf_files, config_dict = setup_config(args.config)
    labels = extract_labels_config(config_dict)
    options = PipelineOptions(unknown_args)

    processed_path = config_dict["data"]["processed_path"]

    # Find the nested directory called "crops" in processed_data and get its parent directory - this is where everything is stored
    base_path = None
    for f in Path(processed_path).rglob("crops"):
        logger.info(f"Found crops directory {f}")
        base_path = f.parent.as_posix()
        break

    if base_path is None:
        logger.error(f"Cannot find crops directory in {processed_path}?")
        exit(1)

    if labels == "all":
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
    else:
        data = [(label, (base_path / "cluster" /  label).as_posix()) for label in labels]

    with beam.Pipeline(options=options) as p:
        (
            p
            | "Create labels" >> beam.Create([data])
            | "Load exemplars" >> beam.Map(load_exemplars, config_dict=config_dict, conf_files=conf_files)
            | "Log results" >> beam.Map(logger.info)
        )


if __name__ == "__main__":
    run_pipeline()
