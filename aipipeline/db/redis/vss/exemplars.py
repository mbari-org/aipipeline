import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict

import dotenv

from aipipeline.config_setup import CONFIG_KEY
from aipipeline.engines.subproc import run_subprocess
from aipipeline.prediction.library import gen_machine_friendly_label

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)
# and log to file
now = datetime.now()
log_filename = f"vss_init_pipeline_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)
logger.addHandler(handler)

# Secrets
dotenv.load_dotenv()
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
TATOR_TOKEN = os.getenv("TATOR_TOKEN")

# Load exemplars into Vector Search Server
def load_exemplars(labels: List[tuple[str, str]], conf_files=Dict) -> str:

    logger.info(labels)
    num_loaded = 0
    for label, save_dir in labels:
        machine_friendly_label = gen_machine_friendly_label(label)
        # Grab the most recent file
        all_exemplars = list(Path(save_dir).rglob("*_exemplars.csv"))
        exemplar_file = sorted(all_exemplars, key=os.path.getmtime, reverse=True)[0] if all_exemplars else None

        if exemplar_file is None:
            logger.info(f"No exemplar file found for {label}")
            exemplar_count = 0
        else:
            with open(exemplar_file, "r") as f:
                exemplar_count = len(f.readlines())

        if exemplar_count < 500 or exemplar_file is None:
            all_detections = list(Path(save_dir).rglob("*_detections.csv"))
            exemplar_file = sorted(all_detections, key=os.path.getmtime, reverse=True)[0] if all_detections else None

            if exemplar_file is None:
                logger.info(f"No detections file found for {label}")
                continue

            with open(exemplar_file, "r") as f:
                exemplar_count = len(f.readlines())
            logger.info(f"To few exemplars, using detections file {exemplar_file} instead")

        logger.info(f"Loading {exemplar_count} exemplars for {label} as {machine_friendly_label} from {exemplar_file}")
        args_list = [
            "aidata",
            "load",
            "exemplars",
            "--input",
            f"'{exemplar_file}'",
            "--label",
            f"'{label}'",
            "--device",
            "cuda:0",
            "--password",
            REDIS_PASSWORD,
            "--config",
            conf_files[CONFIG_KEY],
            "--token",
            TATOR_TOKEN,
        ]


        try:
            result = run_subprocess(args_list=args_list)
            if result != 0:
                logger.error(f"Error loading exemplars to VSS: {result}")
                return f"Failed to load exemplars to VSS: {result}"
            logger.info(f"Loaded cluster exemplars for {label} from {exemplar_file}")
        except Exception as e:
            logger.error(f"Failed to load v exemplars for {label}: {e}")
            return f"Failed to load v exemplars for {label}: {e}"

    return f"Loaded {num_loaded} labels"

# Load exemplars into Vector Search Server
def load_exemplar(data, conf_files=Dict) -> str:
    logger.debug(data)
    num_loaded = 0
    _, label_path, save_dir = data
    label = Path(label_path).stem # Get the label from the path
    # Grab the most recent file
    all_exemplars = list(Path(save_dir).rglob("*exemplars.csv"))
    logger.info(f"Found {len(all_exemplars)} exemplar files for {label}")
    exemplar_file = sorted(all_exemplars, key=os.path.getmtime, reverse=True)[0] if all_exemplars else None

    if exemplar_file is None:
        logger.info(f"No exemplar file found for {label}")
        return f"No exemplar file found for {label}"

    with open(exemplar_file, "r") as f:
        exemplar_count = len(f.readlines())

    logger.info(f"Loading {exemplar_count} exemplars for {label} as {label} from {exemplar_file}")
    args_list = [
        "aidata",
        "load",
        "exemplars",
        "--input",
        f"{exemplar_file}",
        "--label",
        f"{label}",
        "--device",
        "cuda:0",
        "--password",
        REDIS_PASSWORD,
        "--config",
        conf_files[CONFIG_KEY]
    ]
    try:
        result = run_subprocess(args_list=args_list)
        if result != 0:
            logger.error(f"Error loading examplars to VSS: {result}")
            return f"Failed to load exemplars to VSS: {result}"
        logger.info(f"Loaded cluster exemplars for {label} from {exemplar_file}")
        num_loaded += 1
    except Exception as e:
        logger.error(f"Failed to load v exemplars for {label}: {e}")
        return f"Failed to load exemplars for {label}: {e}"

    return f"Loaded {num_loaded} labels"


def load_exemplars(elements, conf_files: Dict) -> str:
    logger.info(f"Loading {elements} ")
    for element in elements:
        load_exemplar(element, conf_files=conf_files)

    return f"Loaded {len(elements)} exemplar classes successfully"
