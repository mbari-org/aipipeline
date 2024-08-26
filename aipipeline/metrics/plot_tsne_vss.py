# aipipeline, Apache-2.0 license
# Filename: aipipeline/metrics/plot_tsne_vss.py
# Description: Batch process missions with visual search server classification
import os
import sys
from datetime import datetime
from pathlib import Path

from config_setup import setup_config

sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent.parent))
from aipipeline.metrics import gen_tsne_plot_vss
import dotenv
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)
# and log to file
now = datetime.now()
log_filename = f"vss-plot-tsne_vss_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Constants
dotenv.load_dotenv()
REDIS_PASSWD = os.getenv("REDIS_PASSWD")


def main(argv=None):
    import argparse

    example_project = Path(__file__).resolve().parent.parent / "projects" / "uav" / "config" / "config.yml"
    example_project = Path(__file__).resolve().parent.parent / "projects" / "biodiversity" / "config" / "config.yml"
    parser = argparse.ArgumentParser(description="Reset the Vector Search Server (VSS) database.")
    parser.add_argument("--config", required=False, help="Config file path", default=example_project)
    args = parser.parse_args(argv)

    _, config_dict = setup_config(args.config)

    if not os.getenv("REDIS_PASSWD"):
        logger.error("REDIS_PASSWD environment variable is not set.")
        return

    gen_tsne_plot_vss.plot_tsne(config_dict, REDIS_PASSWD)

if __name__ == "__main__":
    main()