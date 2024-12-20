# aipipeline, Apache-2.0 license
# Filename: projects/cfe/args_common.py
# Description: Batch process missions with sdcat clustering
from pathlib import Path
import os
import argparse

CONFIG_YAML = Path(__file__).resolve().parent / "config" / "config.yml"

# TODO: Add more platforms as needed - SHOULD BE IN CONFIG?
POSSIBLE_PLATFORMS = ["RachelCarson"]


def parse_args(argv, logger):
    parser = argparse.ArgumentParser(description="Batch process missions")
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
    # # The mission name is the string that includes a regexp with the platform name, e.g. <anything>-<platform>-<anything>
    mission_name = None
    for p in POSSIBLE_PLATFORMS:
        search = re.findall(fr'.*/-{p}', mission_dir)
        if search:
            mission_name = search[0].replace("/", "")
            break

    return mission_name, mission_dir, section
