# aipipeline, Apache-2.0 license
# Filename: projects/uav/load_isiis_clusters_pipeline.py
# Description: Load detections into Tator from sdcat clustering
import argparse
import os
from datetime import datetime
from pathlib import Path
from textwrap import dedent

import apache_beam as beam
import dotenv
import pandas as pd
from apache_beam.options.pipeline_options import PipelineOptions
import logging

from aipipeline.config_setup import setup_config
from aipipeline.db.utils import get_box_type, get_video_type, init_api_project, get_media_ids, format_attributes
from aipipeline.db.utils import get_version_id, gen_spec, load_bulk_boxes

# Secrets
dotenv.load_dotenv()
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
TATOR_TOKEN = os.getenv("TATOR_TOKEN")

# Logging
logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)
# and log to file
now = datetime.now()
log_filename = f"process_video_pipeline_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

def load(element, config_dict) -> str:
    # Data is in the format
    # <image base directory path to process>
    logger.info(f"Processing element {element}")
    all_detections = element

    try:
        # Get needed database ids and attributes for loading from the project config
        api, project = init_api_project(config_dict["tator"]["host"], TATOR_TOKEN, config_dict["tator"]["project"])
        project_id = project.id
        version = config_dict["data"]["version"]
        logger.info(f"Loading to version {version} in project {config_dict['tator']['project']} id {project_id}")
        version_id = get_version_id(api, project_id, version)
        video_type = get_video_type(api, project_id)
        box_type = get_box_type(api, project_id)
        box_attributes = config_dict["tator"]["box"]["attributes"]

        logger.info(f"Loading cluster detections from {all_detections}")
        df = pd.read_csv(all_detections)

        media_map = get_media_ids(api, project, video_type.id)

        # Assign the labels to the localizations, batching by 500
        batch_size = 500
        for i in range(0, len(df), batch_size):
            batch_df = df.iloc[i : i + batch_size]
            logger.info(f"Creating {len(batch_df)} localizations ...")

            specs = []
            for index, row in batch_df.iterrows():
                # /mnt/CFElab/Data_archive/Images/ISIIS/COOK/Videos2frames/20250401_Hawaii_allframes/20250404_scuba/2025-04-04 11-41-36.032/CFE_ISIIS-012-2025-04-04 11-43-06.238_0355.jpg
                image_path = Path(row["image_path"])

                # 2025-04-04 11-41-36.032.mp4
                video_name = Path(row["image_path"]).parent.name # extract the video name from the image path
                logger.info(f"Processing image {image_path}")

                # Get the frame number from the image name
                # 0355 from 2025-04-04 11-43-06.238_0355.jpg
                frame_number = int(image_path.name.split("_")[-1].split(".")[0])

                # Get the video name from the image path
                # 025-04-04 11-43-06.238.mp4 from 2025- 04-04 11-43-06.238_0355.jpg
                video_name = image_path.name.split(f"_{frame_number:04}")[0] + ".mp4"

                if video_name not in media_map.keys():
                    logger.info(f'No video found with name {image_path} in project {config_dict["tator"]["project"]}.')
                    logger.info("Video must be loaded before localizations.")
                    continue

                attributes = format_attributes(row, box_attributes)
                specs.append(
                    gen_spec(
                        box=[row["x"], row["y"], row["xx"], row["xy"]],
                        version_id=version_id,
                        label=row["class"],
                        attributes=attributes,
                        frame_number=int(frame_number),
                        type_id=box_type.id,
                        media_id=media_map[video_name],
                        project_id=project_id
                    )
                )
            box_ids = load_bulk_boxes(project_id, api, specs)
            logger.info(f"Loaded {len(box_ids)} boxes of {len(df)} into Tator")

        return f"{all_detections} loaded."
    except Exception as e:
        logger.error(f"Error loading {all_detections}: {e}")
        return f"Error loading {all_detections}: {e}"


def parse_args(argv, logger):
    parser = argparse.ArgumentParser(
        description=dedent("""\
        Load detections into Tator from sdcat clustering from ISIIS frames extracted from videos
        """),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--config", required=True, help=f"Configuration files", type=str)
    parser.add_argument("--data", help="Path to cluster csv file to load", required=True, type=str)
    args, beam_args = parser.parse_known_args(argv)
    if not os.path.exists(args.data):
        logger.error(f"Data file {args.data} not found")
        raise FileNotFoundError(f"Data file {args.data} not found")

    if not os.path.exists(args.config):
        logger.error(f"Config yaml {args.config} not found")
        raise FileNotFoundError(f"Config yaml {args.config} not found")

    return args, beam_args

# Run the pipeline, reading deployments from a file and skipping lines that start with #
def run_pipeline(argv=None):
    args, beam_args = parse_args(argv, logger)
    options = PipelineOptions()
    config_file, config_dict = setup_config(args.config)

    with beam.Pipeline(options=options) as p:
        (
            p
            | "Data" >> beam.Create([args.data])
            | "Load csv" >> beam.Map(load, config_dict=config_dict)
            | "Log results" >> beam.Map(logger.debug)
        )


if __name__ == "__main__":
    run_pipeline()
