# aipipeline, Apache-2.0 license
# Filename: projects/predictions/crop_pipeline.py
# Description: Crop images based on voc formatted data
from datetime import datetime

import dotenv
import os
from apache_beam.options.pipeline_options import PipelineOptions
import logging

from aipipeline.config_setup import setup_config
from aipipeline.prediction.library import crop_rois_voc

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)
# and log to file
now = datetime.now()
log_filename = f"crop-pipeline_{now:%Y%m%d}.log"
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

    parser = argparse.ArgumentParser(description="Crop localizations from VOC formatted data.")
    parser.add_argument("--config", required=True, help="Config file path")
    parser.add_argument("--image-dir", required=False, help="Directory containing images")
    args, beam_args = parser.parse_known_args(argv)
    options = PipelineOptions(beam_args)
    conf_files, config_dict = setup_config(args.config, silent=True)
    processed_dir = config_dict["data"]["download_dir"]
    labels = config_dict["data"]["labels"].split(",")
    processed_data = config_dict["data"]["download_dir"]
    base_path = os.path.join(processed_data, config_dict["data"]["version"])
    if args.image_dir is None:
        image_dir = f"{base_path}/images",
    else:
        image_dir = args.image_dir

    # Print the new config
    logger.info("Configuration:")
    for key, value in config_dict.items():
        logger.info(f"{key}: {value}\n")

    crop_rois_voc(labels_filter=labels, image_dir=image_dir, processed_dir=processed_dir, config_dict=config_dict)

if __name__ == "__main__":
    run_pipeline()
