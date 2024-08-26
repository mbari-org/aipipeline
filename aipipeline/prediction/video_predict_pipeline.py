# aipipeline, Apache-2.0 license
# Filename: aipipeline/prediction/video-predict-pipeline.py
# Description: Batch process videos with inference
from datetime import datetime

import dotenv
from aidata.plugins.loaders.tator.common import find_box_type, init_api_project, get_version_id
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.io import ReadFromText
import requests
import json
import cv2
import tempfile
from pathlib import Path
import redis
import logging
import os

from config_setup import setup_config

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
now = datetime.now()
log_filename = f"video-predict-pipeline_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Secrets
dotenv.load_dotenv()
REDIS_PASSWD = os.getenv("REDIS_PASSWD")
TATOR_TOKEN = os.getenv("TATOR_TOKEN")

# Global variables
idv = 1  # video index
idl = 1  # localization index
redis_queue = None


class GetVideoMetadataFn(beam.DoFn):
    def process(self, video_name):
        query = f"http://m3.shore.mbari.org/vam/v1/media/videoreference/filename/{video_name}"
        logger.info(f"query: {query}")
        response = requests.get(query)
        logger.info(f"response: {response}")
        data = json.loads(response.text)[0]
        metadata = {
            "uri": data["uri"],
            "video_reference_uuid": data["video_reference_uuid"],
            "start_timestamp": data["start_timestamp"],
            "codec": data["video_codec"],
            "mime": data["container"],
            "resolution": (data["width"], data["height"]),
            "size": data["size_bytes"],
            "num_frames": int(data["frame_rate"] * data["duration_millis"] / 1000),
            "frame_rate": data["frame_rate"],
        }
        return [metadata]


class RunInferenceFn(beam.DoFn):
    def __init__(self, stride, endpoint_url, class_name, version_id):
        self.stride = stride
        self.endpoint_url = endpoint_url
        self.class_name = class_name
        self.version_id = version_id

    def process(self, video_path):
        global idl, redis_queue

        queued_video = False
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval_ms = int(1000 * self.stride)
        current_time_ms = 0
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        while cap.isOpened():
            frame_num = int(current_time_ms / 1000 * fps)
            if frame_num >= total_frames:
                break

            cap.set(cv2.CAP_PROP_POS_MSEC, current_time_ms)
            ret, frame = cap.read()

            if not ret:
                logger.error(f"Error reading frame at {current_time_ms / 1000} seconds")
                break

            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                cv2.imwrite(temp_file.name, frame)
                files = {"file": open(temp_file.name, "rb")}
                logger.info(f"Processing frame in {video_path} at {current_time_ms / 1000} seconds")
                response = requests.post(self.endpoint_url, files=files)

                if response.status_code == 200:
                    frame_num = int(current_time_ms / 1000 * fps)
                    logger.info(f"Frame in {video_path} at {current_time_ms / 1000} seconds processed successfully")
                    data = json.loads(response.text)
                    if len(data) > 0:
                        logger.info(data)
                        for loc in data:
                            if loc["class_name"] == self.class_name:
                                if not queued_video:
                                    queued_video = True
                                    video_path = Path(video_path)
                                    md = GetVideoMetadataFn().process(video_path.name)[0]
                                    if md is None:
                                        logger.error(f"Failed to get video metadata for {video_path}")
                                        return
                                    video_ref_uuid = md["video_reference_uuid"]
                                    iso_start = md["start_timestamp"]
                                    video_url = md["uri"]
                                    redis_queue.hset(
                                        f"video_refs_start:{video_ref_uuid}",
                                        "start_timestamp",
                                        iso_start,
                                    )
                                    redis_queue.hset(
                                        f"video_refs_load:{video_ref_uuid}",
                                        "video_uri",
                                        video_url,
                                    )

                                new_loc = {
                                    "x1": loc["x"],
                                    "y1": loc["y"],
                                    "x2": loc["x"] + loc["width"],
                                    "y2": loc["y"] + loc["height"],
                                    "width": frame_width,
                                    "height": frame_height,
                                    "frame": frame_num,
                                    "version_id": self.version_id,
                                    "score": loc["confidence"],
                                    "cluster": -1,
                                    "label": self.class_name,
                                }
                                redis_queue.hset(f"locs:{video_ref_uuid}", str(idl), json.dumps(new_loc))
                                idl += 1
                                logger.info(f"Found total possible {idl} localizations")
                else:
                    logger.error(f"Error processing frame at {current_time_ms / 1000} seconds: {response.text}")

            current_time_ms += frame_interval_ms

        cap.release()


def run_pipeline(args=None):
    args, beam_args = parse_args(args)
    config_dir, config_dict =  setup_config(args.config)
    tator_host = config_dict["tator"]["host"]
    project = config_dict["tator"]["project"]
    version = config_dict["data"]["version"]
    redis_host = config_dict["redis"]["host"]
    redis_port = config_dict["redis"]["port"]

    # Initialize the Tator API
    api, tator_project = init_api_project(tator_host, TATOR_TOKEN, project)
    box_type = find_box_type(api, tator_project.id, "Box")
    version_id = get_version_id(api, tator_project, version)
    assert box_type is not None, f"No box type found in project {project}"
    assert version_id is not None, f"No version found in project {project}"

    # Initialize the REDIS queue
    redis_queue = redis.Redis(host=redis_host, port=redis_port, password=REDIS_PASSWD)

    # Check if we can connect to the REDIS server
    if not redis_queue.ping():
        logger.error("Failed to connect to REDIS server")
        return

    if args.flush:
        logger.info("Flushing REDIS database")
        redis_queue.flushdb()

    # Run the pipeline
    pipeline_options = PipelineOptions()
    with beam.Pipeline(options=pipeline_options) as p:
        (
            p
            | "Read video file listing" >> ReadFromText(args.video_files)
            | "Run inference" >> beam.ParDo(RunInferenceFn(args.stride, args.endpoint_url, args.class_name, version_id))
        )


def parse_args(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Run model on video with REDIS queue based load.")
    parser.add_argument("--config", required=True, help="Path to the configuration YAML file.")
    parser.add_argument("--videos", help="Text file with video file names.", required=True, type=str)
    parser.add_argument("--stride", help="Stride for inference in seconds.", default=2, type=int)
    parser.add_argument("--class_name", help="Class name to target inference.", default="Ctenophora sp. A", type=str)
    parser.add_argument(
        "--endpoint_url",
        help="URL of the inference endpoint.",
        required=True,
        default="http://localhost:8000/predict",
        type=str,
    )
    parser.add_argument("--flush", help="Flush the REDIS database.", action="store_true")
    args, beam_args = parser.parse_known_args(argv)

    if not os.path.exists(args.videos):
        logger.error(f"Video file {args.videos} not found")
        raise FileNotFoundError(f"Video file {args.videos} not found")

    if not os.path.exists(args.config):
        logger.error(f"Config directory {args.config_dir} not found")
        raise FileNotFoundError(f"Config yaml {args.config} not found")

    return args, beam_args


if __name__ == "__main__":
    run_pipeline()
