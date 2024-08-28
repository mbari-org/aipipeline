# aipipeline, Apache-2.0 license
# Filename: projects/uav/args_common.py
# Description: Batch process missions with sdcat clustering
from pathlib import Path
import os
import argparse

CONFIG_YAML = Path(__file__).resolve().parent / "config" / "config.yml"

# TODO: Add more platforms as needed - SHOULD BE IN CONFIG?
POSSIBLE_PLATFORMS = ["trinity"]


def parse_args(argv, logger):
    parser = argparse.ArgumentParser(description="Batch process missions with sdcat clustering")
    parser.add_argument("--missions", required=True, help="File with missions to process")
    parser.add_argument("--config", required=True, help=f"Configuration files. For example: {CONFIG_YAML}")
    args, beam_args = parser.parse_known_args(argv)

    if not os.path.exists(args.missions):
        logger.error(f"Mission file {args.missions} not found")
        raise FileNotFoundError(f"Mission file {args.missions} not found")

    if not os.path.exists(args.config):
        logger.error(f"Config yaml {args.config} not found")
        raise FileNotFoundError(f"Config yaml {args.config} not found")

    return args, beam_args

def parse_mission_string(line: str):
    import re
    mission_parts = line.split(",")
    mission_dir = mission_parts[0]
    section = mission_parts[1]
    # # The mission name is the string that includes a regexp with the platform name, e.g. trinity-<anything>
    mission_name = None
    for p in POSSIBLE_PLATFORMS:
        search = re.findall(fr'{p}-.*/', mission_dir)
        if search:
            mission_name = search[0].replace("/", "")
            break

    start_image = mission_parts[2] if len(mission_parts) > 2 else None
    end_image = mission_parts[3] if len(mission_parts) > 3 else None
    return mission_name, mission_dir, section, start_image, end_image
