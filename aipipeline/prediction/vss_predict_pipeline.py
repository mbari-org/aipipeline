# aipipeline, Apache-2.0 license
# Filename: aipipeline/prediction/vss_predict_pipeline.py
# Description: Batch process missions with visual search server

import apache_beam as beam
import requests
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.io.fileio import MatchFiles, ReadMatches
import io
import logging
import os
from datetime import datetime
from pathlib import Path
import dotenv

from aipipeline.config_setup import setup_config
from aipipeline.prediction.library import run_vss

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.DEBUG)
# and log to file
now = datetime.now()
log_filename = f"vss_predict_pipeline_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Secrets
dotenv.load_dotenv()
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
TATOR_TOKEN = os.getenv("TATOR_TOKEN")


def read_image(readable_file):
    with readable_file.open() as file:
        img = io.BytesIO(file.read()).getvalue()
        return img, readable_file.metadata.path


def process_image_batch(batch, config_dict) -> int:
    url_load = config_dict["tator"]["url_load"]
    vss_threshold = float(config_dict["vss"]["threshold"])
    tator_project = config_dict["tator"]["project"]
    num_processed = 0
    try:
        logger.debug(f"Processing batch of {len(batch)} images")
        file_paths, best_predictions, best_scores = run_vss(batch, config_dict, top_k=3)
        for file_path, best_pred, best_score in zip(file_paths, best_predictions, best_scores):
            if best_pred is not None and best_score is not None and best_score > vss_threshold:
                # The database_id is the image file stem, e.g.  1925774.jpg -> 1925774
                database_id = int(Path(file_path).stem)

                headers = {
                    "accept": "application/json",
                    "Content-Type": "application/json",
                }
                data = {"loc_id": database_id, "project_name": tator_project, "dry_run": False, "score": best_score}
                logger.info(f"{url_load}/{best_pred}")
                response = requests.post(f"{url_load}/{best_pred}", headers=headers, json=data)
                if response.status_code == 200:
                    logger.debug(f"Assigned label {best_pred} score {best_score} to {database_id}")
                    num_processed += 1
                else:
                    logger.error(f"Error loading label {best_pred} to {database_id} {response.status_code} {response.text}")
                    exit(1)
    except Exception as ex:
        logger.error(f"Error processing batch: {ex}")

    return num_processed


def run_pipeline(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Process images with VSS")
    default_project = (
        Path(__file__).resolve().parent.parent.parent
        / "aipipeline"
        / "projects"
        / "uav"
        / "config"
        / "config.yml"
    )
    parser.add_argument("--image-dir", required=True,
        help="Input image directory, e.g. /mnt/UAV/machineLearning/Unknown/Baseline/crops/Unknown/",
    )
    parser.add_argument("--config", required=False, default=default_project.as_posix(),
                        help="Config yaml file path")
    parser.add_argument("--batch-size", required=False, default=3, help="Batch size")
    parser.add_argument("--max-images", required=False,  help="Maximum number of images to process")
    args, beam_args = parser.parse_known_args(argv)
    options = PipelineOptions(beam_args)
    conf_files, config_dict = setup_config(args.config, silent=True)

    with beam.Pipeline(options=options) as p:
        image_pcoll = (
                p
                | "MatchFiles" >> MatchFiles(file_pattern=f"{args.image_dir}*")
        )

        # Apply the limit conditionally
        if args.max_images:
            image_pcoll = (
                    image_pcoll
                    | 'Limit Matches' >> beam.combiners.Sample.FixedSizeGlobally(int(args.max_images))
                    | "FlattenMatches" >> beam.FlatMap(lambda x: x)
            )

        (
                image_pcoll
                | "ReadFiles" >> ReadMatches()
                | "ReadImages" >> beam.Map(read_image)
                | "BatchImages" >> beam.BatchElements(min_batch_size=1, max_batch_size=20)
                | "ProcessBatches" >> beam.Map(process_image_batch, config_dict)
                | "SumResults" >> beam.CombineGlobally(sum)
                | "WriteResults" >> beam.io.WriteToText("num_processed.txt")
                | "LogResults" >> beam.Map(logger.info)
        )


if __name__ == "__main__":
    run_pipeline()
