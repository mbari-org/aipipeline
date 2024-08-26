# aipipeline, Apache-2.0 license
# Filename: projects/bio-901103/run_strided_inference.py
# Description: commands related to running inference on strided video with REDIS queue based load
import argparse
import json
import logging
import multiprocessing
import tempfile
from datetime import datetime
from pathlib import Path
from textwrap import dedent

import cv2
import redis
import requests
import sys

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)
# and log to file
now = datetime.now()
log_filename = f"vss-reset_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


# Global variables
idv = 1  # video index
idl = 1  # localization index


def get_video_metadata(video_name):
    """
    Get video metadata from the VAM rest API
    """
    try:
        query = f"http://m3.shore.mbari.org/vam/v1/media/videoreference/filename/{video_name}"
        logger.info(f"query: {query}")
        # Get the video reference uuid from the rest query JSON response
        response = requests.get(query)
        logger.info(f"response: {response}")
        data = json.loads(response.text)[0]
        logger.info(f"data: {data}")
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
        return metadata
    except Exception as e:
        print("Error:", e)
        return None


def run_inference(
    video_file: str,
    stride: int,
    endpoint_url: str,
    class_name: str,
    version_id: int = 0,
):
    """
    Run inference on a video file and queue the localizations in REDIS
    """
    global idl, idv, r
    try:
        video_path = Path(video_file)
        md = get_video_metadata(video_path.name)
        if md is None:
            logger.error(f"Failed to get video metadata for {video_path}")
            return
        # Queue the video first
        video_ref_uuid = md["video_reference_uuid"]
        iso_start = md["start_timestamp"]
        video_url = md["uri"]
        logger.info(f"video_ref_uuid: {video_ref_uuid}")
        r.hset(f"video_refs_start:{video_ref_uuid}", "start_timestamp", iso_start)
        r.hset(f"video_refs_load:{video_ref_uuid}", "video_uri", video_url)
    except Exception as e:
        logger.info(f"Error: {e}")
        # Remove the video reference from the queue
        r.delete(f"video_refs_start:{video_ref_uuid}")
        r.delete(f"video_refs_load:{video_ref_uuid}")
        return

    cap = cv2.VideoCapture(video_path.as_posix())
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval_ms = int(1000 * stride)
    current_time_ms = 0
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Loop through the video frames
    while cap.isOpened():
        # Don't exceed the total number of frames
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
            logger.info(f"Processing frame at {current_time_ms / 1000} seconds")
            response = requests.post(endpoint_url, files=files)

            if response.status_code == 200:
                frame_num = int(current_time_ms / 1000 * fps)
                logger.info(f"Frame at {current_time_ms / 1000} seconds processed successfully")
                logger.debug(response.text)
                logger.info(f"resp: {response}")
                data = json.loads(response.text)
                if len(data) > 0:
                    logger.info(data)
                    for loc in data:
                        if loc["class_name"] == class_name:
                            logger.info(f"queuing loc: {loc}")
                            new_loc = {
                                "x1": loc["x"],
                                "y1": loc["y"],
                                "x2": loc["x"] + loc["width"],
                                "y2": loc["y"] + loc["height"],
                                "width": frame_width,
                                "height": frame_height,
                                "frame": frame_num,
                                "version_id": version_id,
                                "score": loc["confidence"],
                                "cluster": -1,
                                "label": class_name,
                            }
                            r.hset(f"locs:{video_ref_uuid}", str(idl), json.dumps(new_loc))
                            idl += 1
                            logger.info(f"Found total possible {idl} ctenophore sp. A localizations")
            else:
                logger.error(f"Error processing frame at {current_time_ms / 1000} seconds: {response.text}")

        current_time_ms += frame_interval_ms

    cap.release()


def parse_args():
    parser = argparse.ArgumentParser(
        description=dedent("""\
    Run model on video with REDIS queue based load.

    Example: 
    python3 run_strided_inference_doris.py /path/to/video.mp4
    """),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--video", help="Video file or directory.", required=True, type=str)
    parser.add_argument("--stride", help="Stride for inference in seconds.", default=2, type=int)
    parser.add_argument(
        "--class_name",
        help="Class name to target inference.",
        default="Ctenophora sp. A",
        type=str,
    )
    parser.add_argument(
        "--endpoint_url",
        help="URL of the inference endpoint.",
        required=False,
        default="http://localhost:8000/predict",
        type=str,
    )
    parser.add_argument("--version_id", help="Version ID of the model.", default=0, type=int)
    parser.add_argument("--flush", help="Flush the REDIS database.", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    global r

    args = parse_args()

    # Connect to Redis
    r = redis.Redis(host="mantis.shore.mbari.org", port=6379, db=1)

    # TODO: add a check for the version_id

    # Clear the database
    if args.flush:
        r.flushdb()

    video_path = Path(args.video)

    if not video_path.exists():
        logger.error(f"Video does not exist: {video_path}")
        exit(1)

    if video_path.is_file():
        video_uri = video_path.as_posix()
        run_inference(
            video_path.as_posix(),
            args.stride,
            args.endpoint_url,
            args.class_name,
            args.version_id,
        )
    else:
        # Scale to number of CPUs
        video_files = list(video_path.glob("**/*.mp4"))
        num_cpus = multiprocessing.cpu_count()
        pool = multiprocessing.Pool(processes=num_cpus)
        pool.starmap(
            run_inference,
            [
                (
                    v.as_posix(),
                    args.stride,
                    args.endpoint_url,
                    args.class_name,
                    args.version_id,
                )
                for v in video_files
            ],
        )
        pool.close()
        pool.join()
