# aipipeline, Apache-2.0 license
# Filename: projects/uav-901902/scripts/load-sdcat-pipeline.py
# Description: Load detections into Tator from sdcat clustering
import os
from datetime import datetime
from pathlib import Path

import apache_beam as beam
import dotenv
from apache_beam.options.pipeline_options import PipelineOptions
import logging

from aipipeline.projects.uav.args_common import parse_args, parse_mission_string, POSSIBLE_PLATFORMS
from aipipeline.docker.utils import run_docker
from aipipeline.config_setup import setup_config

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
now = datetime.now()
log_filename = f"uav-load-sdcat-pipeline_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Constants
dotenv.load_dotenv()
REDIS_PASSWD = os.getenv("REDIS_PASSWD")
TATOR_TOKEN = os.getenv("TATOR_TOKEN")

if not REDIS_PASSWD:
    logger.error("REDIS_PASSWD not found. Need to set in .env file")
    exit(-1)

if not TATOR_TOKEN:
    logger.error("TATOR_TOKEN not found. Need to set in .env file")
    exit(-1)


def process_mission(element) -> str:
    # Data is in the format
    # <path>,<tator section>,<start image>,<end image>
    # /mnt/UAV/Level-1/trinity-2_20240702T153433_NewBrighton/SONY_DSC-RX1RM2,2024/07/NewBrighton,DSC00100.JPG,DSC00301.JPG
    logger.info(f"Processing element {element}")
    line, config_dict = element
    mission_name, mission_dir, section, start_image, end_image = parse_mission_string(line)

    if not mission_name:
        logger.error(f"Could not find mission name in path: {line} that starts with {POSSIBLE_PLATFORMS}")
        return f"Could not find mission name in path: {line} that starts with {POSSIBLE_PLATFORMS}"

    logger.info(f"Mission name: {mission_name}")

    project = config_dict["tator"]["project"]
    version = config_dict["data"]["version"]
    base_dir = Path(config_dict["data"]["processed_path"]) / "seedDetections"
    det_dir = Path(base_dir) / mission_name / "detections" / "combined" / "hustvl" / "yolos-tiny" / "clusters"

    if not det_dir.exists():
        logger.error(f"Could not find directory: {det_dir}")
        return f"Could not find directory: {det_dir}"

    # Find the first cluster file
    for det_index, det_file in enumerate(det_dir.glob("*cluster*.csv")):
        logger.info(f"Loading detections for {det_file}")
        args = [
            "load",
            "boxes",
            "--input",
            det_file.as_posix(),
            "--config",
            f"/tmp/{project}/config.yml",
            "--token",
            TATOR_TOKEN,
            "--version",
            version,
        ]

        container = run_docker(
            config_dict["docker"]["aidata"],
            name=f"aidata-sdcat-load-{mission_name}",
            args_list=args,
            bind_volumes=config_dict["docker"]["bind_volumes"],
        )
        if container:
            logger.info(f"Loading detections for {mission_name}....")
            container.wait()
            logger.info(f"Done loading detections for {mission_name}....")
        else:
            logger.error(f"Failed to load detections for {mission_name}....")

    return f"Mission {mission_name} processed."


# Run the pipeline, reading missions from a file and skipping lines that start with #
def run_pipeline(argv=None):
    args = parse_args(argv, logger)
    options = PipelineOptions()
    config_dict = setup_config(args.config)

    with beam.Pipeline(options=options) as p:
        (
            p
            | "Read missions" >> beam.io.ReadFromText(args.missions)
            | "Filter comments" >> beam.Filter(lambda line: not line.startswith("#"))
            | "Create elements" >> beam.Map(lambda line: (line, config_dict))
            | "Process missions (Cluster)" >> beam.Map(process_mission)
            | "Log results" >> beam.Map(logger.info)
        )


if __name__ == "__main__":
    run_pipeline()
