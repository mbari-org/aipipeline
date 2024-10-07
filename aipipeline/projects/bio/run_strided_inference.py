# aipipeline, Apache-2.0 license
# Filename: projects/bio/run_strided_inference.py
# Description: commands related to running inference on strided video with REDIS queue based load
import argparse
import dotenv
import io
import json
import logging
import multiprocessing
import os
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from textwrap import dedent

import cv2
import pandas as pd
import redis
import requests

from aipipeline.config_setup import setup_config
from aipipeline.db_utils import init_api_project, get_version_id
from aipipeline.prediction.library import run_vss
from aipipeline.docker.utils import run_docker

CONFIG_YAML = Path(__file__).resolve().parent / "config" / "config.yml"

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)
# and log to file
now = datetime.now()
log_filename = f"run_strided_inference_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Global variables
idv = 1  # video index
idl = 1  # localization index

# Secrets
dotenv.load_dotenv()
REDIS_PASSWD = os.getenv("REDIS_PASSWD")
TATOR_TOKEN = os.getenv("TATOR_TOKEN")


def get_ancillary_data(platform: str, iso_datetime: datetime) -> dict:
    try:
        container = run_docker(
            config_dict["docker"]["expd"],
            f"expd-{platform}-{iso_datetime:%Y%m%dT%H%M%S}",
            [platform, iso_datetime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')],
            auto_remove=False,
        )
        if container:
            container.wait()
            # get the output string and convert to a dictionary
            output = container.logs().decode("utf-8")
            data = json.loads(output)
            container.remove()
            return data
        else:
            container.remove()
            logger.error(f"Failed to capture expd data....")
    except Exception as e:
        logger.error(f"Failed to capture expd data....{e}")


def get_video_metadata(video_name):
    """
    Get video metadata from the VAM rest API
    """
    try:
        # Check if the metadata is cached
        cache_file = f"/tmp/{video_name}.json"
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                return json.load(f)
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
            "mime": data["container"],
            "resolution": (data["width"], data["height"]),
            "size": data["size_bytes"],
            "num_frames": int(data["frame_rate"] * data["duration_millis"] / 1000),
            "frame_rate": data["frame_rate"],
            "dive": data["video_sequence_name"],
        }
        # Cache the metadata to /tmp
        with open(cache_file, "w") as f:
            json.dump(metadata, f)
        return metadata
    except Exception as e:
        print("Error:", e)
        return None


def read_image(file_path: str) -> tuple[bytes, str]:
    with open(file_path, 'rb') as file:
        img = io.BytesIO(file.read()).getvalue()
        return img, file_path


def resolve_video_path(video_path: Path) -> Path:
    # Resolve the video URI to a local path
    md = get_video_metadata(video_path.name)
    if md is None:
        logger.error(f"Failed to get video metadata for {video_path}")
        return None

    resolved_path = Path(f'/mnt/M3/mezzanine' + md['uri'].split('/mezzanine')[-1])
    return resolved_path


def run_inference(
        video_file: str,
        stride: int,
        endpoint_url: str,
        config_dict: dict,
        class_name: str,
        version_id: int = 0,
):
    """
    Run inference on a video file and queue the localizations in REDIS
    """
    global idl, idv, redis_queue
    queued_video = False
    video_ref_uuid = None
    try:
        video_path = Path(video_file)
        md = get_video_metadata(video_path.name)
        if md is None:
            logger.error(f"Failed to get video metadata for {video_path}")
            return
    except Exception as e:
        logger.info(f"Error: {e}")
        return

    dive = md["dive"]
    cap = cv2.VideoCapture(video_path.as_posix())
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval_ms = int(1000 * stride)
    frames_to_skip = int(fps * stride)
    current_time_ms = 0
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Loop through the video frames
    frame_count = 0
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
        while cap.isOpened():
            # Don't exceed the total number of frames
            if frame_count >= total_frames:
                break

            ret, frame = cap.read()

            if not ret:
                logger.error(f"{video_path.name}: error reading frame {frame_count}")
                break

            if frame_count % frames_to_skip == 0:

                current_time_ms += frame_interval_ms

                cv2.imwrite(temp_file.name, frame)
                files = {"file": open(temp_file.name, "rb")}
                logger.info(f"{video_path.name}: processing frame at {current_time_ms / 1000} seconds")

                for n_try in range(5):
                    try:
                        logger.info(f"Sending frame to {endpoint_url}")
                        response = requests.post(endpoint_url, files=files)
                        if response.status_code == 200:
                            break
                    except Exception as e:
                        logger.error(f"{video_path.name}: error processing frame at {current_time_ms / 1000} seconds: {e} in {video_path}")
                        # delay to avoid overloading the server
                        time.sleep(5)
                        continue

                if response.status_code == 200:
                    logger.info(f"{video_path.name}: frame at {current_time_ms / 1000} seconds processed successfully")
                    logger.debug(response.text)
                    logger.info(f"resp: {response}")
                    data = json.loads(response.text)
                    if len(data) > 0:
                        logger.info(data)

                        # Remove duplicates
                        data = [dict(t) for t in {tuple(d.items()) for d in data}]

                        for loc in data:
                            if loc["class_name"] == class_name:
                                # For low confidence detections, run through the vss model
                                if loc["confidence"] < 0.6:
                                    logger.info(
                                        f"{video_path.name}: running VSS model on low confidence {class_name} detection {loc['confidence']}")
                                    images = [read_image(temp_file.name)]
                                    file_paths, best_predictions, best_scores = run_vss(images, config_dict, top_k=3)
                                    if len(best_predictions) == 0:
                                        logger.info(f"{video_path.name}: no predictions from VSS model. Skipping this detection.")
                                        continue
                                    if best_predictions[0] != class_name:
                                        logger.info(
                                            f"{video_path.name}: VSS model prediction {best_predictions[0]} does not match {class_name}. Skipping this detection.")
                                        continue
                                    logger.info(f"===>{video_path.name}: VSS model prediction {best_predictions[0]} matches {class_name}<====")
                                else:
                                    logger.info(f"====>{video_path.name}: high confidence {class_name} detection {loc['confidence']}<====")

                                if not queued_video:
                                    queued_video = True
                                    # Only queue the video if we have a valid localization to queue
                                    # Video transcoding to gif for thumbnail generation is expensive
                                    try:
                                        logger.info(f"Queuing video {video_path.name}")
                                        video_path = Path(video_file)
                                        md = get_video_metadata(video_path.name)
                                        if md is None:
                                            logger.error(f"{video_path.name} failed to get video metadata")
                                            return
                                        iso_start = md["start_timestamp"]
                                        # Convert the start time to a datetime object
                                        iso_start_datetime = datetime.strptime(iso_start, "%Y-%m-%dT%H:%M:%SZ")
                                        platform = dive.split(' ')[:-1]  # remove the last element which is the dive number
                                        platform = ''.join(platform)
                                        # Queue the video first
                                        video_ref_uuid = md["video_reference_uuid"]
                                        iso_start = md["start_timestamp"]
                                        video_url = md["uri"]
                                        logger.info(f"video_ref_uuid: {video_ref_uuid}")
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
                                    except Exception as e:
                                        logger.info(f"Error: {e}")
                                        # Remove the video reference from the queue
                                        redis_queue.delete(f"video_refs_start:{video_ref_uuid}")
                                        redis_queue.delete(f"video_refs_load:{video_ref_uuid}")
                                        return

                                loc_datetime = iso_start_datetime + timedelta(milliseconds=current_time_ms)
                                loc_datetime_str = loc_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
                                logger.info(f"queuing loc: {loc} for {class_name} {platform} {loc_datetime}")
                                ancillary_data = get_ancillary_data(platform, loc_datetime)
                                if ancillary_data is None or "depthMeters" not in ancillary_data:
                                    logger.error(f"Failed to get ancillary data for {dive}")
                                    continue

                                if ancillary_data["depthMeters"] < 300:
                                    logger.info(f"Depth is less than 300 meters, skipping")
                                    continue

                                new_loc = {
                                    "x1": loc["x"],
                                    "y1": loc["y"],
                                    "x2": loc["x"] + loc["width"],
                                    "y2": loc["y"] + loc["height"],
                                    "width": frame_width,
                                    "height": frame_height,
                                    "frame": frame_count,
                                    "version_id": version_id,
                                    "score": loc["confidence"],
                                    "cluster": -1,
                                    "label": loc["class_name"],
                                    "dive": dive,
                                    "depth": ancillary_data["depthMeters"],
                                    "iso_datetime": loc_datetime_str,
                                    "latitude": ancillary_data["latitude"],
                                    "longitude": ancillary_data["longitude"],
                                    "temperature": ancillary_data["temperature"],
                                    "oxygen": ancillary_data["oxygen"],
                                }
                                redis_queue.hset(f"locs:{video_ref_uuid}", str(idl), json.dumps(new_loc))
                                logger.info(f"{video_path.name} found total possible {idl} localizations of {class_name}")
                                idl += 1
                else:
                    logger.error(f"Error processing frame at {current_time_ms / 1000} seconds: {response.text}")

            frame_count += 1

    logger.info(f"Finished processing video {video_path}")
    cap.release()


def process_videos(video_files, stride, endpoint_url, config_dict, class_name, version_id):
    num_cpus = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(processes=num_cpus)
    pool.starmap(
        run_inference,
        [(v, stride, endpoint_url, config_dict, class_name, version_id) for v in video_files],
    )
    pool.close()
    pool.join()


def parse_args():
    parser = argparse.ArgumentParser(
        description=dedent("""\
        Run model on video with REDIS queue based load.

        Example: 
        python3 run_inference_video.py /path/to/video.mp4
        """),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--config", required=True, help=f"Configuration files. For example: {CONFIG_YAML}")
    parser.add_argument("--video", help="Video file or directory.", required=False, type=str)
    parser.add_argument(
        "--tsv",
        help="TSV file with video paths per Haddock output",
        required=False,
        type=str,
    )
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
        required=True,
        default="http://localhost:8000/predict",
        type=str,
    )
    parser.add_argument("--flush", help="Flush the REDIS database.", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":

    args = parse_args()
    config_files, config_dict = setup_config(args.config)

    if TATOR_TOKEN is None:
        logger.error("TATOR_TOKEN environment variable not set")
        exit(1)

    if REDIS_PASSWD is None:
        logger.error("REDIS_PASSWD environment variable not set")
        exit(1)

    # Get the version id from the database
    project = config_dict["tator"]["project"]
    host = config_dict["tator"]["host"]
    version = config_dict["data"]["version"]
    api, project = init_api_project(host=host, token=TATOR_TOKEN, project=project)
    version_id = get_version_id(api, project, version)
    if version_id is None:
        logger.error(f"Failed to get version id for {version}")
        exit(1)

    # Need to have a video or TSV file with video paths to process
    if not args.video and not args.tsv:
        logger.error("Must provide either a video or TSV file with video paths")
        exit(1)

    # Connect to Redis
    redis_host = config_dict["redis"]["host"]
    redis_port = config_dict["redis"]["port"]
    redis_queue = redis.Redis(host=redis_host, port=redis_port, password=os.getenv("REDIS_PASSWD"))

    # Clear the database
    if args.flush:
        # Delete all relevant keys
        keys_start = redis_queue.keys("video_refs_start:*")
        keys_load = redis_queue.keys("video_refs_load:*")
        keys_locs = redis_queue.keys("locs:*")
        keys_ids = redis_queue.keys("tator_ids_v:*")
        keys = keys_start + keys_load + keys_locs + keys_ids
        for key in keys:
            redis_queue.delete(key)
        logger.info("Flushed REDIS database")

    if args.video:
        video_path = Path(args.video)

        if video_path is None:
            logger.error(f"Invalid video path: {args.video}")
            exit(1)

        if video_path.is_file() and not video_path.exists():
            logger.error(f"Video does not exist: {video_path}")
            exit(1)

        if video_path.is_file():
            video_uri = video_path.as_posix()
            run_inference(
                video_path.as_posix(),
                args.stride,
                args.endpoint_url,
                config_dict,
                args.class_name,
                version_id,
            )
        elif video_path.is_dir():
            # Fanout to number of CPUs
            video_files = list(video_path.rglob("*.mp4"))
            video_files = [v for v in video_files]
            process_videos(
                video_files,
                args.stride,
                args.endpoint_url,
                config_dict,
                args.class_name,
                version_id,
            )
        else:
            logger.error(f"Invalid video path: {video_path}")
            exit(1)
    elif args.tsv:
        df = pd.read_csv(args.tsv, sep="\t")
        # The 5th column is the video path
        video_files = df.iloc[:, 4].tolist()
        # Make sure the files are unique -there may be duplicates, but we don't want to process them multiple times
        video_files = list(set(video_files))
        # Convert to Path objects and resolve the video paths; remove any None values which mean the video path is invalid
        video_files = [resolve_video_path(Path(v)) for v in video_files]
        video_files = [v for v in video_files if v is not None]
        # Fanout to number of CPUs
        process_videos(
            video_files,
            args.stride,
            args.endpoint_url,
            config_dict,
            args.class_name,
            version_id,
        )

    logger.info("Finished processing videos")