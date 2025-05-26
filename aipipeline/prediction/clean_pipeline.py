# aipipeline, Apache-2.0 license
# Filename: projects/predictions/clean-pipeline.py
# Description: Clean bad images in a directory using CleanVision.
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
logger.setLevel(logging.DEBUG)
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
        logger.info(f"Searching for directories in {root_dir}")
        # If the root_dir contains no directories, yield the root_dir itself
        if not os.path.exists(root_dir):
            logger.warning(f"Root directory {root_dir} does not exist.")
            yield root_dir
            return
        if not os.path.isdir(root_dir):
            logger.warning(f"Root directory {root_dir} is not a directory.")
            yield root_dir
            return
        # Count the number of directories in the root_dir
        num_dirs = sum(os.path.isdir(os.path.join(root_dir, name)) for name in os.listdir(root_dir))
        logger.info(f"Found {num_dirs} directories in {root_dir}")

        if num_dirs == 0:
            # If no directories found, yield the root_dir itself
            logger.info(f"No directories found in {root_dir}, yielding the root directory.")
            yield root_dir
            return

        # If the root_dir contains directories, yield each directory path
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
    parser.add_argument("--image-dir", required=True, help="Directory containing images")
    args, beam_args = parser.parse_known_args(argv)
    _, config_dict = setup_config(args.config, silent=True)

    # Run the Apache Beam pipeline
    with beam.Pipeline(options=PipelineOptions()) as p:
        (p
        | "Create directory" >> beam.Create([args.image_dir])
         | "Find image directories" >> beam.ParDo(FindDirectories())
         | "Run clean vision" >> beam.ParDo(RunCleanVision(config_dict))
         | "Print Results" >> beam.Map(print)
         | "Log Results" >> beam.Map(lambda x: logger.info(x) if isinstance(x, str) else logger.info(str(x)))
         )

if __name__ == "__main__":
    run_pipeline()
