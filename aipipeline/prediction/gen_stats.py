# aipipeline, Apache-2.0 license
# Filename: aipipeline/prediction/gen_stats.py
# Description: Compute stats for downloaded datasets and save to a csv file
import json
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)
# and log to file
now = datetime.now()
log_filename = f"gen_stats_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


def run(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Compute stats for dataset.")
    parser.add_argument("--data", required=True, help="Root path for the dataset")
    parser.add_argument("--prefix", required=True, help="Prefix for the dataset")
    args, beam_args = parser.parse_known_args(argv)

    # Find all the stats.json files
    download_path = Path(args.data)
    combined_stats = {}
    logger.info(f"Computing stats for {download_path}")
    for d in download_path.rglob("stats.json"):
        logger.info(f"Found stats file: {d}")
        stats = json.load(d.open())
        for version, stat in stats.items():
            for k,v in stat.items():
                if k in combined_stats:
                    combined_stats[k] += int(v)
                else:
                    combined_stats[k] = int(v)

    # Sort the stats in descending order
    combined_stats = dict(sorted(combined_stats.items(), key=lambda x: x[1], reverse=True))

    # Save to a csv file
    output_path = download_path / f"{args.prefix}stats.csv"
    logger.info(f"Saving stats to {output_path}")
    with output_path.open("w") as f:
        f.write("label,count\n")
        for k,v in combined_stats.items():
            f.write(f"{k},{v}\n")

if __name__ == "__main__":
    run()
