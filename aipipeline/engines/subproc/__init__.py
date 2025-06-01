# aipipeline, Apache-2.0 license
# Filename: aipipeline/engines/subproc/__init__.py
# Description: Utilities for executing subprocesses within a pipeline
import logging
import os
import subprocess
from datetime import datetime
from typing import List

from aipipeline.engines.docker import logger, ENVIRONMENT

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
now = datetime.now()
log_filename = f"subproc-{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


def run_subprocess(
    args_list: List[str],
    env_list: List[str] = None,
):
    env = os.environ.copy()

    if env_list:
        env.update(dict(item.split('=', 1) for item in env_list))

    # Drop any empty arguments from args_list
    args_list = [arg for arg in args_list if arg]

    logger.info(f"Running command '{args_list}' with env {env_list}")

    if ENVIRONMENT == "testing":
        logger.info("Testing environment, skipping command execution")
        return

    try:
        process = subprocess.Popen(
            args_list,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        # Stream stdout live
        for line in process.stdout:
            logger.info(line.rstrip())

        return_code = process.wait()
        if return_code != 0:
            logger.error(f"Subprocess exited with return code {return_code}")
            return None
        logger.info("Subprocess completed successfully")
        return return_code

    except subprocess.SubprocessError as e:
        logger.error(f"Subprocess execution failed: {e}")
        return None
