# aipipeline, Apache-2.0 license
# Filename: aipipeline/prediction/vss-predict-pipeline.py
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

from aipipeline.prediction.utils import top_majority
from aipipeline.config_setup import setup_config

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
REDIS_PASSWD = os.getenv("REDIS_PASSWD")
TATOR_TOKEN = os.getenv("TATOR_TOKEN")


def read_image(readable_file):
    with readable_file.open() as file:
        img = io.BytesIO(file.read()).getvalue()
        return img, readable_file.metadata.path


def process_image_batch(batch, config_dict):
    top_k = 3
    logger.info(f"Processing {len(batch)} images")
    project = config_dict["tator"]["project"]
    vss_threshold = float(config_dict["vss"]["threshold"])
    url_vs = f"{config_dict['vss']['url']}/{top_k}/{project}"
    url_load = config_dict["tator"]["url_load"]
    logger.debug(f"URL: {url_vs} threshold: {vss_threshold}")
    num_loaded = 0
    files = []
    for img, path in batch:
        files.append(("files", (path, img)))

    logger.info(f"Processing {len(files)} images with {url_vs}")
    response = requests.post(url_vs, headers={"accept": "application/json"}, files=files)
    logger.debug(f"Response: {response.status_code}")

    if response.status_code != 200:
        logger.error(f"Error processing images: {response.text}")
        return [f"Error processing images: {response.text}"]

    predictions = response.json()["predictions"]
    scores = response.json()["scores"]
    logger.debug(f"Predictions: {predictions}")
    logger.debug(f"Scores: {scores}")

    if len(predictions) == 0:
        img_failed = [x[0] for x in batch]
        return [f"No predictions found for {img_failed} images"]

    # Workaround for bogus prediction output - put the predictions in a list
    # 3 predictions per image
    ###
    batch_size = len(batch)
    predictions = [predictions[i:i + top_k] for i in range(0, batch_size * top_k, top_k)]
    ####
    # Skip if rhizaria, larvacean, copepod, fecal_pellet, centric_diatom, football, or larvacean are in the predictions
    low_confidence_labels = ["rhizaria", "copepod", "fecal_pellet", "centric_diatom", "football", "larvacean"]
    low_confidence_labels = ["copepod"]
    if not any([x in low_confidence_labels for x in predictions]):
        logger.info(f"=======>Did not find {low_confidence_labels}")
        return 0

    file_paths = [x[1][0] for x in files]
    for i, element in enumerate(zip(scores, predictions)):
        score, pred = element
        score = [float(x) for x in score]
        logger.info(f"Prediction: {pred} with score {score} for image {file_paths[i]}")
        best_pred, best_score = top_majority(pred, score, threshold=vss_threshold, max_p=False, majority_count=-1)

        if best_pred is None:
            logger.error(f"No majority prediction for {file_paths[i]}")
            continue

        logger.info(f"Best prediction: {best_pred} with score {best_score} for image {file_paths[i]}")

        # The database_id is the image file stem, e.g.  1925774.jpg -> 1925774
        database_id = int(Path(file_paths[i]).stem)

        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
        }
        data = {"loc_id": database_id, "project_name": project, "dry_run": False, "score": 1 - best_score}
        logger.debug(f"{url_load}/{best_pred}")
        response = requests.post(f"{url_load}/{best_pred}", headers=headers, json=data)
        if response.status_code == 200:
            logger.debug(f"Assigned label {best_pred} to {database_id}")
            num_loaded += 1
        else:
            logger.error(f"Error loading label {best_pred} to {database_id} {response.status_code} {response.text}")

    return num_loaded


def run_pipeline(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Process images with VSS")
    default_project = (
        Path(__file__).resolve().parent.parent.parent
        / "aipipeline"
        / "projects"
        / "uav-901902"
        / "config"
        / "config.yml"
    )
    parser.add_argument("--image_dir", required=True,
        help="Input image directory, e.g. /mnt/UAV/machineLearning/Unknown/Baseline/crops/Unknown/",
    )
    parser.add_argument("--config", required=False, default=default_project.as_posix(),
                        help="Config yaml file path")
    parser.add_argument("--batch_size", required=False, default=3, help="Batch size")
    parser.add_argument("--max_images", required=False,  help="Maximum number of images to process")
    args, beam_args = parser.parse_known_args(argv)
    options = PipelineOptions(beam_args)
    conf_files, config_dict = setup_config(args.config, silent=True)

    with beam.Pipeline(options=options) as p:
        (
            p
            | "MatchFiles" >> MatchFiles(file_pattern=f"{args.image_dir}*")
            | 'Limit Matches' >> beam.combiners.Sample.FixedSizeGlobally(int(args.max_images))
            | "FlattenMatches" >> beam.FlatMap(lambda x: x)
            | "ReadFiles" >> ReadMatches()
            | "ReadImages" >> beam.Map(read_image)
            | "BatchImages" >> beam.BatchElements(min_batch_size=3, max_batch_size=3)
            | "ProcessBatches" >> beam.Map(process_image_batch, config_dict)
            | "SumResults" >> beam.CombineGlobally(sum)
            | "WriteResults" >> beam.io.WriteToText("num_loaded")
            | "LogResults" >> beam.Map(logger.info)
        )


if __name__ == "__main__":
    run_pipeline()
