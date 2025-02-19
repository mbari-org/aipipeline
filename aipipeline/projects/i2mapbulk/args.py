# aipipeline, Apache-2.0 license
# Filename: projects/i2mapbulk/args.py
# Description: Argument parser for bio projects

import argparse
import os
from pathlib import Path
from textwrap import dedent

DEFAULT_CONFIG_YAML = Path(__file__).resolve().parent / "config" / "config.yml"

def parse_args(argv, logger):
    parser = argparse.ArgumentParser(
        description=dedent("""\
        Run inference/clustering in bulk on images
        """),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--config", default=DEFAULT_CONFIG_YAML, required=False, help=f"Configuration files. Default: {DEFAULT_CONFIG_YAML}", type=str)
    parser.add_argument("--min-score", help="Minimum score for a classification to be valid.", required=False, type=float, default=0.7)
    parser.add_argument("--gpu-id", help="GPU ID to use for inference.", required=False, type=int, default=0)
    parser.add_argument("--data", help="Path to a text with path to the images to process or path to the processed csv file to load", required=True, type=str)
    args, beam_args = parser.parse_known_args(argv)
    if not os.path.exists(args.data):
        logger.error(f"Data file {args.data} not found")
        raise FileNotFoundError(f"Data file {args.data} not found")

    if not os.path.exists(args.config):
        logger.error(f"Config yaml {args.config} not found")
        raise FileNotFoundError(f"Config yaml {args.config} not found")

    return args, beam_args
