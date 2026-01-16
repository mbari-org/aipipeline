# aipipeline, Apache-2.0 license
# Filename: projects/predictions/crop_pipeline.py
# Description: Crop images based on voc formatted data
from datetime import datetime
import logging
import apache_beam as beam

from aipipeline.config_setup import setup_config
from aipipeline.prediction.library import crop_rois_voc, report_stats

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


# Run the pipeline
def run_pipeline(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Crop localizations from VOC formatted data.")
    parser.add_argument("--config", required=True, help="Config file path")
    parser.add_argument("--images", required=True, help="Directory containing images")
    parser.add_argument("--xml", required=True, help="Directory containing xml")
    parser.add_argument("--output_dir", required=True, help="Directory to download crops to")
    args, beam_args = parser.parse_known_args(argv)
    conf_files, config_dict = setup_config(args.config)

    # Print the new config
    logger.info("Configuration:")
    for key, value in config_dict.items():
        logger.info(f"{key}: {value}\n")

    logger.info("Starting crop pipeline...")
    with beam.Pipeline() as p:
        (
            p
            | "Start" >> beam.Create([(args.xml, args.images, args.output_dir)])
            | "Download labeled data" >> beam.Map(crop_rois_voc, config_dict=config_dict)
            #| "Report stats" >> beam.Map(report_stats)
        )

if __name__ == "__main__":
    run_pipeline()
