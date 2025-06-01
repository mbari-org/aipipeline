# aipipeline, Apache-2.0 license
# Filename: aipipeline/config_setup.py
# Description: Batch load images for missions
import shutil
from pathlib import Path
from typing import List, Dict, Tuple

import yaml
import os

from aipipeline.prediction.utils import logger

SDCAT_KEY = "sdcat"
CONFIG_KEY = "config"

def extract_labels_config(config_dict) -> List[str]:
    if config_dict["data"]["labels"]:
        labels = config_dict["data"]["labels"].split(",")
    else:
        labels = []
    logger.info(f'Extracted labels: {labels}')
    return labels


def check_config(config_dict: Dict) -> bool:
    # Check if the required keys are present in the configuration
    required_keys = ["tator", "vss", "data", "sdcat"]
    for key in required_keys:
        if key not in config_dict:
            logger.error(f"Missing key {key} in configuration file")
            return False

    # Required keys for the data section
    required_keys = ["labels", "processed_path", "download_args"]
    for key in required_keys:
        if key not in config_dict["data"]:
            logger.error(f"Missing key {key} in data section of configuration file")
            return False

    # Check if the .ini files are present in the configuration
    if "sdcat" in config_dict:
        if "ini" not in config_dict["sdcat"]:
            logger.error("Missing exemplar .ini file in configuration file")
            return False
    return True

def parse_labels(labels: str) -> Dict:
    config_path_yml = Path(labels)
    if not config_path_yml.exists():
        logger.error(f"Cannot find {config_path_yml}")
        exit(1)

    with config_path_yml.open("r") as file:
        try:
            config_dict = yaml.safe_load(file)
        except yaml.YAMLError as e:
            logger.error(f"Error reading YAML file: {e}")
            raise e

    return config_dict

def setup_config(config_yml: str, overrides: dict = {}, silent=False) -> Tuple[Dict, Dict]:
    config_path_yml = Path(config_yml)
    if not config_path_yml.exists():
        logger.error(f"Cannot find {config_path_yml}")
        exit(1)

    with config_path_yml.open("r") as file:
        try:
            config_dict = yaml.safe_load(file)
            if not check_config(config_dict):
                exit(1)
        except yaml.YAMLError as e:
            logger.error(f"Error reading YAML file: {e}")
            raise e

    # Get the default configuration from the YAML file in the same directory as this script
    # These settings don't change often and are generally the same for all projects
    with open(os.path.join(os.path.dirname(__file__), "config.yml"), "r") as file:
        try:
            base_conf_dict = yaml.safe_load(file)
        except yaml.YAMLError as e:
            logger.error(f"Error reading YAML file: {e}")
            raise e

    def merge_dicts(dict1, dict2):
        merged = dict1.copy()
        for key, value in dict2.items():
            if key in merged:
                if isinstance(merged[key], dict) and isinstance(value, dict):
                    merged[key] = merge_dicts(merged[key], value)  # Recursively merge nested dictionaries
            else:
                merged[key] = value
        return merged

    # Merge the two dictionaries
    merged_dict = merge_dicts(base_conf_dict, config_dict)

    # Pretty print the configuration
    if not silent:
        logger.info("Configuration:")
        for key, value in merged_dict.items():
            logger.info(f"{key}: {value}\n")

    # Apply any overrides
    merged_dict = merge_dicts(overrides, merged_dict)

    # Copy the config files to /tmp/project - project names are unique so no collision should occur
    project = merged_dict["tator"]["project"]
    ini = merged_dict["sdcat"]["ini"]

    # Prepare the config directory that stores the config files for use in the docker container
    config_root = Path(f"/tmp/{project}")
    config_root.mkdir(parents=True, exist_ok=True)

    sdcat_ini_path = Path(config_path_yml).parent / ini

    if not sdcat_ini_path.exists():
        logger.error(f"Cannot find {file}")
        exit(1)

    shutil.copyfile(sdcat_ini_path.as_posix(), f"/tmp/{project}/{sdcat_ini_path.name}")

    # Write the new yaml file to the config directory
    with open(f"/tmp/{project}/{config_path_yml.name}", "w") as file:
        yaml.dump(merged_dict, file)

    config_files = {CONFIG_KEY: f"/tmp/{project}/{config_path_yml.name}",
                    SDCAT_KEY: f"/tmp/{project}/{sdcat_ini_path.name}"}

    return config_files, merged_dict
