# aipipeline, Apache-2.0 license
# Filename: prediction/vss-remove.py
# Description: Remove entries from the Vector Search Server (VSS) database.
from datetime import datetime

import dotenv
import os
import logging
import sys

import redis

from aipipeline.config_setup import setup_config

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)
# and log to file
now = datetime.now()
log_filename = f"vss_remove_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Constants
dotenv.load_dotenv()
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")


def run_pipeline(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Remove entries from the Vector Search Server (VSS) database..")
    parser.add_argument("--config", required=True, help="Config file path")
    parser.add_argument("--doc", required=True, help="document to remove from the VSS database")
    args = parser.parse_args(argv)

    config_files, config_dict = setup_config(args.config)

    if not os.getenv("REDIS_PASSWORD"):
        logger.error("REDIS_PASSWORD environment variable is not set.")
        return

    # Connect to the VSS database
    redis_host = config_dict["redis"]["host"]
    redis_port = config_dict["redis"]["port"]
    redis_password = REDIS_PASSWORD

    r = redis.Redis(host=redis_host, port=redis_port, password=redis_password)

    logger.info(f"Removing hash {args.doc} from the VSS database...")

    # Find and delete keys matching the pattern
    num_deleted = 0
    for key in r.scan_iter(args.doc):
        r.delete(key)
        num_deleted += 1

    print(f"Deleted {num_deleted} keys.")


if __name__ == "__main__":
    run_pipeline(sys.argv[1:])
