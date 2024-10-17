# aipipeline, Apache-2.0 license
# Filename: projects/predictions/crop-pipeline.py
# Description: Crop images based on voc formatted data
from datetime import datetime

import dotenv
import os
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import logging

from aipipeline.config_setup import extract_labels_config, setup_config
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
    args, beam_args = parser.parse_known_args(argv)
    options = PipelineOptions(beam_args)
    conf_files, config_dict = setup_config(args.config, silent=True)
    processed_dir = config_dict["data"]["processed_path"]
    labels = config_dict["data"]["labels"].split(",")

    # Print the new config
    logger.info("Configuration:")
    for key, value in config_dict.items():
        logger.info(f"{key}: {value}\n")

    with beam.Pipeline(options=options) as p:
        (
            p
            | "Extract labels" >> beam.Create([labels])
            | "Crop ROI" >> beam.Map(crop_rois_voc, config_dict=config_dict, processed_dir=processed_dir)
            | "Log results" >> beam.Map(logger.info)
        )


if __name__ == "__main__":
    run_pipeline()
