# aipipeline, Apache-2.0 license
# Filename: aipiipeline/db/redis/vss/init_vss_pipeline.py
# Description: Run the VSS initialization pipeline with special padded and rescale for plankivore ROIs
from datetime import datetime

import dotenv
import os
from pathlib import Path
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import logging

from aipipeline.config_args import parse_override_args
from aipipeline.config_setup import extract_labels_config, setup_config
from aipipeline.prediction.library import (
    download,
    compute_stats,
    clean,
    remove_multicrop_views,
    generate_multicrop_views,
    clean_images,
    cluster_collections
)
from aipipeline.db.redis.vss.exemplars import load_exemplars
from aipipeline.projects.planktivore.adjust_roi import pad_and_rescale

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.DEBUG)
# and log to file
now = datetime.now()
log_filename = f"ptvr_init_vss_pipeline{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Secrets
dotenv.load_dotenv()
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
TATOR_TOKEN = os.getenv("TATOR_TOKEN")


# Beam pipeline
def run_pipeline(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Initialize the VSS database with plankton data")
    example_project = Path(__file__).resolve().parent.parent / "projects" / "uav" / "config" / "config.yml"
    parser.add_argument("--config", required=True, help=f"Config file path, e.g. {example_project}")
    parser.add_argument("--clean", action="store_true", help="Clean previously downloaded data")
    parser.add_argument("--skip-download", required=False, default=False, help="Skip downloading data")

    MIN_DETECTIONS = 2000
    args, other_args = parser.parse_known_args(argv)
    options = PipelineOptions(other_args)
    conf_files, config_dict = setup_config(args.config, silent=True)
    config_dict = parse_override_args(config_dict, other_args)

    download_path = Path(config_dict["data"]["download_dir"])
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
    download_args.extend(["--crop-roi"])
    config_dict["data"]["download_args"] = download_args

    # Need to wrap this to handle the extra arg labels passed by beam from the "Download labeled data" step
    def _pad_and_rescale(input_path: Path) -> str:
        logger.info(f"Padding {input_path}")
        return pad_and_rescale(input_path, input_path)

    with beam.Pipeline(options=options) as p:
            download_data = (
                p
                | "Start download" >> beam.Create([labels])
                | "Download labeled data" >> beam.Map(download, conf_files=conf_files, config_dict=config_dict)
            )
            crop_path = download_data | beam.Map(lambda s: s + '/crops')
            (
                 crop_path
                | "Square ROIs" >> beam.Map(_pad_and_rescale, input_path=crop_path)
                | "Compute stats" >> beam.Map(compute_stats)
                | "Generate views" >> beam.Map(generate_multicrop_views)
                | "Clean bad examples" >> beam.Map(clean_images, config_dict=config_dict)
                | "Cluster examples" >> beam.Map(cluster_collections, config_dict=config_dict, min_detections=MIN_DETECTIONS)
                | "Load exemplars" >> beam.Map(load_exemplars, conf_files=conf_files)
                | "Log results" >> beam.Map(logger.info)
            )


if __name__ == "__main__":
    run_pipeline()
