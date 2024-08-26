# aipipeline, Apache-2.0 license
# Filename: projects/uav-901902/src/cluster-pipeline.py
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
