# aipipeline, Apache-2.0 license
# Filename: projects/cfe/args_common.py
# Description: Batch process missions with sdcat clustering
from pathlib import Path
import os
import argparse

CONFIG_YAML = Path(__file__).resolve().parent / "config" / "config.yml"

# TODO: Add more platforms as needed - SHOULD BE IN CONFIG?
POSSIBLE_PLATFORMS = ["RachelCarson", "scuba"]


def parse_args(argv, logger):
    parser = argparse.ArgumentParser(description="Batch process missions")
    parser.add_argument("--missions", required=True, help="File with missions to process")
    parser.add_argument("--config", required=True, help=f"Configuration files. For example: {CONFIG_YAML}")
    parser.add_argument("--tator-project", required=False, default="902111-CFE-Deployments", help="Override tator project")
    args, beam_args = parser.parse_known_args(argv)

    if not os.path.exists(args.missions):
        logger.error(f"Mission file {args.missions} not found")
        raise FileNotFoundError(f"Mission file {args.missions} not found")

    if not os.path.exists(args.config):
        logger.error(f"Config yaml {args.config} not found")
        raise FileNotFoundError(f"Config yaml {args.config} not found")

    return args, beam_args

def parse_mission_string(line: str):
    mission_parts = line.split(",")
    mission_dir = mission_parts[0]
    section = mission_parts[1]
    # The platform name is in the name of the mission directory
    # RachelCarson from
    # /mnt/CFELab/Data_archive/Images/ISIIS/COOK/VideosMP4/20230712_RachelCarson/2023-07-12\ 09-14-56.898,RachelCarson/2023/07
    platform_name = None
    for p in POSSIBLE_PLATFORMS:
        if p in mission_dir:
            platform_name = p
            break
    return platform_name, mission_dir, section
