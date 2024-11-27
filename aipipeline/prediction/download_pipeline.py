# aipipeline, Apache-2.0 license
# Filename: projects/predictions/download_pipeline.py
# Description: Download dataset
from datetime import datetime

import dotenv
import os
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import logging

from aipipeline.config_setup import setup_config
from aipipeline.prediction.library import download

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)
# and log to file
now = datetime.now()
log_filename = f"download-pipeline_{now:%Y%m%d}.log"
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

    parser = argparse.ArgumentParser(description="Download versioned data.")
    parser.add_argument("--config", required=True, help="Config file path")

    args, beam_args = parser.parse_known_args(argv)
    options = PipelineOptions(beam_args)
    conf_files, config_dict = setup_config(args.config, silent=True)

    labels = config_dict["data"]["labels"].split(",")


    with beam.Pipeline(options=options) as p:
        (
            p
            | "Start download" >> beam.Create([labels])
            | "Download labeled data" >> beam.Map(download, conf_files=conf_files, config_dict=config_dict)
            | "Log results" >> beam.Map(logger.info)
        )

    logger.info("Download pipeline completed.")
    logger.info(f"Downloaded to {config_dict['data']['processed_path']}/{config_dict['data']['version']}.")


if __name__ == "__main__":
    run_pipeline()
