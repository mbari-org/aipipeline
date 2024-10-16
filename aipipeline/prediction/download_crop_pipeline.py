# aipipeline, Apache-2.0 license
# Filename: projects/predictions/download-crop-pipeline.py
# Description: Download dataset of images and prepare them running vss pipelines
import glob
from datetime import datetime
from pathlib import Path

import dotenv
import os
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import logging

from aipipeline.config_setup import extract_labels_config, setup_config
from aipipeline.prediction.library import download, crop_rois_voc, clean

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)
# and log to file
now = datetime.now()
log_filename = f"download-crop-pipeline_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Secrets
dotenv.load_dotenv()
TATOR_TOKEN = os.getenv("TATOR_TOKEN")


# Run the pipeline
def run_pipeline(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Download and crop unknown images.")
    parser.add_argument("--config", required=True, help="Config file path")
    parser.add_argument("--labels", required=True, help="Comma separated list of labels to download")
    parser.add_argument("--download_args", required=False, default=[""], help="Additional arguments for download")
    parser.add_argument("--download_dir", required=True, help="Directory to download images")
    parser.add_argument("--skip_clean", required=False, default=False,
                                                    help="Skip cleaning of previously downloaded data")
    args, beam_args = parser.parse_known_args(argv)
    options = PipelineOptions(beam_args)
    conf_files, config_dict = setup_config(args.config, silent=True)
    download_args = config_dict["data"]["download_args"]

    if not os.path.exists(args.download_dir):
        os.makedirs(args.download_dir)

    # Override the config
    config_dict["data"]["labels"] = args.labels
    config_dict["data"]["download_args"] = args.download_args
    labels = args.labels.split(",")

    # Print the new config
    logger.info("Configuration:")
    for key, value in config_dict.items():
        logger.info(f"{key}: {value}\n")

    # Make sure the download directory is contained in the config docker mounts
    if "docker" in config_dict and "bind_volumes" in config_dict["docker"]:
        for mount in config_dict["docker"]["bind_volumes"]:
            if mount in args.download_dir:
                break
        else:
            raise ValueError(f"Download directory {args.download_dir} not in docker mounts")

    # Make sure the download directory is not a child of the processed directory - this is a safety check
    # Otherwise, the processed data could be deleted
    processed_dir = config_dict["data"]["processed_path"]
    if Path(args.download_dir).is_relative_to(processed_dir):
        raise ValueError(f"Download directory {args.download_dir} is a child of the processed directory {processed_dir}")

    if not args.skip_clean:
        clean(args.download_dir)

    with beam.Pipeline(options=options) as p:
        (
            p
            | "Start download" >> beam.Create([labels])
            | "Download labeled data" >> beam.Map(download, conf_files=conf_files, config_dict=config_dict, additional_args=download_args, download_dir=args.download_dir)
            | "Crop ROI" >> beam.Map(crop_rois_voc, config_dict=config_dict, processed_dir=args.download_dir)
            | "Log results" >> beam.Map(logger.info)
        )


if __name__ == "__main__":
    run_pipeline()
