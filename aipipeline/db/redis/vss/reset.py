# aipipeline, Apache-2.0 license
# Filename: prediction/vss-reset.py
# Description: Reset the Vector Search Server (VSS) database. Removes all data from the VSS database.
from datetime import datetime

import dotenv
import os
import logging
import sys

from aipipeline.config_setup import setup_config
from aipipeline.engines.subproc import run_subprocess

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)
# and log to file
now = datetime.now()
log_filename = f"vss_reset_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Constants
dotenv.load_dotenv()
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")


def run_pipeline(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Reset the Vector Search Server (VSS) database.")
    parser.add_argument("--config", required=True, help="Config file path")
    args = parser.parse_args(argv)

    config_files, config_dict = setup_config(args.config)
    conf_temp = config_files["config"]

    if not os.getenv("REDIS_PASSWORD"):
        logger.error("REDIS_PASSWORD environment variable is not set.")
        return

    args_list = ["aidata", "db", "reset", "--redis-password", REDIS_PASSWORD, "--config", conf_temp]
    run_subprocess(args_list)


if __name__ == "__main__":
    run_pipeline(sys.argv[1:])
