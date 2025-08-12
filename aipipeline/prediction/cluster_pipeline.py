import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import dotenv
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

from aipipeline.config_setup import setup_config
from aipipeline.engines.docker import run_docker
from aipipeline.prediction.library import clean_bad_images

# Secrets
dotenv.load_dotenv()
TATOR_TOKEN = os.getenv("TATOR_TOKEN")

# Logging
logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)
# and log to file
now = datetime.now()
log_filename = f"i2mapbulk-cluster-pipeline-{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


def process(element, config_dict):
    # Data is in the format
    # <image base directory path to process>
    logger.info(f"Processing element {element}")
    _, image_dir, save_dir = element

    project = config_dict["tator"]["project"]
    ini = config_dict["sdcat"]["ini"]

    image_path = Path(image_dir)
    save_path = Path(save_dir)

    if not image_path.exists():
        logger.error(f"Could not find directory: {image_path}")
        return

    if not save_path.exists():
        os.makedirs(save_path.as_posix())

    # Run the clustering
    args = [
        "cluster",
        "roi",
        "--config-ini",
        f"/tmp/{project}/{ini}",
        "--roi-dir",
        str(image_path.as_posix()),
        "--save-dir",
        str(save_path.as_posix()),
        "--device",
        "cuda:0",
        "--use-vits"
    ]

    container = run_docker(
        image=config_dict["docker"]["sdcat"],
        name=f"sdcat-clu-{image_path.name}-{now:%Y%m%d.%f}",
        args_list=args,
        bind_volumes=config_dict["docker"]["bind_volumes"],
    )

    if not container:
        logger.error(f"Failed to start container for {image_path}")
        return

    try:
        logger.info(f"Container {container.name} started.")
        for log in container.logs(stream=True):
            logger.info(log.decode("utf-8").strip())
        container.wait()
        logger.info(f"Container {container.name} finished.")

        return f"{image_path} processed."
    except Exception as e:
        logger.error(f"Error processing {image_path}: {e}")
        return

def parse_line(element):
    logger.info(element)
    input, output = element.split(',')
    logger.info(f"Processing input: {input}, output: {output}")
    return 1, input, output

def parse_args(argv, logger):
    import argparse
    parser = argparse.ArgumentParser(description="Run the cluster pipeline.")
    parser.add_argument("--input", type=str, required=True, help="Path to the input data file containing image directories.",)
    parser.add_argument("--output", type=str, required=True, help="Path to the output directory to save the cluster results.",)
    parser.add_argument("--config", type=str, default="config.ini",help="Path to the configuration file.",)
    args, beam_args = parser.parse_known_args(argv)
    return args, beam_args

# Run the pipeline
def run_pipeline(argv=None):
    args, beam_args = parse_args(argv, logger)
    options = PipelineOptions(beam_args)
    conf_files, config_dict = setup_config(args.config)

    # If the input is a directory, create a list of image subdirectories within it
    if not os.path.isdir(args.input):
        logger.info(f"Input is not a directory, assuming it is a file with image directories: {args.input}")
        return

    input_dir = Path(args.input)
    image_dirs = [str(d) for d in input_dir.glob("**/*") if d.is_dir()]
    output_dirs = [Path(args.output) / d.name for d in input_dir.glob("**/*") if d.is_dir()]
    image_tuples = [(1, image_dir, output_dir) for image_dir, output_dir in zip(image_dirs, output_dirs)]

    logger.info("Starting cluster pipeline...")
    with beam.Pipeline(options=options) as p:
        (
            p
            | "Create elements" >> beam.Create(image_tuples)
            | "Clean data" >> beam.Map(clean_bad_images, config_dict=config_dict)
            | "Process (cluster)" >> beam.Map(process, config_dict=config_dict)
        )


if __name__ == "__main__":
    run_pipeline(sys.argv)


