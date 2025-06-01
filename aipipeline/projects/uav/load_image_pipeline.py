# aipipeline, Apache-2.0 license
# Filename: projects/uav/src/load-image-pipeline.py
# Description: Batch load images for missions
import os
from datetime import datetime

import apache_beam as beam
import dotenv
from apache_beam.options.pipeline_options import PipelineOptions
import logging

from aipipeline.engines.subproc import run_subprocess
from aipipeline.config_setup import setup_config
from aipipeline.projects.uav.args_common import parse_args, POSSIBLE_PLATFORMS, parse_mission_string

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
now = datetime.now()
log_filename = f"load-image-pipeline_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)

# Constants
dotenv.load_dotenv()
TATOR_TOKEN = os.getenv("TATOR_TOKEN")


def load_images(element) -> str:
    # Data is in the format
    # <path>,<tator section>,<start image>,<end image>
    # /mnt/UAV/Level-1/trinity-2_20240702T153433_NewBrighton/SONY_DSC-RX1RM2,2024/07/NewBrighton,DSC00100.JPG,DSC00301.JPG
    logger.info(f"Processing element {element}")
    line, config_dict = element
    _, mission_name, mission_dir, section, start_image, end_image = parse_mission_string(line)

    if not mission_name:
        logger.error(f"Could not find mission name in path: {line} that starts with {POSSIBLE_PLATFORMS}")
        return f"Could not find mission name in path: {line} that starts with {POSSIBLE_PLATFORMS}"

    logger.info(f"Mission name: {mission_name}")

    project = config_dict["tator"]["project"]

    logger.info(f"Loading images in {mission_dir} to Tator project {project} in section {section}")
    args_list = [
        "aidata",
        "load",
        "images",
        "--input",
        mission_dir,
        "--config",
        f"/tmp/{project}/config.yml",
        "--token",
        TATOR_TOKEN,
        "--section",
        section,
    ]

    if start_image:
        args_list += ["--start-image", start_image]
    if end_image:
        args_list += ["--end-image", end_image]

    result = run_subprocess(args_list=args_list)
    if result != 0:
        logger.error(f"Failed to load images for {mission_name}")
        return f"Failed to load images for {mission_name}"
    logger.info(f"Images loaded for {mission_name}")
    return f"Mission {mission_name} images loaded."


# Run the pipeline, reading missions from a file and skipping lines that start with #
def run_pipeline(argv=None):
    args, beam_args = parse_args(argv, logger)
    options = PipelineOptions(beam_args)
    conf_files, config_dict = setup_config(args.config)
    with beam.Pipeline(options=options) as p:
        (
            p
            | "Read missions" >> beam.io.ReadFromText(args.missions)
            | "Filter comments" >> beam.Filter(lambda line: not line.startswith("#"))
            | "Create elements" >> beam.Map(lambda line: (line, config_dict))
            | "Process Missions (Load images)" >> beam.Map(load_images)
            | "Log results" >> beam.Map(logger.info)
        )


if __name__ == "__main__":
    run_pipeline()
