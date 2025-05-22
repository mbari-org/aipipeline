# aipipeline, Apache-2.0 license
# Filename: projects/cfe/load_isiis_video_pipeline.py
# Description: Batch load video for missions
import os
from datetime import datetime
from pathlib import Path

import apache_beam as beam
import dotenv
from apache_beam.options.pipeline_options import PipelineOptions
import logging

from aipipeline.docker.utils import run_docker
from aipipeline.config_setup import setup_config
from aipipeline.projects.cfe.args_common import parse_args, POSSIBLE_PLATFORMS, parse_mission_string

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
now = datetime.now()
log_filename = f"load-isiis-video{now:%Y%m%d}.log"
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


def load_video(element) -> str:
    # Data is in the format
    # <mission path>,<tator section>
    # /mnt/CFElab/Data_archive/Videos/ISIIS/COOK/VideosMP4/20230712_RachelCarson,RachelCarson/2023/07/
    logger.info(f"Processing element {element}")
    line, config_dict = element
    platform_name, mission_dir, section = parse_mission_string(line)

    if not platform_name:
        logger.error(f"Could not find platform name in path: {line} that ends with {POSSIBLE_PLATFORMS}")
        return f"Could not find platform name in path: {line} that ends with {POSSIBLE_PLATFORMS}"

    logger.info(f"Platform: {platform_name}")

    project = config_dict["tator"]["project"]

    logger.info(f"Loading videos in {mission_dir} to Tator project {project} in section {section}")
    args = [
        "load",
        "videos",
        "--input",
        f"'{mission_dir}'",
        "--config",
        f"/tmp/{project}/config.yml",
        "--token",
        TATOR_TOKEN,
        "--section",
        section,
    ]

    try:
        container = run_docker(
            image=config_dict["docker"]["aidata"],
            name=f'isiisvidload{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            args_list=args,
            bind_volumes=config_dict["docker"]["bind_volumes"]
        )
        if container:
            logger.info(f"Video loading for {platform_name}...")
            container.wait()
            logger.info(f"Videos loaded for {platform_name}")
            return f"Mission {platform_name} videos loaded."
        else:
            logger.error(f"Failed to load videos for {platform_name}")
            return f"Failed to load Videos for {platform_name}"
    except Exception as e:
        logger.error(f"Error loading videos for {platform_name}: {e}")
        return f"Error loading videos for {platform_name}: {e}"



# Run the pipeline, reading missions from a file and skipping lines that start with #
def run_pipeline(argv=None):
    args, beam_args = parse_args(argv, logger)
    options = PipelineOptions(beam_args)
    overrides = {"tator": {"project": args.tator_project}}
    conf_files, config_dict = setup_config(args.config, overrides=overrides)
    with beam.Pipeline(options=options) as p:
        (
            p
            | "Read missions" >> beam.io.ReadFromText(args.missions)
            | "Filter comments" >> beam.Filter(lambda line: not line.startswith("#"))
            | "Create elements" >> beam.Map(lambda line: (line, config_dict))
            | "Process Missions (Load Videos)" >> beam.Map(load_video)
            | "Log results" >> beam.Map(logger.info)
        )


if __name__ == "__main__":
    run_pipeline()
