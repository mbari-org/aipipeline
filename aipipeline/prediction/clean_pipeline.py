# aipipeline, Apache-2.0 license
# Filename: projects/predictions/clean-pipeline.py
# Description: Crop images based on voc formatted data
from datetime import datetime
import dotenv
import logging
import os

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

from aipipeline.config_setup import setup_config
from aipipeline.prediction.library import clean_bad_images

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)
# and log to file
now = datetime.now()
log_filename = f"clean-pipeline_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Secrets
dotenv.load_dotenv()

class FindDirectories(beam.DoFn):
    def process(self, root_dir):
        if os.path.exists(root_dir) and os.path.isdir(root_dir):
            for name in os.listdir(root_dir):
                dir_path = os.path.join(root_dir, name)
                if os.path.isdir(dir_path):
                    yield dir_path

class RunCleanVision(beam.DoFn):
    def __init__(self, config):
        self.config = config  #

    def process(self, directory):
        element = None, directory, directory
        num_remaining, _, _ = clean_bad_images(element, self.config)
        result = f"Processed {directory} num_remaining {num_remaining}"
        yield result

# Run the pipeline
def run_pipeline(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Clean training images.")
    parser.add_argument("--config", required=True, help="Config file path")
    parser.add_argument("--image-dir", required=False, help="Directory containing images")
    args, beam_args = parser.parse_known_args(argv)
    _, config_dict = setup_config(args.config, silent=True)

    # Run the Apache Beam pipeline
    with beam.Pipeline(options=PipelineOptions()) as p:
        (p
        | "Create directory" >> beam.Create([args.image_dir])
         | "Find image directories" >> beam.ParDo(FindDirectories())
         | "Run clean vision" >> beam.ParDo(RunCleanVision(config_dict))
         | "Print Results" >> beam.Map(print)
         )

if __name__ == "__main__":
    run_pipeline()
