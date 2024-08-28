# aipipeline, Apache-2.0 license
# Filename: projects/uav-901902/src/detect-pipeline.py
# Description: Batch process missions with sdcat detection
import os
from datetime import datetime

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.io import ReadFromText
from pathlib import Path
import logging

from aipipeline.docker.utils import run_docker
from aipipeline.projects.uav.args_common import parse_args, POSSIBLE_PLATFORMS
from config_setup import setup_config

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
now = datetime.now()
log_filename = f"uav-detect-pipeline-{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


ENVIRONMENT = os.getenv("ENVIRONMENT") if os.getenv("ENVIRONMENT") else None


def process_mission(element, config_dict: dict) -> str:
    mission = element
    if mission is None:
        logger.error("No mission provided.")
        return "No mission provided."

    base_path = Path(config_dict["data"]["processed_path"]) / "seedDetections"
    project = config_dict["tator"]["project"]
    clu_det_ini = config_dict["sdcat"]["clu_det_ini"]
    model = config_dict["sdcat"]["model"]
    config_ini = f"/tmp/{project}/{clu_det_ini}"

    mission_parts = mission.split(",")
    mission_dir = mission_parts[0]
    parts = list(Path(mission_dir).parts)

    # Find the first part that starts with a platform name
    for part in parts:
        if any([part.startswith(p) for p in POSSIBLE_PLATFORMS]):
            mission_name = part
            break

    if not mission_name:
        logger.error(f"Could not find mission name in path: {mission_dir} that starts with {POSSIBLE_PLATFORMS}")
        return f"Could not find mission name in path: {mission_dir}"

    start_image = mission_parts[2] if len(mission_parts) > 2 else None
    end_image = mission_parts[3] if len(mission_parts) > 3 else None

    save_dir = base_path / mission_name / "detections" / "combined"
    if not os.path.exists(mission_dir):
        logger.error(f"Could not find directory: {mission_dir}")
        return f"Could not find directory: {mission_dir}"

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    args = [
        "detect",
        "--device",
        "cuda:0",
        "--config-ini",
        config_ini,
        "--scale-percent",
        "40",
        "--model",
        model,
        "--slice-size-width",
        "900",
        "--slice-size-height",
        "900",
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

    return f"Mission {mission_name} processed."


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
            | "Create elements" >> beam.Map(lambda line: (line, config_dict))
            | "Process missions (cluster)" >> beam.Map(process_mission)
        )


if __name__ == "__main__":
    print(f"Logging captured to {log_filename}", flush=True)
    run_pipeline()
