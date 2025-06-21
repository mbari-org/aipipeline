# aipipeline, Apache-2.0 license
# Filename: aipipeline/metrics/optimize_vss.py
# Description: Read in the vss performance file and optimize the VSS data based on the performance
import os
from datetime import datetime
import dotenv
import logging
import pandas as pd
from aipipeline.config_setup import setup_config

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# and log to file
now = datetime.now()
log_filename = f"vss_optimize{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Constants
dotenv.load_dotenv()
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
from pathlib import Path
import redis


def optimize(config: dict, password: str, csv_path: Path, min_instance: int = 1, min_score: float = 0.5):
    r = redis.Redis(
        host=config["redis"]["host"],
        port=config["redis"]["port"],
        password=password,
    )

    # Read in the csv file as a pandas dataframe
    # where the true_label is not the same as the pred_label and the score is greater than the threshold
    df = pd.read_csv(csv_path)
    df = df[(df["true_label"] != df["pred_label"]) & (df["predicted_score"] > min_score)]

    # Group by predicted_id and only remove those that occur more than min_instance times
    confused = df.groupby("predicted_id").filter(lambda x: len(x) > min_instance)

    # Get the unique predicted_ids that are confused
    confused = confused.drop_duplicates(subset="predicted_id")
    logger.info(f"Found {len(confused)} confused predicted_ids")

    # Remove the exemplar from the redis server
    for index, row in confused.iterrows():
        pred_label = row["pred_label"]
        key = f"doc:{pred_label}:{row['predicted_id']}"

        try:
            # Check if the key exists
            logger.info(f"Checking if {key} exists in the redis server")
            if r.exists(key):
                r.delete(key)
                logger.info(f"Removed {key} from the redis server")
            else:
                logger.info(f"{key} not found in the redis")
        except Exception as e:
            logger.error(f"Error removing {key} from the redis server: {e}")


def main(argv=None):
    import argparse

    example_project = Path(__file__).resolve().parent.parent / "projects" / "biodiversity" / "config" / "config.yml"
    parser = argparse.ArgumentParser(description="Calculate the accuracy of the vss")
    parser.add_argument("--config", required=False, help="Config file path", default=example_project)
    parser.add_argument("--confused-csv", required=True, help="CSV file path")
    parser.add_argument("--min-instance", required=False, help="Number of times the predicted_id must be falsely predicted to b "
                                                    "removed", default=1)
    parser.add_argument("--min-score", required=False, help="Minimum score for the predicted_id to be removed", default=0.90)
    args = parser.parse_args(argv)

    _, config_dict = setup_config(args.config)

    if not os.getenv("REDIS_PASSWORD"):
        logger.error("REDIS_PASSWORD environment variable is not set.")
        return

    optimize(config_dict, os.getenv("REDIS_PASSWORD"), Path(args.confused_csv), int(args.min_instance), float(args.min_score))


if __name__ == "__main__":
    main()
