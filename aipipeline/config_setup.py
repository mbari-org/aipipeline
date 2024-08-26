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


def setup_config(config_yml: str) -> Tuple[Dict, Dict]:
    config_path_yml = Path(config_yml)
    if not config_path_yml.exists():
        logger.error(f"Cannot find {config_path_yml}")
        exit(1)

    with config_path_yml.open("r") as file:
        try:
            config_dict = yaml.safe_load(file)
        except yaml.YAMLError as e:
            logger.error(f"Error reading YAML file: {e}")
            raise e

    # Pretty print the configuration
    logger.info("Configuration:")
    for k, v in config_dict.items():
        logger.info(f"{k}: {v}")

    # Copy the config files to /tmp/project - project names are generally unique so no collision should occur
    project = config_dict["tator"]["project"]
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

    return config_files, config_dict
