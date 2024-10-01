# aipipeline, Apache-2.0 license
# Filename: projects/uav/detect-pipeline.py
# Description: Batch process missions with sdcat detection
import multiprocessing
import os
import uuid
from datetime import datetime
from typing import Any

import apache_beam as beam
import pandas as pd
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.io import ReadFromText
from pathlib import Path
from multiprocessing import Pool
import logging
import io
import tqdm

from aipipeline.docker.utils import run_docker
from aipipeline.projects.uav.args_common import parse_args, POSSIBLE_PLATFORMS, parse_mission_string
from aipipeline.config_setup import setup_config, SDCAT_KEY
from aipipeline.prediction.library import run_vss
from aipipeline.prediction.utils import crop_square_image

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
now = datetime.now()
log_filename = f"uav_detect_pipeline_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


ENVIRONMENT = os.getenv("ENVIRONMENT") if os.getenv("ENVIRONMENT") else None


def run_mission_detect(element) -> Any:

    # Data is in the format
    # <path>,<tator section>,<start image>,<end image>
    # /mnt/UAV/Level-1/trinity-2_20240702T153433_NewBrighton/SONY_DSC-RX1RM2,2024/07/NewBrighton,DSC00100.JPG,DSC00301.JPG
    logger.info(f"Running mission detect {element}")
    line, config_dict, conf_files = element
    mission_name, mission_dir, section, start_image, end_image = parse_mission_string(line)

    base_path = Path(config_dict["data"]["processed_path_sdcat"]) / "seedDetections"
    model = config_dict["sdcat"]["model"]

    if not mission_name:
        logger.error(f"Could not find mission name in path: {mission_dir} that starts with {POSSIBLE_PLATFORMS}")
        return f"Could not find mission name in path: {mission_dir}"

    save_dir = base_path / mission_name / "detections" / "combined"
    if not os.path.exists(mission_dir):
        logger.error(f"Could not find directory: {mission_dir}")
        return f"Could not find directory: {mission_dir}"

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    args = [
        "detect",
        "--device",
        "cuda:0",
        "--config-ini",
        conf_files[SDCAT_KEY],
        "--scale-percent",
        "50",
        "--model",
        model,
        "--slice-size-width",
        "1280",
        "--slice-size-height",
        "1280",
        "--conf",
        "0.1",
        "--save-dir",
        str(save_dir),
        "--image-dir",
        mission_dir,
    ]

    if start_image:
        args += ["--start-image", start_image]
    if end_image:
        args += ["--end-image", end_image]

    logger.debug(f"Starting detection for mission {mission_name}...")

    container = run_docker(
        image=config_dict["docker"]["sdcat"],
        name=f"sdcat-det-{mission_name}",
        args_list=args,
        bind_volumes=config_dict["docker"]["bind_volumes"],
    )

    if ENVIRONMENT == "testing":
        return f"Mission {mission_name} would have been processed."

    if not container:
        logger.error(f"Failed to start container for mission {mission_name}")
        return f"Mission {mission_name} failed to process."

    logger.info(f"Container {container.name} started.")
    for log in container.logs(stream=True):
        logger.info(log.decode("utf-8").strip())
    container.wait()
    logger.info(f"Container {container.name} finished.")

    return element


def read_image(file_path: str) -> tuple[bytes, str]:
    with open(file_path, 'rb') as file:
        img = io.BytesIO(file.read()).getvalue()
        return img, file_path


def run_mission_vss(element) -> str:

    # Data is in the format
    # <path>,<tator section>,<start image>,<end image>
    # /mnt/UAV/Level-1/trinity-2_20240702T153433_NewBrighton/SONY_DSC-RX1RM2,2024/07/NewBrighton,DSC00100.JPG,DSC00301.JPG
    logger.info(f"Running mission vss {element}")
    # If the element is not a tuple, return - this is a failed mission
    if not isinstance(element, tuple):
        logger.error(f"Failed mission: {element}")
        return f"Failed mission: {element}"

    line, config_dict, conf_files = element
    mission_name, mission_dir, section, start_image, end_image = parse_mission_string(line)

    base_path = Path(config_dict["data"]["processed_path_sdcat"]) / "seedDetections"
    base_path_scratch = Path(config_dict["data"]["processed_path"])
    model = config_dict["sdcat"]["model"]
    vss_threshold = float(config_dict["vss"]["threshold"])

    if not mission_name:
        logger.error(f"Could not find mission name in path: {mission_dir} that starts with {POSSIBLE_PLATFORMS}")
        return f"Could not find mission name in path: {mission_dir}"

    det_dir = base_path / mission_name / "detections" / "combined" / model / "det_filtered"
    if not os.path.exists(det_dir):
        return f"Could not find directory: {det_dir}"

    crop_path = base_path_scratch / model / "crops"
    if not os.path.exists(crop_path):
        os.makedirs(crop_path)

    # Get the file paths from the csv files, and run the vss prediction
    det_csv = list(det_dir.rglob("*.csv"))

    if len(det_csv) == 0:
        return f"No detections found in {det_csv}"

    det_df = pd.DataFrame()
    for d in det_csv:
        df = pd.read_csv(d)
        logger.info(f"Found {len(df)} detections in {d}")
        df['csv_file'] = d.as_posix()
        det_df = pd.concat([det_df, df])

    # Add in a column for the unique crop name for each detection with a unique id
    # unique uuid is based on the md5 hash of the box in the row
    det_df['crop_path'] = det_df.apply(lambda
                                    row: f"{crop_path}/{uuid.uuid5(uuid.NAMESPACE_DNS, str(row['x']) + str(row['y']) + str(row['xx']) + str(row['xy']))}.png",
                                    axis=1)

    # Only run if the class is "Unknown" with a saliency score greater than 300
    det_df = det_df[(det_df['class'] == "Unknown") & (det_df['saliency'] > 300)]
    if len(det_df) == 0:
        return f"No unknown detections found in {det_csv}"

    logger.info(f"Cropping {len(det_df)} detections for {mission_name}")
    for i in range(0, len(det_df), 500):
        df = det_df.iloc[i:i+500]
        num_processes = min(multiprocessing.cpu_count(), len(df))
        with Pool(num_processes) as pool:
            args = [(row, 224) for index, row in df.iterrows()]
            pool.starmap(crop_square_image, args)
        logger.info(f"Crop {i+500} of {len(det_df)} detections completed {mission_name}")
    logger.info(f"Crop {len(det_df)} detections completed {mission_name}")

    # iterate through the detections 32 at a time
    batch_size = 32
    for i in tqdm.tqdm(range(0, len(det_df), batch_size), desc=f"Processing {mission_name}"):
        try:
            # Read the images for the batch prediction
            images = []
            for index, row in det_df.iloc[i:i+batch_size].iterrows():
                images.append(read_image(row['crop_path']))

            file_paths, best_predictions, best_scores = run_vss(images, config_dict, top_k=3)

            # Update the dataframe with the best prediction
            for file_path, best_pred, best_score in zip(file_paths, best_predictions, best_scores):
                if best_pred is None:
                    logger.debug(f"No majority prediction for {file_path}")
                    det_df.loc[det_df['crop_path'] == file_path, 'class'] = "Unknown"
                    continue

                if best_score < vss_threshold:
                    logger.error(f"Score {best_score} below threshold {vss_threshold} for {file_path}")
                    continue

                logger.info(f"Best prediction: {best_pred} with score {best_score} for image {file_path}")

                det_df.loc[det_df['crop_path'] == file_path, 'class'] = best_pred
                det_df.loc[det_df['crop_path'] == file_path, 'score'] = best_score

        except Exception as ex:
            return str(ex)

    # Save the results back to the csv files
    for csv_file in det_csv:
        df_csv = det_df[det_df['csv_file'] == csv_file.as_posix()]
        df_csv = df_csv.drop(columns=['csv_file'])
        df_csv.to_csv(csv_file.as_posix(), index=False)

    return f"Mission {mission_name} processed."

# Run the pipeline, reading missions from a file and skipping lines that start with #
def run_pipeline(argv=None):
    args, beam_args = parse_args(argv, logger)
    options = PipelineOptions(beam_args)
    conf_files, config_dict = setup_config(args.config)

    logger.info("Starting detect pipeline...")
    with beam.Pipeline(options=options) as p:
        detect = (
            p
            | "Read missions" >> ReadFromText(args.missions)
            | "Filter comments" >> beam.Filter(lambda line: not line.startswith("#"))
            | "Create elements" >> beam.Map(lambda line: (line, config_dict, conf_files))
            | "Process missions (detect)" >> beam.Map(run_mission_vss)
        )

        # If --vss specified, run with vss prediction
        # if '--vss' in beam_args:
        #     detect | "Process missions (vss)" >> beam.Map(run_mission_vss)


if __name__ == "__main__":
    print(f"Logging captured to {log_filename}", flush=True)
    run_pipeline()
