# aipipeline, Apache-2.0 license
# Filename: aipipeline/db/download_crop_pipeline.py
# Description: Download dataset of images and prepare them running vss pipelines\
from datetime import datetime
from pathlib import Path

import dotenv
import os
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import logging

from aipipeline.config_args import parse_override_args
from aipipeline.config_setup import extract_labels_config, setup_config
from aipipeline.prediction.library import download, clean, compute_stats, generate_multicrop_views, \
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
    parser.add_argument("--clean", action="store_true", help="Clean previously downloaded data")
    parser.add_argument("--use-cleanvision", action="store_true", help="Clean bad data using cleanvision")
    parser.add_argument("--gen-multicrop", action="store_true", help="Artificially generate more data using multicrop")
    parser.add_argument("--labels", nargs="+", help="Labels to download, if not provided all labels will be downloaded")
    args, other_args = parser.parse_known_args(argv)
    options = PipelineOptions(other_args)
    conf_files, config_dict = setup_config(args.config, silent=True)
    config_dict = parse_override_args(config_dict, other_args)
    labels = args.labels if args.labels else [""]
    data = config_dict.get("data", {})
    download_path = Path(data.get("download_dir", "/tmp/downloads"))
    download_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Download path: {download_path}")

    # Print the new config
    logger.info("Configuration:")
    for key, value in config_dict.items():
        logger.info(f"{key}: {value}\n")

    if args.clean:
        clean(download_path.as_posix())

    # Always remove any previous augmented data before starting
    remove_multicrop_views(download_path.as_posix())

    # Set up the configuration for downloading
    download_args = data.get("download_args", []) # Get download arguments from config
    download_args = download_args.split(" ") if isinstance(download_args, str) else download_args # Convert to list if it's a string
    download_args = [arg for arg in download_args if arg] # Remove empty strings
    download_args.extend(["--crop-roi", "--resize", "224"])
    download_args = [arg.strip("'") for arg in download_args if arg.strip("'")]
    config_dict["data"]["download_args"] = download_args

    with beam.Pipeline(options=options) as p:
        download_data = (
                p
                | "Start download" >> beam.Create([labels])
                | "Download labeled data" >> beam.Map(download, conf_files=conf_files, config_dict=config_dict)
        )
        crop_path = download_data | beam.Map(lambda s: s + '/crops')

        download_views =  crop_path |"Compute stats" >> beam.Map(compute_stats)

        if args.gen_multicrop:
            download_views = (
                download_views
                | "Generate multicrop views" >> beam.Map(generate_multicrop_views)
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
