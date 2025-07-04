# aipipeline, Apache-2.0 license
# Filename: projects/cfedeploy/load_isiis_video_pipeline.py
# Description: Batch load video for missions
import os
from datetime import datetime

import apache_beam as beam
import dotenv
from apache_beam.options.pipeline_options import PipelineOptions
import logging
import subprocess

from aipipeline.config_setup import setup_config
from aipipeline.projects.cfedeploy.args_common import parse_args, POSSIBLE_PLATFORMS, parse_mission_string

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
now = datetime.now()
log_filename = f"load-isiis-video{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Constants
dotenv.load_dotenv()
TATOR_TOKEN = os.getenv("TATOR_TOKEN")


def load_video(element) -> str:
    # Data is in the format below. Note there is some redundancy here, but this format allows for flexibility in the loading
    # <platform>,<mission path>,<tator section>
    # RachelCarson,/mnt/CFElab/Data_archive/Videos/ISIIS/COOK/VideosMP4/20230712_RachelCarson,RachelCarson/2023/07/
    logger.info(f"Processing element {element}")
    line, config_dict = element
    platform_name, mission_dir, section = parse_mission_string(line)

    if not platform_name:
        logger.error(f"Could not find platform name in path: {line} that ends with {POSSIBLE_PLATFORMS}")
        return f"Could not find platform name in path: {line} that ends with {POSSIBLE_PLATFORMS}"

    logger.info(f"Platform: {platform_name}")
    logger.info(f"Section: {section}")
    logger.info(f"Mission directory: {mission_dir}")

    project = config_dict["tator"]["project"]

    logger.info(f"Loading videos in {mission_dir} to Tator project {project} in section {section}")
    args = [
        "aidata",
        "load",
        "videos",
        "--input",
        mission_dir,
        "--config",
        f"/tmp/{project}/config.yml",
        "--token",
        TATOR_TOKEN,
        "--section",
        section,
    ]

    try:
        logger.info(f"Running command: {' '.join(args)}")

        try:
            proc = subprocess.run(args)
            if proc.returncode != 0:
                logger.error(f"Command failed with return code {proc.returncode}")
                return f"Command failed with return code {proc.returncode}"
            return f"Video loaded successfully."
        except subprocess.CalledProcessError as e:
            logger.error(f"Error occurred: {e}")
            return f"Error occurred: {e}"
    except Exception as e:
        logger.error(f"Error loading videos: {e}")
        return f"Error loading videos: {e}"
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
