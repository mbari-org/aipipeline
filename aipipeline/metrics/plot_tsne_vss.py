# aipipeline, Apache-2.0 license
# Filename: aipipeline/metrics/plot_tsne_vss.py
# Description: Batch process missions with visual search server classification
import datetime
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import redis
from matplotlib import pyplot as plt
from redis.commands.search.query import Query
from sklearn.manifold import TSNE

from aipipeline.config_setup import setup_config

sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent.parent))
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

def convert_redis_vector_to_float(vector_np):
    return np.frombuffer(vector_np, dtype=np.float32)


def extract_name(input_str):
    match = re.match(r"^(.*?)(?=_[0-9]+)", input_str)
    return match.group(1) if match else None


def download_data(r: redis.Redis, page_size=50):
    # Get all hashes from the index
    query = Query("*").return_fields("id").return_field("vector", decode_field=False)
    total_vectors = []
    total_class_names = []
    offset = 0
    while True:
        query.paging(offset, page_size)
        results = r.ft("index").search(query)
        vectors = [convert_redis_vector_to_float(result.vector) for result in results.docs]
        names = [extract_name(result.id.split("doc:")[-1]) for result in results.docs]
        total_vectors.extend(vectors)
        total_class_names.extend(names)
        if len(vectors) < page_size:
            break
        offset += page_size

    return total_vectors, total_class_names


def plot_tsne(config: dict, password: str):
    try:
        host = config["redis"]["host"]
        port = config["redis"]["port"]
        project = config["tator"]["project"]

        logging.info(f"Connecting to Redis at {host}:{port}")
        # Get the redis connection
        r = redis.Redis(host, port, password=password)

        vectors, class_names = download_data(r)
        logging.info(f"Downloaded {len(vectors)} vectors from Redis")

        if len(vectors) == 0:
            logging.error("No vectors found in Redis. Exiting.")
            return

        tsne = TSNE(n_components=2, random_state=0)
        class_idx = np.unique(class_names, return_inverse=True)[1]

        final_vectors = []
        for i in range(len(vectors)):
            n = vectors[i] + [class_idx[i]]
            final_vectors.append(n)

        logging.info(f"Final vectors: {len(final_vectors)}")

        v = np.array(final_vectors)
        vectors_2d = tsne.fit_transform(v)
        logging.info(f"t-SNE completed on {len(v)} vectors")

        # Plot the t-SNE results, colored by class
        plt.figure(figsize=(12, 12))

        colors = [
            (1, 0, 0),
            (0, 1, 0),
            (0, 0, 1),
            (1, 1, 0),
            (1, 0, 1),
            (0, 1, 1),
            (0.5, 0.5, 0),
            (0.5, 0, 0.5),
            (0, 0.5, 0.5),
            (0.5, 0.5, 0.5),
            (0.5, 0, 0),
            (0, 0.5, 0),
            (0, 0, 0.5),
            (0.5, 0.5, 0),
            (0.25, 0, 0.5),
            (0, 0, 0),
        ]

        # Assign a color to each class, up to 16 classes then repeat
        colors = colors * (len(np.unique(class_names)) // 16 + 1)

        for i, class_name in enumerate(np.unique(class_names)):
            plt.scatter([], [], c=colors[i], label=class_name, s=10)

        # Adjust the plot to make room for the legend
        plt.subplots_adjust(right=0.75)

        # Customize and place the legend outside the plot
        plt.legend(loc="center left", bbox_to_anchor=(1, 0.5), title="Classes")
        plt.suptitle(f"t-SNE of 768-dimensional vectors {project} exemplars")
        d = f"{datetime.now():%Y-%m-%d %H:%M:%S}"
        plt.title(d)

        # Plot the t-SNE results, colored by class
        for i, class_name in enumerate(class_names):
            x, y = vectors_2d[i]
            idx = np.where(np.unique(class_names) == class_name)[0][0]
            plt.scatter(x, y, c=colors[idx], label=class_name, s=10, alpha=0.5)

        logging.info(f"Saving plot to tsne_plot_{project}_{d}.png")
        plt.savefig(f"tsne_plot_{project}_{d}.png")
        plt.show()
    except Exception as e:
        logging.exception(f"Error: {e}")
        if "index: no such index" in str(e):
            logging.info("Redis database not initialized.")


def main(argv=None):
    import argparse

    example_project = Path(__file__).resolve().parent.parent / "projects" / "biodiversity" / "config" / "config.yml"
    parser = argparse.ArgumentParser(description="Reset the Vector Search Server (VSS) database.")
    parser.add_argument("--config", required=False, help="Config file path", default=example_project)
    args = parser.parse_args(argv)

    _, config_dict = setup_config(args.config)

    if not os.getenv("REDIS_PASSWD"):
        logger.error("REDIS_PASSWD environment variable is not set.")
        return

    plot_tsne(config_dict, REDIS_PASSWD)

if __name__ == "__main__":
    main()