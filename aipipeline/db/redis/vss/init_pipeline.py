# aipipeline, Apache-2.0 license
# Filename: aipiipeline/db/redis/vss/init_pipeline.py
# Description: Run the VSS initialization pipeline
import time
from datetime import datetime

import dotenv
import os
from pathlib import Path
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from typing import Dict
import logging

from aipipeline.config_args import parse_override_args
from aipipeline.config_setup import extract_labels_config, setup_config, CONFIG_KEY
from aipipeline.engines.subproc import run_subprocess
from aipipeline.prediction.library import (
    download,
    compute_stats,
    get_short_name,
    gen_machine_friendly_label,
    clean,
    batch_elements,
    ProcessClusterBatch, remove_multicrop_views, clean_images, generate_multicrop_views,
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
def load_exemplars(data, config_dict=Dict, conf_files=Dict) -> str:
    project = str(config_dict["tator"]["project"])
    short_name = get_short_name(project)

    logger.info(data)
    num_loaded = 0
    for label, save_dir in data:
        machine_friendly_label = gen_machine_friendly_label(label)
        # Grab the most recent file
        all_exemplars = list(Path(save_dir).rglob("*exemplars.csv"))
        logger.info(f"Found {len(all_exemplars)} exemplar files for {label}")
        exemplar_file = sorted(all_exemplars, key=os.path.getmtime, reverse=True)[0] if all_exemplars else None

        if exemplar_file is None:
            logger.info(f"No exemplar file found for {label}")
            return f"No exemplar file found for {label}"

        exemplar_count = 0
        with open(exemplar_file, "r") as f:
            exemplar_count = len(f.readlines())

        logger.info(f"Loading {exemplar_count} exemplars for {label} as {label} from {exemplar_file}")
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
        try:
            result = run_subprocess(args_list=args_list)
            if result != 0:
                logger.error(f"Error loading examplars to VSS: {result}")
                return f"Failed to load exemplars to VSS: {result}"
            logger.info(f"Loaded cluster exemplars for {label} from {exemplar_file}")
            num_loaded += 1
        except Exception as e:
            logger.error(f"Failed to load v exemplars for {label}: {e}")
            return f"Failed to load exemplars for {label}: {e}"

    return f"Loaded {num_loaded} labels"


# Beam pipeline
def run_pipeline(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Initialize the VSS database")
    example_project = Path(__file__).resolve().parent.parent / "projects" / "uav" / "config" / "config.yml"
    parser.add_argument("--config", required=True, help=f"Config file path, e.g. {example_project}")
    parser.add_argument("--clean", action="store_true", help="Clean previously downloaded data")
    parser.add_argument("--skip-download", required=False, default=False, help="Skip downloading data")
    parser.add_argument("--batch-size", required=False, type=int, default=1, help="Batch size")
    args, beam_args = parser.parse_known_args(argv)

    MIN_DETECTIONS = 2000
    batch_size = int(args.batch_size)
    args, other_args = parser.parse_known_args(argv)
    options = PipelineOptions(other_args)
    conf_files, config_dict = setup_config(args.config, silent=True)
    config_dict = parse_override_args(config_dict, other_args)

    download_path = Path(config_dict["data"]["processed_path"])
    labels = extract_labels_config(config_dict)

    # Print the new config
    logger.info("Configuration:")
    for key, value in config_dict.items():
        logger.info(f"{key}: {value}\n")

    if args.clean:
        clean(download_path.as_posix())

    # Always remove any previous augmented data before starting
    remove_multicrop_views(download_path.as_posix())

    # Set up the configuration for downloading
    download_args = config_dict["data"].get("download_args", []) # Get download arguments from config
    download_args = download_args.split(" ") if isinstance(download_args, str) else download_args # Convert to list if it's a string
    download_args = [arg for arg in download_args if arg] # Remove empty strings
    download_args.extend(["--crop-roi", "--resize", "224"])
    config_dict["data"]["download_args"] = download_args

    with beam.Pipeline(options=options) as p:
        (
            p
            | "Start download" >> beam.Create([labels])
            | "Download labeled data" >> beam.Map(download, conf_files=conf_files, config_dict=config_dict)
            | "Compute stats" >> beam.Map(compute_stats, config_dict=config_dict)
            | "Generate views" >> beam.Map(generate_multicrop_views)
            | "Clean bad examples" >> beam.Map(clean_images, config_dict=config_dict)
            | 'Batch cluster ROI elements' >> beam.FlatMap(lambda x: batch_elements(x, batch_size=batch_size))
            | 'Process cluster ROI batches' >> beam.ParDo(ProcessClusterBatch(config_dict=config_dict, min_detections=MIN_DETECTIONS))
            | "Load exemplars" >> beam.Map(load_exemplars, config_dict=config_dict, conf_files=conf_files)
            | "Log results" >> beam.Map(logger.info)
        )


if __name__ == "__main__":
    run_pipeline()
