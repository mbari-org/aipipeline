# aipipeline, Apache-2.0 license
# Filename: projects/uav/load-sdcat-pipeline.py
# Description: Load detections into Tator from sdcat clustering
import os
import tempfile
from datetime import datetime
from pathlib import Path

import apache_beam as beam
import dotenv
from apache_beam.options.pipeline_options import PipelineOptions
import logging

from pandas import read_csv

from aipipeline.projects.uav.args_common import parse_args, parse_mission_string, POSSIBLE_PLATFORMS
from aipipeline.docker.utils import run_docker
from aipipeline.config_setup import setup_config, CONFIG_KEY

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
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
TATOR_TOKEN = os.getenv("TATOR_TOKEN")

if not REDIS_PASSWORD:
    logger.error("REDIS_PASSWORD not found. Need to set in .env file")
    exit(-1)

if not TATOR_TOKEN:
    logger.error("TATOR_TOKEN not found. Need to set in .env file")
    exit(-1)


def load_mission(element) -> str:
    # Data is in the format
    # <path>,<tator section>,<start image>,<end image>
    # /mnt/UAV/Level-1/trinity-2_20240702T153433_NewBrighton/SONY_DSC-RX1RM2,2024/07/NewBrighton,DSC00100.JPG,DSC00301.JPG
    logger.info(f"Processing element {element}")
    line, config_files, config_dict, type = element
    mission_name, mission_dir, section, start_image, end_image = parse_mission_string(line)

    if not mission_name:
        logger.error(f"Could not find mission name in path: {line} that starts with {POSSIBLE_PLATFORMS}")
        return f"Could not find mission name in path: {line} that starts with {POSSIBLE_PLATFORMS}"

    logger.info(f"Mission name: {mission_name}")

    version = config_dict["data"]["version"]
    model = config_dict["sdcat"]["model"]
    base_dir = Path(config_dict["data"]["processed_path_sdcat"]) / "seedDetections"
    if type == "detect":
        load_file_or_dir = Path(base_dir) / mission_name / "detections" / "combined" / model / "det_filtered"
    elif type == "cluster":
        load_dir = Path(base_dir) / mission_name / "detections" / "combined" / model / "clusters"
        # Grab the most recent file
        all_detections = list(Path(load_dir).rglob("*cluster_detections.csv"))
        load_file_or_dir = sorted(all_detections, key=os.path.getmtime, reverse=True)[0] if all_detections else None
    else:
        logger.error(f"Type {type} not supported")
        return f"Type {type} not supported"

    if not load_file_or_dir.exists():
        logger.error(f"Could not find: {load_file_or_dir}")
        return f"Could not find: {load_file_or_dir}"

    load_min_score = config_dict["data"]["load_min_score"]

    with tempfile.TemporaryDirectory() as tmpdir:
        # Read in all the detections and filter out the ones below the min score in the score column
        if load_file_or_dir.is_dir():
            for d in load_file_or_dir.rglob("*.csv"):
                detections = read_csv(load_file_or_dir)
                detections = detections[detections["score"] >= load_min_score]
                detections.to_csv(Path(tmpdir) / d.name, index=False)
        else:
            detections = read_csv(load_file_or_dir)
            detections = detections[detections["score"] >= load_min_score]
            detections.to_csv(Path(tmpdir) / load_file_or_dir.name, index=False)

        logger.info(f"Loading {load_file_or_dir}")
        args = [
            "load",
            "boxes",
            "--input",
            load_file_or_dir.as_posix(),
            "--config",
            config_files[CONFIG_KEY],
            "--token",
            TATOR_TOKEN,
            "--version",
            version,
            "--exclude",
            "Poop",
            "--exclude",
            "Batray",
            "--exclude",
            "Wave",
            "--exclude",
            "Foam",
            "--exclude",
            "Reflectance",
        ]

        container = run_docker(
            image=config_dict["docker"]["aidata"],
            name=f"aidata-sdcat-load-{type}-{mission_name}",
            args_list=args,
            bind_volumes=config_dict["docker"]["bind_volumes"],
        )
        if container:
            logger.info(f"Loading {mission_name}....")
            container.wait()
            logger.info(f"Done loading {mission_name}....")
        else:
            logger.error(f"Failed to load {mission_name}....")

    return f"Mission {mission_name} processed."


# Run the pipeline, reading missions from a file and skipping lines that start with #
def run_pipeline(argv=None):
    args, beam_args = parse_args(argv, logger)
    options = PipelineOptions()
    config_file, config_dict = setup_config(args.config)

    # Must have a type
    if '--type' not in beam_args:
        logger.error("Type must be specified, e.g. --type detect or --type cluster")
        return

    # Convert extra args to a dictionary, e.g. --type detect -> {'--type': 'detect'}
    beam_args_dict = {}
    for i in range(0, len(beam_args), 2):
        beam_args_dict[beam_args[i]] = beam_args[i + 1]

    with beam.Pipeline(options=options) as p:
        (
            p
            | "Read missions" >> beam.io.ReadFromText(args.missions)
            | "Filter comments" >> beam.Filter(lambda line: not line.startswith("#"))
            | "Create elements" >> beam.Map(lambda line: (line, config_file, config_dict, beam_args_dict['--type']))
            | f"Load missions ({beam_args_dict['--type']})" >> beam.Map(load_mission)
            | "Log results" >> beam.Map(logger.info)
        )


if __name__ == "__main__":
    run_pipeline()
