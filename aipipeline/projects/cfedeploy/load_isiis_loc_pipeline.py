# aipipeline, Apache-2.0 license
# Filename: projects/cfedeploy/load_isiis_loc_pipeline.py
# Description: Load detections into Tator from sdcat clustering. Working with ISIIS frames extracted from videos.
# This load frame-based detections on video media
import argparse
import os
import re
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
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)

pattern1 = re.compile(
    r'^(CFE_ISIIS-\d{3}-\d{4}-\d{2}-\d{2} \d{2}-\d{2}-\d{2}\.\d{3})_(\d{4})\.jpg$'
)
pattern2 = re.compile(
    r'^(CFE_ISIIS-\d{3}-\d{4}-\d{2}-\d{2} \d{2}-\d{2}-\d{2}\.\d{3})_(\d{4})_(\d+\.\d+)m\.jpg$'
)

def frame_depth_video(row, stride) -> tuple:
    if 'image_path' in row:
        filename = Path(row['image_path']).name
    elif 'crop_path' in row:
        filename = Path(row['crop_path']).name
    else:
        return (None, None,None)

    match1 = pattern1.search(filename)
    match2 = pattern2.search(filename)
    if match1:
        video_name = f"{match1.group(1)}.mp4"
        second = float(match1.group(2))
        frame = int(second*stride+1)
        depth = None
        return (frame, depth, video_name)
    elif match2:
        video_name = f"{match2.group(1)}.mp4"
        second = float(match2.group(2))
        frame = int(second*stride+1)
        depth = match2.group(3)
        return (frame, depth, video_name)
    else:
        logger.error(f"No match found in filename {filename} with pattern {pattern1} or {pattern2}.")
        return (None, None,None)

def load(element, config_dict) -> str:
    # Data is in the format
    # <image base directory path to process>,<stride frame images were captured at>
    logger.info(f"Processing element {element}")
    all_detections, stride, label, version = element

    try:
        # Get needed database ids and attributes for loading from the project config
        api, project = init_api_project(config_dict["tator"]["host"], TATOR_TOKEN, config_dict["tator"]["project"])
        project_id = project.id
        if version is None:
            version = config_dict["tator"]["version"]
        logger.info(f"Loading to version {version} in project {config_dict['tator']['project']} id {project_id}")
        version_id = get_version_id(api, project, version)
        video_type = find_media_type(api, project_id, "Video")
        box_type = find_box_type(api, project_id)
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

        logger.info(f"Getting video files names from project {project_id}")
        media_map = get_media_ids(api, project, video_type.id)

        for csv_file in all_csv_files:
            df = pd.read_csv(csv_file)
            df['frame'] = None
            df['depth'] = None
            df['video_name'] = None

            df['frame'], df['depth'] ,df['video_name']= zip(*df.apply(lambda row: frame_depth_video(row, stride), axis=1))

            # Rename class_s to label_s if it exists - this matches the attribute name in the config.yaml
            df.rename(columns={"class_s": "label_s"}, inplace=True)

            # Get the first row to extract the image path
            if df.empty:
                logger.error(f"No data found in {csv_file}.")
                continue

            # Assign the labels to the localizations, batching by 500
            batch_size = min(500, len(df))
            num_loaded = 0
            logger.info("Creating localizations ...")
            for i in range(0, len(df), batch_size):
                batch_df = df.iloc[i : i + batch_size]

                specs = []
                for index, row in batch_df.iterrows():
                    # if row['area'] > 300 and row['class'] == "copepod" and row["score"] > 0.97:  # Filter out boxes < 300 pixels and low score copepods
                    attributes = format_attributes(row, box_attributes)
                    if "label_s" in attributes and label is not None:
                        attributes["label_s"] = label
                    if row.depth is not None:
                        attributes["depth"] = row.depth
                    if row.frame is not None and row.video_name is not None:
                        # Clamp all boxes to be within the normalized range of 0 to 1
                        row["x"] = max(0, min(1, row["x"]))
                        row["y"] = max(0, min(1, row["y"]))
                        row["xx"] = max(0, min(1, row["xx"]))
                        row["xy"] = max(0, min(1, row["xy"]))
                        specs.append(
                            gen_spec(
                                elemental_id=row["elemental_id"],
                                box=[row["x"], row["y"], row["xx"], row["xy"]],
                                width=row["image_width"],
                                height=row["image_height"],
                                version_id=version_id,
                                label=label if label is not None else row["class"],
                                attributes=attributes,
                                frame_number=row.frame,
                                type_id=box_type.id,
                                media_id=media_map[row.video_name],
                                project_id=project_id,
                                normalize=False
                            )
                        )
                        logger.info(specs)
                        num_loaded += 1
                box_ids = load_bulk_boxes(project_id, api, specs)
                logger.info(f"Loaded {len(box_ids)} boxes of {len(df)} into Tator")

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
    parser.add_argument("--stride", help="Frame stride the image index in the filenames represent", default=14, type=int)
    parser.add_argument('--label', help="Override label to use for the boxes", type=str)
    parser.add_argument('--version', help="Version to load the data into", type=str, default="Baseline")
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
            | "Data" >> beam.Create([(args.data, args.stride, args.label, args.version)])
            | "Load csv" >> beam.Map(load, config_dict=config_dict)
            | "Log results" >> beam.Map(logger.debug)
        )


if __name__ == "__main__":
    run_pipeline()
