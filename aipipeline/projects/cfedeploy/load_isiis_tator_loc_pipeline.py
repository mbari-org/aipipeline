# aipipeline, Apache-2.0 license
# Filename: projects/cfedeploy/load_isiis_tator_loc_pipeline.py
# Description: Load detections into Tator from Tator downloads. Working with ISIIS frames extracted from videos.
# This load frame-based detections on video media
import argparse
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from textwrap import dedent

import apache_beam as beam
import dotenv
import pandas as pd
from apache_beam.options.pipeline_options import PipelineOptions
import logging

from aipipeline.config_setup import setup_config
from mbari_aidata.plugins.loaders.tator.attribute_utils import format_attributes
from mbari_aidata.plugins.loaders.tator.common import init_api_project, get_version_id, find_box_type, find_media_type
from mbari_aidata.plugins.loaders.tator.localization import gen_spec, load_bulk_boxes
from mbari_aidata.plugins.loaders.tator.media import get_media_ids

# Secrets
dotenv.load_dotenv()
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
TATOR_TOKEN = os.getenv("TATOR_TOKEN")

# Logging
logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
now = datetime.now()
log_filename = f"load-isiis-loc-pipeline{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

pattern = re.compile(r"CFE_(.*?)-(\d+)-(\d{4}-\d{2}-\d{2} \d{2}-\d{2}-\d{2}\.\d{3})\.mp4")

def frame_depth_video(row) -> tuple:
    filename = row["(media) $name"]
    frame = int(row['$frame'])
    match = pattern.search(filename)
    if match:
        depth = None
        return frame, depth, filename
    else:
        logger.error(f"No match found in filename {filename} with pattern {pattern}")
        return None, None,None

def load(element, config_dict) -> str:
    # Data is in the format
    # <image base directory path to process>,<stride frame images were captured at>
    logger.info(f"Processing element {element}")
    all_detections = element

    try:
        # Get needed database ids and attributes for loading from the project config
        api, project = init_api_project(config_dict["tator"]["host"], TATOR_TOKEN, config_dict["tator"]["project"])
        logger.info(f"Loading to project {config_dict['tator']['project']}")
        video_type = find_media_type(api, project.id, "Video")
        box_type = find_box_type(api, project.id)
        box_attributes = config_dict["tator"]["box"]["attributes"]

        logger.info(f"Loading cluster detections from {all_detections}")
        all_detections_path = Path(all_detections)
        if not all_detections_path.exists():
            logger.error(f"File {all_detections} does not exist.")
            return f"File {all_detections} does not exist."

        if not all_detections_path.is_file():
            all_csv_files = list(all_detections_path.glob("*.csv"))
            if len(all_csv_files) == 0:
                logger.error(f"No CSV files found in {all_detections}.")
                return f"No CSV files found in {all_detections}."
        else:
            all_csv_files = [all_detections_path]

        logger.info(f"Getting video files names from project {project.id}")
        kwargs =  {  "section" :  288 }
        media_map = get_media_ids(api, project, video_type.id, **kwargs)

        elemental_ids = []
        for csv_file in all_csv_files:
            try:
                df = pd.read_csv(csv_file)
                elemental_ids = elemental_ids + df['$elemental_id'].to_list()

                df['frame'] = None
                df['depth'] = None
                df['video_name'] = None
                df['frame'], df['depth'] ,df['video_name']= zip(*df.apply(lambda row: frame_depth_video(row), axis=1))

                # Rename the columns "Label" to "label"
                df.rename(columns={"Label": "label"}, inplace=True)

                # Assign the labels to the localizations, batching by 500
                batch_size = min(500, len(df))
                num_loaded = 0
                logger.info("Creating localizations ...")
                for i in range(0, len(df), batch_size):
                    batch_df = df.iloc[i : i + batch_size]

                    specs = []
                    for index, row in batch_df.iterrows():

                        attributes = format_attributes(row, box_attributes)

                        if row.frame is not None and row.video_name is not None:
                            # Clamp all boxes to be within the normalized range of 0 to 1
                            row["x"] = max(0, min(1, row["$x"]))
                            row["y"] = max(0, min(1, row["$y"]))
                            row["xx"] = row["x"] + row["$width"]
                            row["xy"] = row["y"] + row["$height"]
                            row["xx"] = max(0, min(1, row["xx"]))
                            row["xy"] = max(0, min(1, row["xy"]))
                            spec = gen_spec(
                                    box=[row["x"], row["y"], row["xx"], row["xy"]],
                                    width=row["(media) $width"],
                                    height=row["(media) $height"],
                                    version_id=row["$version_id"],
                                    label=row["label"],
                                    attributes=attributes,
                                    frame_number=row["$frame"],
                                    type_id=box_type.id,
                                    media_id=media_map[row["(media) $name"]],
                                    project_id=project.id,
                                    normalize=False
                                )
                            spec["elemental_id"] = row["$elemental_id"]
                            specs.append(spec)
                            logger.info(specs)
                            num_loaded += 1
                    box_ids = load_bulk_boxes(project.id, api, specs)
                    logger.info(f"Loaded {len(box_ids)} boxes of {len(df)} into Tator")
            except Exception as e:
                logger.error(f"Error processing {all_detections} in files {csv_file}: {e}")
                continue

        uuids = set(elemental_ids)
        len_data = len(elemental_ids)
        print(f"Found {len(uuids)} unique images with {len_data} total detections in {all_detections}")
        return f"{all_detections} loaded."
    except Exception as e:
        logger.error(f"Error loading {all_detections}: {e}")
        return f"Error loading {all_detections}: {e}"


def parse_args(argv, logger):
    parser = argparse.ArgumentParser(
        description=dedent("""\
        Load detections into Tator from ISIIS frames extracted from videos
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

# Run the pipeline. This could be modified to read multiple files or directories.
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
