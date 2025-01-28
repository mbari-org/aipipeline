# aipipeline, Apache-2.0 license
# Filename: aipipeline/prediction/download_crop_pipeline.py
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
from aipipeline.prediction.library import download, crop_rois_voc, clean, compute_stats, generate_multicrop_views, \
    clean_images, remove_multicrop_views

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
    parser.add_argument("--labels", required=False, help="Comma separated list of labels to download")
    parser.add_argument("--download-dir", required=False, help="Directory to download images")
    parser.add_argument("--version", required=False, help="Version of the dataset")
    parser.add_argument("--skip-clean", required=False, default=False,
                                                    help="Skip cleaning of previously downloaded data")
    parser.add_argument("--use-cleanvision", required=False,
                                                    help="Clean of bad data using cleanvision")
    args, beam_args = parser.parse_known_args(argv)
    options = PipelineOptions(beam_args)
    conf_files, config_dict = setup_config(args.config, silent=True)

    if args.download_dir:
        download_path = Path(args.download_dir)
    else:
        download_path = Path(config_dict["data"]["processed_path"])

    if args.version:
        config_dict["data"]["version"] = args.version

    if args.labels:
        config_dict["data"]["labels"] = args.labels

    labels = extract_labels_config(config_dict)

    # Print the new config
    logger.info("Configuration:")
    for key, value in config_dict.items():
        logger.info(f"{key}: {value}\n")

    # Make sure the download directory is contained in the config docker mounts
    if "docker" in config_dict and "bind_volumes" in config_dict["docker"]:
        for mount in config_dict["docker"]["bind_volumes"]:
            if mount in download_path.as_posix():
                break
        else:
            raise ValueError(f"Download directory {args.download_dir} not in docker mounts")

    # Make sure the download directory is not a child of the processed directory - this is a safety check
    # Otherwise, the processed data could be deleted
    bind_volumes = config_dict["docker"]["bind_volumes"].keys()
    # Check if the download directory is a child of any bind volumes in the docker config
    found = False
    for volume in bind_volumes:
        if download_path.is_relative_to(volume):
            found = True
            break
    if not found:
        raise ValueError(
            f"Download directory {args.download_dir} is not a child of any of the bind volumes in the docker config")

    version_path = download_path / config_dict["data"]["version"]
    if not args.skip_clean:
        clean(version_path.as_posix())

    # Always remove any previous augmented data before starting
    remove_multicrop_views(version_path.as_posix())

    if args.download_dir:
        config_dict["data"]["processed_path"] = args.download_dir

    download_args = config_dict["data"]["download_args"]
    download_args.extend(["--crop-roi", "--resize", "224"])
    config_dict["data"]["download_args"] = download_args

    with beam.Pipeline(options=options) as p:
        download_views = (
            p
            | "Start download" >> beam.Create([labels])
            | "Download labeled data" >> beam.Map(download, conf_files=conf_files, config_dict=config_dict)
            | "Compute stats" >> beam.Map(compute_stats, config_dict=config_dict)
            | "Generate views" >> beam.Map(generate_multicrop_views)
        )
        if args.use_cleanvision:
          (
            download_views
            | "Clean bad examples" >> beam.Map(clean_images, config_dict=config_dict)
            | "Log results" >> beam.Map(logger.info)
         )
        else:
            (
            download_views
            | "Log results" >> beam.Map(logger.info)
            )


if __name__ == "__main__":
    run_pipeline()
