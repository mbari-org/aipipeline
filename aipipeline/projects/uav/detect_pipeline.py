# aipipeline, Apache-2.0 license
# Filename: projects/uav/detect-pipeline.py
# Description: Batch process missions with sdcat detection
import multiprocessing
import os
import uuid
from datetime import datetime
from typing import Any

import apache_beam as beam
import pandas as pd
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.io import ReadFromText
from pathlib import Path
from multiprocessing import Pool
import logging
import io
import tqdm

from aipipeline.docker.utils import run_docker
from aipipeline.projects.uav.args_common import parse_args, POSSIBLE_PLATFORMS, parse_mission_string
from aipipeline.config_setup import setup_config, SDCAT_KEY
from aipipeline.prediction.library import run_vss
from aipipeline.prediction.utils import crop_square_image

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
now = datetime.now()
log_filename = f"uav_detect_pipeline_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


ENVIRONMENT = os.getenv("ENVIRONMENT") if os.getenv("ENVIRONMENT") else None


def run_mission_detect(element) -> Any:

    # Data is in the format
    # <path>,<tator section>,<start image>,<end image>
    # /mnt/UAV/Level-1/trinity-2_20240702T153433_NewBrighton/SONY_DSC-RX1RM2,2024/07/NewBrighton,DSC00100.JPG,DSC00301.JPG
    logger.info(f"Running mission detect {element}")
    line, config_dict, conf_files = element
    gpu_device, mission_name, mission_dir, section, start_image, end_image = parse_mission_string(line)

    base_path = Path(config_dict["data"]["processed_path_sdcat"]) / "seedDetections"
    model = config_dict["sdcat"]["model"]

    if not mission_name:
        logger.error(f"Could not find mission name in path: {mission_dir} that starts with {POSSIBLE_PLATFORMS}")
        return f"Could not find mission name in path: {mission_dir}"

    save_dir = base_path / mission_name / "detections" / "combined"
    if not os.path.exists(mission_dir):
        logger.error(f"Could not find directory: {mission_dir}")
        return f"Could not find directory: {mission_dir}"

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    args = [
        "detect",
        "--device",
        str(gpu_device),
        "--config-ini",
        conf_files[SDCAT_KEY],
        "--scale-percent",
        "50",
        "--model",
        model,
        "--slice-size-width",
        "1280",
        "--slice-size-height",
        "1280",
        "--conf",
        "0.1",
        "--save-dir",
        str(save_dir),
        "--image-dir",
        mission_dir,
    ]

    if start_image:
        args += ["--start-image", start_image]
    if end_image:
        args += ["--end-image", end_image]

    logger.debug(f"Starting detection for mission {mission_name}...")

    container = run_docker(
        image=config_dict["docker"]["sdcat"],
        name=f"sdcat-det-{mission_name}",
        args_list=args,
        bind_volumes=config_dict["docker"]["bind_volumes"],
    )

    if ENVIRONMENT == "testing":
        return f"Mission {mission_name} would have been processed."

    if not container:
        logger.error(f"Failed to start container for mission {mission_name}")
        return f"Mission {mission_name} failed to process."

    logger.info(f"Container {container.name} started.")
    for log in container.logs(stream=True):
        logger.info(log.decode("utf-8").strip())
    container.wait()
    logger.info(f"Container {container.name} finished.")

    return element

# Run the pipeline, reading missions from a file and skipping lines that start with #
def run_pipeline(argv=None):
    args, beam_args = parse_args(argv, logger)
    options = PipelineOptions(beam_args)
    conf_files, config_dict = setup_config(args.config)

    logger.info("Starting detect pipeline...")
    with beam.Pipeline(options=options) as p:
        (
            p
            | "Read missions" >> ReadFromText(args.missions)
            | "Filter comments" >> beam.Filter(lambda line: not line.startswith("#"))
            | "Create elements" >> beam.Map(lambda line: (line, config_dict, conf_files))
            | "Process missions (detect)" >> beam.Map(run_mission_detect)
        )

if __name__ == "__main__":
    print(f"Logging captured to {log_filename}", flush=True)
    run_pipeline()
