# aipipeline, Apache-2.0 license
# Filename: projects/uav/cluster-pipeline.py
# Description: Batch process missions with sdcat clustering
import os
from datetime import datetime
from pathlib import Path

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import logging
import sys

from aipipeline.docker.utils import run_docker
from aipipeline.projects.uav.args_common import parse_args, POSSIBLE_PLATFORMS, parse_mission_string
from aipipeline.config_setup import setup_config

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
now = datetime.now()
log_filename = f"uav-cluster-pipeline-{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

ENVIRONMENT = os.getenv("ENVIRONMENT") if os.getenv("ENVIRONMENT") else None


def process_mission(element):
    # Data is in the format
    # <path>,<tator section>,<start image>,<end image>
    # /mnt/UAV/Level-1/trinity-2_20240702T153433_NewBrighton/SONY_DSC-RX1RM2,2024/07/NewBrighton,DSC00100.JPG,DSC00301.JPG
    logger.info(f"Processing element {element}")
    line, config_dict = element
    mission_name, mission_dir, section, start_image, end_image = parse_mission_string(line)

    base_path = Path(config_dict["data"]["processed_path_sdcat"]) / "seedDetections"
    project = config_dict["tator"]["project"]
    ini = config_dict["sdcat"]["ini"]
    model = config_dict["sdcat"]["model"]

    if not mission_name:
        logger.error(f"Could not find mission name in path: {line} that starts with {POSSIBLE_PLATFORMS}")
        return f"Could not find mission name in path: {line} that starts with {POSSIBLE_PLATFORMS}"


    det_dir = base_path / mission_name / "detections" / "combined" / model / "det_filtered"
    save_dir = base_path / mission_name / "detections" / "combined" / model / "clusters"

    if not det_dir.exists():
        logger.error(f"Could not find directory: {det_dir}")
        return

    if not save_dir.exists():
        os.makedirs(save_dir)

    args = [
        "cluster",
        "detections",
        "--config-ini",
        f"/tmp/{project}/{ini}",
        "--det-dir",
        str(det_dir),
        "--save-dir",
        str(save_dir),
        "--min-cluster-size",
        "3",
        "--device",
        "cuda:0",
        "--skip-visualization",
        "--use-vits"
    ]

    container = run_docker(
        image=config_dict["docker"]["sdcat"],
        name=f"sdcat-clu-{mission_name}",
        args_list=args,
        bind_volumes=config_dict["docker"]["bind_volumes"],
    )

    if ENVIRONMENT == "testing":
        return f"Mission {mission_name} would have been processed."

    if not container:
        logger.error(f"Failed to start container for mission {mission_name}")
        return

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

    logger.info("Starting cluster pipeline...")
    with beam.Pipeline(options=options) as p:
        (
            p
            | "Read missions" >> beam.io.ReadFromText(args.missions)
            | "Filter comments" >> beam.Filter(lambda line: not line.startswith("#"))
            | "Create elements" >> beam.Map(lambda line: (line, config_dict))
            | "Process missions (cluster)" >> beam.Map(process_mission)
        )


if __name__ == "__main__":
    run_pipeline(sys.argv)
