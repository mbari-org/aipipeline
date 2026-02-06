# aipipeline, Apache-2.0 license
# Filename: aipiipeline/db/redis/vss/init_pipeline.py
# Description: Run the VSS initialization pipeline
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
    report_stats,
    clean,
    remove_multicrop_views,
    generate_multicrop_views,
    clean_images,
    cluster_collections
)
from aipipeline.db.redis.vss.exemplars import load_exemplars

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


# Beam pipeline
def run_pipeline(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Initialize the VSS database")
    example_project = Path(__file__).resolve().parent.parent / "projects" / "uav" / "config" / "config.yml"
    parser.add_argument("--config", required=True, help=f"Config file path, e.g. {example_project}")
    parser.add_argument("--clean", action="store_true", help="Clean previously downloaded data")
    parser.add_argument("--skip-download", action="store_true", help="Skip downloading data")
    parser.add_argument("--skip-generate-views", action="store_true", help="Skip generating multicrop views")
    parser.add_argument("--min-detections", type=int, default=2000, help="Minimum number of detections to cluster")

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
    download_args.extend(["--crop-roi", "--resize", "224", "--verified"])
    config_dict["data"]["download_args"] = download_args

    with beam.Pipeline(options=options) as p:
        if args.skip_download:
            logger.info("Skipping download step")
            crop_path = (
                p
                | "Skip download" >> beam.Create([config_dict["data"]["download_dir"]])
            )
        else:
            download_data = (
                p
                | "Start download" >> beam.Create([labels])
                | "Download labeled data" >> beam.Map(download, conf_files=conf_files, config_dict=config_dict)
            )
            crop_path = download_data | beam.Map(lambda s: s + '/crops')

        (
            crop_path
            | "Report stats" >> beam.Map(report_stats)
            | "Generate views" >> beam.Map(lambda path: path if args.skip_generate_views else generate_multicrop_views(path))
            | "Clean bad examples" >> beam.Map(clean_images, config_dict=config_dict)
            | "Cluster examples" >> beam.Map(cluster_collections, config_dict=config_dict, min_detections=args.min_detections)
            | "Load exemplars" >> beam.Map(load_exemplars, conf_files=conf_files)
        )


if __name__ == "__main__":
    run_pipeline()
