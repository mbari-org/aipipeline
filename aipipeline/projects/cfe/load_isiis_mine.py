import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)
# and log to file
now = datetime.now()
log_filename = f"load_isiis_mine{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

if __name__ == "__main__":
    import multiprocessing
    import time

    time_start = time.time()

    out_path = Path.cwd() / 'output'
    (out_path / 'csv').mkdir(parents=True, exist_ok=True)
    (out_path / 'crop').mkdir(parents=True, exist_ok=True)

    # Read in all the csv files into a pandas dataframe
    # This will be used to filter the images that need to be processed
    df = pd.concat([pd.read_csv(f) for f in Path.cwd().rglob("*.csv")], ignore_index=True)

    # Find the unique image paths
    image_paths = df['image_path'].unique()

    # For each image path, load the media
    for image_path in image_paths:
        # Load the media
        pass

    time_end = time.time()
    logger.info(f"total processing time: {time_end - time_start}")
