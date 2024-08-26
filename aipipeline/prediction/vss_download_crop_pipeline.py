# aipipeline, Apache-2.0 license
# Filename: projects/uav-901902/scripts/vss-download-crop-pipeline.py
# Description: Download dataset of images and prepare them running vss pipelines
from datetime import datetime

import dotenv
import os
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import logging

from config_setup import setup_config
from aipipeline.prediction.library import download, crop_rois, clean

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)
# and log to file
now = datetime.now()
log_filename = f"download-unknown-pipeline_{now:%Y%m%d}.log"
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

    parser = argparse.ArgumentParser(description="Download and cluster unknown images.")
    parser.add_argument("--label", required=True, help="Label to download and cluster")
    parser.add_argument("--config", required=True, help="Config file path")
    args, beam_args = parser.parse_known_args(argv)
    options = PipelineOptions(beam_args)
    conf_files, config_dict = setup_config(args.config)
    download_args = config_dict["data"]["download_args"]
    processed_data = config_dict["data"]["processed_path"]
    base_path = str(os.path.join(processed_data, config_dict["data"]["version"]))
    label_path = os.path.join(base_path, "crops", args.label)

    with beam.Pipeline(options=options) as p:
        p | "Start clean" >> beam.Create([label_path]) | "Clean Previously Downloaded Data" >> beam.Map(clean)
        (
            p
            | "Start download and cluster" >> beam.Create([args.label])
            | "Download labeled data" >> beam.Map(download, config_dict=config_dict, additional_args=download_args)
            | "Crop ROI" >> beam.Map(crop_rois, config_dict=config_dict)
            | "Log results" >> beam.Map(logger.info)
        )


if __name__ == "__main__":
    run_pipeline()
