# aipipeline, Apache-2.0 license
# Filename: aipipeline/config_setup.py
# Description: Batch load images for missions
import shutil
from pathlib import Path
from typing import List, Dict, Tuple

import yaml
import os

from aipipeline.prediction.utils import logger


def extract_labels_config(config_dict) -> List[str]:
    logger.info(config_dict["data"]["labels"].split(","))
    return config_dict["data"]["labels"].split(",")


def check_config(config_dict: Dict) -> bool:
    # Check if the required keys are present in the configuration
    required_keys = ["tator", "vss", "data", "sdcat"]
    for key in required_keys:
        if key not in config_dict:
            logger.error(f"Missing key {key} in configuration file")
            return False

    # Required keys for the data section
    required_keys = ["labels", "processed_path"]
    for key in required_keys:
        if key not in config_dict["data"]:
            logger.error(f"Missing key {key} in data section of configuration file")
            return False

    return True


def setup_config(config_yml: str) -> Tuple[Dict, Dict]:
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
                    logger.info(f"Warning duplicate ey {merged.get(key, 0)} with value {value}")
            else:
                merged[key] = value
        return merged

    # Merge the two dictionaries
    merged_dict = merge_dicts(base_conf_dict, config_dict)

    # Pretty print the configuration
    logger.info("Configuration:")
    for key, value in merged_dict.items():
        logger.info(f"{key}: {value}\n")

    # Copy the config files to /tmp/project - project names are generally unique so no collision should occur
    project = merged_dict["tator"]["project"]
    config_files = {
        "config": f"/tmp/{project}/{config_path_yml.name}"
    }

    Path(f"/tmp/{project}").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(config_path_yml.as_posix(), f"/tmp/{project}/{config_path_yml.name}")

    ex_ini_path = Path(config_path_yml).parent / f"sdcat_exemplar.ini"
    if ex_ini_path.exists():
        shutil.copyfile(ex_ini_path, f"/tmp/{project}/{ex_ini_path.name}")
        config_files["exemplar"] = f"/tmp/sdcat_exemplar_{project}.ini"

    sd_ini_path = Path(config_path_yml).parent / f"sdcat_clu_det.ini"
    if sd_ini_path.exists():
        shutil.copyfile(ex_ini_path, f"/tmp/{project}/{sd_ini_path.name}")
        config_files["cluster"] = f"/tmp/{project}/{sd_ini_path.name}"

    return config_files, merged_dict
