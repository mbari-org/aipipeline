# aipipeline, Apache-2.0 license
# Filename: projects/i2mapbulk/load_pipeline_best_top2.py
# Description: Load detections into Tator from sdcat clustering
import os
from datetime import datetime

import apache_beam as beam
import dotenv
import tqdm
import pandas as pd
from apache_beam.options.pipeline_options import PipelineOptions
import logging

from aipipeline.projects.i2mapbulk.args import parse_args
from aipipeline.config_setup import setup_config
from mbari_aidata.plugins.loaders.tator.common import init_api_project

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
now = datetime.now()
log_filename = f"i2mapbulk-load-pipeline_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Constants
dotenv.load_dotenv()
TATOR_TOKEN = os.getenv("TATOR_TOKEN")


if not TATOR_TOKEN:
    logger.error("TATOR_TOKEN not found. Need to set in .env file")
    exit(-1)


def load(element, config_dict) -> str:
    # Data is in the format
    # <image base directory path to process>
    logger.info(f"Processing element {element}")
    all_detections = element

    # Get the project id and specific version id
    api, project_id = init_api_project(config_dict["tator"]["host"], TATOR_TOKEN, config_dict["tator"]["project"])

    # Get the minimum score to load
    load_min_score = config_dict["data"]["load_min_score"]

    # Bulk replace the detections, only keeping scores that sum to greater than the score threshold in the score and score_s columns
    # This captures both confident score and those that have confusion
    def filter_scores(x):
        return x["score"] + x["score_s"] >= load_min_score

    # Create a new row which is the filename without the extension - this is the loc_id
    def create_loc_id(x):
        return int(os.path.splitext(os.path.basename(x))[0])

    logger.info(f"Loading detections from {all_detections} with a minimum score of {load_min_score}...")
    df = pd.read_csv(all_detections)
    num_before = len(df)
    df = df[df.apply(filter_scores, axis=1)]
    df["loc_id"] = df["image_path"].apply(create_loc_id)
    num_after = len(df)
    logger.info(f"Filtered out {num_before - num_after} detections with a score less than {load_min_score}")

    # Assign the labels to the localizations
    for index, row in tqdm.tqdm(df.iterrows(), total=len(df)):
        loc_id = row["loc_id"]
        label = row["class"]
        label_s = row["class_s"]
        score = row["score"]
        score_s = row["score_s"]
        cluster = f'Unknown C{row["cluster"]}'
        logger.info(f"Assigning localizations for {loc_id}  to {label} {score} and second choice {label_s} {score_s}...")
        params = {
            "attributes": {"Label": label, "label_s": label_s, "score": score, "score_s": score_s, "cluster": cluster}
        }

        logger.debug(params)
        response = api.update_localization(loc_id, localization_update=params)
        logger.debug(response)

    return f"{all_detections} processed."


# Run the pipeline, reading missions from a file and skipping lines that start with #
def run_pipeline(argv=None):
    args, beam_args = parse_args(argv, logger)
    options = PipelineOptions()
    config_file, config_dict = setup_config(args.config)

    # Overwrite the config_dict with the command line arguments
    if args.min_score:
        config_dict["data"]["load_min_score"] = args.min_score

    with beam.Pipeline(options=options) as p:
        (
            p
            | "Data" >> beam.Create([args.data])
            | "Load csv" >> beam.Map(load, config_dict=config_dict)
            | "Log results" >> beam.Map(logger.debug)
        )


if __name__ == "__main__":
    run_pipeline()
