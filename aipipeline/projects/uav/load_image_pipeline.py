# aipipeline, Apache-2.0 license
# Filename: projects/uav-901902/src/load-image-pipeline.py
# Description: Batch load images for missions
import os
from datetime import datetime
from typing import Dict

import apache_beam as beam
import dotenv
from apache_beam.options.pipeline_options import PipelineOptions
import logging

from aipipeline.docker.utils import run_docker
from aipipeline.config_setup import setup_config
from aipipeline.projects.uav.args_common import parse_args

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
now = datetime.now()
log_filename = f"load-image-pipeline_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Constants
dotenv.load_dotenv()
TATOR_TOKEN = os.getenv("TATOR_TOKEN")


def load_images(element, config_dict: Dict) -> str:
    # Data is in the format
    # <path>,<tator section>,<start image>,<end image>
    # /mnt/UAV/Level-1/trinity-2_20240702T153433_NewBrighton/SONY_DSC-RX1RM2,2024/07/NewBrighton,DSC00100.JPG,DSC00301.JPG
    mission = element
    mission_parts = mission.split(",")
    mission_dir = mission_parts[0]
    # The mission name is the string that includes trinity
    mission_path = mission_dir.split("/")
    for i, part in enumerate(mission_path):
        if "trinity" in part:
            mission_name = part
            break
    section = mission_dir.parts[1]
    start_image = mission_parts[2] if len(mission_parts) > 2 else None
    end_image = mission_parts[3] if len(mission_parts) > 3 else None

    project = config_dict["tator"]["project"]

    logger.info(f"Loading images for {input}")
    args = [
        "load",
        "images",
        "--input",
        input,
        "--config",
        f"/tmp/{project}/config.yml",
        "--token",
        TATOR_TOKEN,
        "--section",
        section,
    ]

    if start_image:
        args += ["--start-image", start_image]
    if end_image:
        args += ["--end-image", end_image]

    container = run_docker(
        config_dict["docker"]["aidata"],
        name=f"aidata-image-load-{mission_name}",
        args_list=args,
        bind_volumes=config_dict["docker"]["bind_volumes"]
    )
    if container:
        logger.info(f"Images loading for {mission}...")
        container.wait()
        logger.info(f"Images loaded for {mission}")
        return f"Mission {mission} images loaded."
    else:
        logger.error(f"Failed to load images for {mission}")
        return f"Failed to load images for {mission}"



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
