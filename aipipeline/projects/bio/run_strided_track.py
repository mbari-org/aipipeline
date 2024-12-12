# aipipeline, Apache-2.0 license
# Filename: projects/bio/run_strided_track.py
# Description: commands related to running tracking on strided video with REDIS queue based load
import argparse
import ast
import uuid
import random

import dotenv
import json
import logging
import multiprocessing
import os
from datetime import datetime, timedelta
from pathlib import Path
from textwrap import dedent

import cv2
import pandas as pd
import redis

from aipipeline.config_setup import setup_config
from aipipeline.db_utils import init_api_project, get_version_id
from biotrack.batch_utils import media_to_stack
from aipipeline.prediction.utils import crop_square_image

from biotrack.tracker import BioTracker
from aipipeline.projects.bio.model.inference import FastAPIYV5, YV10, YV5
from aipipeline.projects.bio.bioutils import get_ancillary_data, get_video_metadata, resolve_video_path, video_to_frame, \
    seconds_to_timestamp, read_image

CONFIG_YAML = Path(__file__).resolve().parent / "config" / "config.yml"

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)
# and log to file
now = datetime.now()
log_filename = f"run_strided_track_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Global variables
idv = 1  # video index
idl = 1  # localization index

# Secrets
dotenv.load_dotenv()
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
TATOR_TOKEN = os.getenv("TATOR_TOKEN")

class_colors = {}

def get_random_color():
    bright_palette = [
        "#FF5733", "#33FF57", "#3357FF", "#FF33A1", "#F1C40F",
        "#8E44AD", "#16A085", "#E67E22", "#2ECC71", "#3498DB",
        "#9B59B6", "#F39C12", "#D35400", "#27AE60", "#2980B9",
        "#1ABC9C", "#E74C3C", "#EC7063", "#AF7AC5", "#F5B041",
        "#5DADE2", "#58D68D", "#EB984E", "#F4D03F", "#D5DBDB",
        "#E59866", "#52BE80", "#5499C7", "#A569BD", "#FAD7A0",
        "#BB8FCE", "#73C6B6", "#AED6F1", "#A9DFBF", "#F5CBA7",
        "#FADBD8", "#ABEBC6", "#D7BDE2", "#D2B4DE", "#A3E4D7",
        "#FDEBD0", "#E6B0AA", "#7FB3D5", "#48C9B0", "#E8DAEF",
        "#F7DC6F", "#E74C3C", "#F1948A", "#85C1E9", "#F9E79F"
    ]
    color_hex = random.choice(bright_palette)
    color = tuple(int(color_hex[i:i + 2], 16) for i in (1, 3, 5))
    return color

def display_tracks(frames, tracks, frame_num, out_video, imshow=False):
    for i, frame in enumerate(frames):
        j = frame_num + i
        for track in tracks:
            pt, label, box, score = track.get(j, rescale=True)
            # Offset to the right by 10 pixels for better visibility on small objects
            center = None
            if box is not None:
                center = (int(box[0] + 20), int(box[1]))
            if pt is not None:
                center = (int(pt[0] + 20), int(pt[1]))
            # if the track is not visible in this frame, skip it
            if center is None:
                continue
            thickness = 1
            font = cv2.FONT_HERSHEY_SIMPLEX
            fontScale = 1
            if label not in class_colors:
                class_colors[label] = get_random_color()
            color = class_colors[label]
            # Draw the track track_id with the label, e.g. 1:marine organism:0.12
            frame = cv2.putText(frame, f"{track.id}:{label}:{float(score):.2f}", center, font, fontScale, color, thickness,
                            cv2.LINE_AA)
            # Drop the box - this is visually distracting to me
            # thickness = 1
            # color = class_colors[label]
            # frame = cv2.rectangle(frame, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), color, thickness)

        if frame is not None:
            if imshow:
                cv2.imshow("Frame", frame)
                cv2.waitKey(500)
            out_video.write(frame)


def clean(output_path: Path):
    """
    Clean up the output directory
    """
    for output_path in output_path.rglob("*.jpg"):
        output_path.unlink()
    for output_path in output_path.rglob("*.json"):
        output_path.unlink()

def run_inference_track(video_file: str, version_id: int = 0, **kwargs):
    """
    Run inference and tracking on a video file and queue the localizations in REDIS
    """
    global idl, idv, redis_queue
    queued_video = False
    dive = Path(video_file).parent.name
    video_path = Path(video_file)
    stride_fps = kwargs.get("stride_fps", 3)
    endpoint_url = kwargs.get("endpoint_url", None)
    det_model = kwargs.get("det_model", None)
    vits_model = kwargs.get("vits_model", None)
    allowed_class_names = kwargs.get("allowed_class_names", None)
    remapped_class_names = kwargs.get("remapped_class_names", None)
    skip_load = kwargs.get("skip_load", False)
    min_depth = kwargs.get("min_depth", 200)
    max_secs = kwargs.get("max_seconds", -1)
    max_frames_tracked = kwargs.get("max_frames_tracked", 300)
    min_frames = kwargs.get("min_frames", 5)
    min_score_det = kwargs.get("min_score_det", 0.1)
    min_score_track = kwargs.get("min_score_track", 0.1)
    gpu_id = kwargs.get("gpu_id", 0)
    imshow = kwargs.get("imshow", False)
    ffmpeg_path = kwargs.get("ffmpeg_path", "/usr/bin/ffmpeg")
    if not skip_load:
        try:
            md = get_video_metadata(video_path.name)
            dive = md["dive"]
            if md is None:
                logger.error(f"Failed to get video metadata for {video_path}")
                return
        except Exception as e:
            logger.info(f"Error: {e}")
            return

    # Initialize the YOLOv5 detector instance if we have an endpoint
    yv5 = None
    yv10 = None
    if endpoint_url:
        yv5 = FastAPIYV5(endpoint_url)
    else:
        # yv10 = YV10(det_model)
        yv10 = YV5(det_model, device_num=gpu_id)

    # Video summarization and output
    results = {}
    cap = cv2.VideoCapture(video_path.as_posix())
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration_secs = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS))
    tracker = BioTracker(frame_width, frame_height, device_id=gpu_id, model_name=vits_model)
    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    output_path = Path("/tmp") / video_path.stem
    frame_path = output_path / "frames"
    crop_path = output_path / "crops"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    dive_path = Path("/tmp") / dive
    out_video_path = dive_path / f"{video_path.stem}_tracked_{Path(vits_model).name}.mp4"
    frame_path.mkdir(parents=True, exist_ok=True)
    crop_path.mkdir(parents=True, exist_ok=True)
    dive_path.mkdir(parents=True, exist_ok=True)
    clean(output_path)
    clean(dive_path)
    out_video = cv2.VideoWriter(out_video_path.as_posix(), fourcc, 10, (frame_width, frame_height))

    if not skip_load:
        # Check the beginning and ending of the video depths, and skip if less than 200 meters
        iso_start = md["start_timestamp"]
        iso_start_datetime = datetime.strptime(iso_start, "%Y-%m-%dT%H:%M:%SZ")
        ancillary_data_start = get_ancillary_data(md['dive'], config_dict, iso_start_datetime)
        if ancillary_data_start is None or "depthMeters" not in ancillary_data_start:
            logger.error(f"Failed to get ancillary data for {md['dive']} {iso_start_datetime}")
            return
        if ancillary_data_start["depthMeters"] < min_depth:
            logger.info(f"{video_path.name} depth {ancillary_data_start['depthMeters']} "
                        f"is less than {min_depth} meters, skipping")
            return

    # Loop through the video frames, processing every `stride_fps` seconds
    # The cotracker is not designed to run on every frame - it runs every 4 frames
    # so make sure the window_len is a multiple of 4
    total_frames = int(duration_secs * frame_rate)
    frame_stride = int(frame_rate / stride_fps)
    window_len = min(8*frame_stride, 60)
    all_loc = []
    end = False
    for frame_num in range(0, total_frames, frame_stride):
        frame_idx = frame_num // frame_stride
        current_time_secs = float(frame_num / frame_rate)
        logger.info(f"{video_path.name}: processing frame at {current_time_secs} seconds")

        # Run the tracking every window_len frames or the last frame
        if (frame_idx % window_len == 0 and frame_idx > 0
                or frame_idx == total_frames - 1
                or max_secs > 0 and current_time_secs > max_secs):
            if frame_idx == total_frames - 1 or max_secs > 0 and current_time_secs > max_secs:
                end = True
            logger.info(f"Running tracker at {current_time_secs} seconds")
            frame_stack, num_frames = media_to_stack(frame_path, resize=(640, 360))
            if num_frames == 0:
                logger.error(f"Error reading frames from {frame_path}")
                return

            frame_stack_full, _ = media_to_stack(frame_path)
            detections = []
            loc_df = pd.DataFrame(all_loc)
            # Get all the detections in the window
            start_frame = frame_idx - window_len
            end_frame = min(start_frame+frame_idx, start_frame+num_frames)
            if len(loc_df) > 0:
                for i in range(start_frame, end_frame + 1):
                    in_frame = loc_df[loc_df["frame"] == i]
                    for _, loc in in_frame.iterrows():
                        t_loc = loc.to_dict()
                        # Convert the x, y to the image coordinates
                        t_loc["x"] = loc["x"] * loc["image_width"]
                        t_loc["y"] = loc["y"] * loc["image_height"]
                        t_loc["xx"] = loc["xx"] * loc["image_width"]
                        t_loc["xy"] = loc["xy"] * loc["image_height"]
                        t_loc["frame"] = i
                        t_loc["score"] = loc["confidence"]
                        detections.append(t_loc)

            # Run the tracker and clean up the localizations
            tracks = tracker.update_batch((start_frame, end_frame),
                                          frame_stack,
                                          detections=detections,
                                          max_empty_frames=4,
                                          max_frames=max_frames_tracked,
                                          max_cost=0.5)
            display_tracks(frame_stack_full, tracks, start_frame, out_video, imshow)
            clean(output_path)
            all_loc = []

            # Check if any tracks are closed and queue the localizations in REDISx
            closed_tracks = [t for t in tracks if t.is_closed()]

            # Force track closure at the end of the video
            if end:
                closed_tracks = tracks

            if closed_tracks and len(closed_tracks) > 0:
                for track in closed_tracks:
                    logger.info(f"Closed track {track.id} at frame {frame_idx}")
                    best_frame, best_pt, best_labels, best_box, best_scores = track.get_best(rescale=False)
                    if track.num_frames <= min_frames or best_scores[0] <= min_score_track:
                        logger.info(f"Track {track.id} is too short num frames {track.num_frames} or best score {best_scores[0]} is < {min_score_track}, skipping")
                        continue
                    best_time_secs = float(best_frame*frame_stride / frame_rate)
                    logger.info(f"Best track {track.id} is {best_pt},{best_box},{best_labels},{best_scores} in frame {best_frame}")
                    if best_labels[0] not in results:
                        results[best_labels[0]] = 1
                    else:
                        results[best_labels[0]] += 1

                    if not skip_load:
                        loc_datetime = iso_start_datetime + timedelta(seconds=best_time_secs)
                        loc_datetime_str = loc_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
                        ancillary_data = get_ancillary_data(md['dive'], config_dict, loc_datetime)

                        if ancillary_data is None or "depthMeters" not in ancillary_data:
                            logger.error(f"Failed to get ancillary data for {md['dive']} {iso_start_datetime}")
                            continue

                        new_loc = {
                            "x1": float(best_box[0]),
                            "y1": float(best_box[1]),
                            "x2": float(best_box[2]),
                            "y2": float(best_box[3]),
                            "width": int(frame_width),
                            "height": int(frame_height),
                            "frame": int(best_frame*frame_stride),
                            "version_id": int(version_id),
                            "score": float(best_scores[0]),
                            "score_s": float(best_scores[1]),
                            "cluster": "-1",
                            "label": best_labels[0],
                            "label_s": best_labels[1] if best_labels[1] else "marine organism", # TODO: make this lower case
                            "dive": md["dive"],
                            "depth": ancillary_data["depthMeters"],
                            "iso_datetime": loc_datetime_str,
                            "latitude": ancillary_data["latitude"],
                            "longitude": ancillary_data["longitude"],
                            "temperature": ancillary_data["temperature"],
                            "oxygen": ancillary_data["oxygen"],
                        }
                        logger.info(f"queuing loc: {new_loc} {md['dive']} {loc_datetime}")
                        redis_queue.hset(f"locs:{md['video_reference_uuid']}", str(idl), json.dumps(new_loc))
                    logger.info(f"{video_path.name} found total possible {idl} localizations")
                    idl += 1
                tracker.purge_closed_tracks()  # Purge the closed tracks

        if not end:
            relative_timestamp = seconds_to_timestamp(current_time_secs)
            output_frame = frame_path / f"{frame_idx:06d}.jpg"
            video_to_frame(relative_timestamp, video_path, output_frame, ffmpeg_path)
            if yv5:
                data = yv5.predict_image( open(output_frame.as_posix(), "rb"))
                if data is None:
                    logger.error(f"Error processing frame at {current_time_secs} seconds")
                    continue

                logger.info(f"{video_path.name}: frame at {current_time_secs} seconds processed successfully")
                if len(data) == 0:
                    logger.info(f"{video_path.name}: No localizations in frame at {current_time_secs} seconds")
                    continue
            if yv10:
                data = yv10.predict_image(cv2.imread(output_frame.as_posix()))
                if data is None:
                    logger.error(f"Error processing frame at {current_time_secs} seconds")
                    continue

                logger.info(f"{video_path.name}: frame at {current_time_secs} seconds processed successfully")
                if len(data) == 0:
                    logger.info(f"{video_path.name}: No localizations in frame at {current_time_secs} seconds")
                    continue

        # Remove any detections in the corner 1% of the frame or not in the allowed class names or below the confidence threshold
        threshold = 0.01 # 1% threshold
        for loc in reversed(data):
            loc["image_path"] = output_frame.as_posix()
            x = loc["x"] / frame_width
            y = loc["y"] / frame_height
            xx = (loc["x"] + loc["width"]) / frame_width
            xy = (loc["y"] + loc["height"])  / frame_height
            if (
                    (0 <= x <= threshold or 1 - threshold <= x <= 1) or
                    (0 <= y <= threshold or 1 - threshold <= y <= 1) or
                    (0 <= xx <= threshold or 1 - threshold <= xx <= 1) or
                    (0 <= xy <= threshold or 1 - threshold <= xy <= 1) or
                    allowed_class_names and loc["class_name"] not in allowed_class_names or
                    loc["confidence"] < min_score_det
            ):
                data.remove(loc)
                continue

            # Crop the image to the bounding box
            loc["image_width"] = frame_width
            loc["image_height"] = frame_height
            loc["frame"] = frame_idx
            loc["x"] = x
            loc["y"] = y
            loc["xx"] = xx
            loc["xy"] = xy
            loc["crop_path"] = (crop_path / f"{uuid.uuid5(uuid.NAMESPACE_DNS, str(loc['x']) + str(loc['y']) + str(loc['width']) + str(loc['height']))}.jpg").as_posix()
            crop_square_image(pd.Series(loc), 224)

            # Remove the crop if it has a blurriness score of 2.0 or greater
            def detect_blur(image_path, threshold):
                image = cv2.imread(image_path)
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                _, binary_image = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
                laplacian = cv2.Laplacian(gray, cv2.CV_64F)
                _, max_val, _, _ = cv2.minMaxLoc(gray)
                laplacian_variance = laplacian.var()
                print(f"laplacian_variance: {laplacian_variance} for {image_path}")
                if laplacian_variance < threshold:
                    return True
                return False

            if detect_blur(loc["crop_path"], 2.0):
                data.remove(loc)
                os.remove(loc["crop_path"])
                continue

        if len(data) == 0:
            logger.info(f"{video_path.name}: No valid localizations in frame at {current_time_secs} seconds")
            continue

        for loc in data:
            all_loc.append(loc)

        # Only queue the video if we have a valid localization to queue
        # Video transcoding to gif for thumbnail generation is expensive
        if not skip_load and not queued_video and len(all_loc) > 0:
            queued_video = True
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
                # Queue the video first
                video_ref_uuid = md["video_reference_uuid"]
                iso_start = md["start_timestamp"]
                video_url = md["uri"]
                # http://mantis.shore.mbari.org/M3/mezzanine/Ventana/2022/09/4432/V4432_20220914T210637Z_h264.mp4
                # https://m3.shore.mbari.org/videos/M3/mezzanine/Ventana/2022/09/4432/V4432_20220914T210637Z_h264.mp4
                # Replace m3.shore.mbari.org/videos with mantis.shore.mbari.org/M3
                video_url = video_url.replace("https://m3.shore.mbari.org/videos", "http://mantis.shore.mbari.org")
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

        if end:
            logger.info(f"Reached max_secs: {max_secs}. Stopping processing.")
            break

    logger.info(f"Finished processing video {video_path}")
    out_video.release()

    # Save the results to a tsv file
    with open(dive_path / f"{video_path.stem}_concepts.tsv", "w") as f:
        f.write("concept\tcount\n")
        for k, v in results.items():
            f.write(f"{k}\t{v}\n")

def process_videos(
        video_files: [str],
        stride_fps: int,
        endpoint_url: str,
        det_model: str,
        vits_model: str,
        allowed_class_names: [str] = None,
        remapped_class_names: dict = None,
        version_id: int = 0,
        skip_load: bool = False,
        min_confidence: float = 0.1,
        min_depth: int = 200,
        max_secs: int = -1,
        max_frames_tracked: int = 300,
):
    multiprocessing.set_start_method("forkserver")
    video_files_args = [
        (v, stride_fps, endpoint_url, det_model, vits_model, allowed_class_names, remapped_class_names, version_id,
         skip_load, min_confidence, min_depth, max_secs, max_frames_tracked, random.choice([1,0]))
        for v in video_files
    ]
    with multiprocessing.Pool(2) as pool:
        pool.map(run_inference_track, video_files_args)


def parse_args():
    parser = argparse.ArgumentParser(
        description=dedent("""\
        Run strided video track pipeline with REDIS queue based load.

        Example: 
        python3 run_strided_track.py /path/to/video.mp4
        """),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--config", required=True, help=f"Configuration files. For example: {CONFIG_YAML}")
    parser.add_argument("--video", help="Video file or directory.", required=False, type=str)
    parser.add_argument("--max-seconds", help="Maximum number of seconds to process.", required=False, type=int, default=-1)
    parser.add_argument("--min-frames", help="Minimum number of frames a track must have.", required=False, type=int, default=5)
    parser.add_argument("--min-score-track", help="Minimum score for a track to be valid.", required=False, type=float, default=0.1)
    parser.add_argument("--min-score-det", help="Minimum score for a detection to be valid.", required=False, type=float, default=0.1)
    parser.add_argument("--max-frames-tracked", help="Maximum number of frames a track can have before closing it.", required=False, type=int, default=300)
    parser.add_argument("--version", help="Version name", required=False, type=str)
    parser.add_argument("--gpu-id", help="GPU ID to use for inference.", required=False, type=int, default=0)
    parser.add_argument("--vits-model", help="ViTS vits_model location", required=False, type=str, default="/mnt/DeepSea-AI/models/m3midwater-vit-b-16/")
    parser.add_argument("--skip-load", help="Skip loading the video reference into Tator.", action="store_true")
    parser.add_argument("--imshow", help="Display the video frames.", action="store_true")
    parser.add_argument(
        "--tsv",
        help="TSV file with video paths per Haddock output",
        required=False,
        type=str,
    )
    parser.add_argument("--stride-fps", help="Frames per second to run detection, e.g. 1 is 1 frame every second, "
                                      "5 is 5 frames a second.", default=3, type=int)
    parser.add_argument(
        "--class_name",
        help="Class name to target inference.",
        default="Ctenophora sp. A",
        type=str,
    )
    parser.add_argument(
        "--endpoint-url",
        help="URL of the inference endpoint.",
        required=False,
        type=str,
    )
    parser.add_argument(
        "--det-model",
        help="Object detection vmodel path.",
        required=False,
        type=str,
    )
    parser.add_argument("--min-depth", help="Minimum depth for detections.", default=0, type=int)
    parser.add_argument("--flush", help="Flush the REDIS database.", action="store_true")
    parser.add_argument(
        '--allowed-classes',
        type=str,
        nargs='+',  # Accepts multiple values®
        help='List of allowed classes.'
    )
    parser.add_argument(
        '--class-remap',
        type=str,
        help='Dictionary of class remapping, formatted as a string.'
    )
    return parser.parse_args()


if __name__ == "__main__":

    args = parse_args()
    config_files, config_dict = setup_config(args.config)

    if TATOR_TOKEN is None:
        logger.error("TATOR_TOKEN environment variable not set")
        exit(1)

    if REDIS_PASSWORD is None:
        logger.error("REDIS_PASSWORD environment variable not set")
        exit(1)

    # Get the version track_id from the database
    project = config_dict["tator"]["project"]
    host = config_dict["tator"]["host"]
    if args.version:  # Override the version in the config file
        config_dict["data"]["version"] = args.version
    version = config_dict["data"]["version"]
    api, project = init_api_project(host=host, token=TATOR_TOKEN, project=project)
    version_id = get_version_id(api, project, version)
    if version_id is None:
        logger.error(f"Failed to get version id for {version}")
        exit(1)

    # Convert the remapped class names to a dictionary
    if args.class_remap:
        args.class_remap = ast.literal_eval(args.class_remap)

    # Need to have a video or TSV file with video paths to process
    if not args.video and not args.tsv:
        logger.error("Must provide either a video or TSV file with video paths")
        exit(1)

    # Connect to Redis
    redis_host = config_dict["redis"]["host"]
    redis_port = config_dict["redis"]["port"]
    redis_queue = redis.Redis(host=redis_host, port=redis_port, password=os.getenv("REDIS_PASSWORD"))
    if not redis_queue.ping():
        logger.error(f"Failed to connect to REDIS queue at {redis_host}:{redis_port}")
        exit(1)

    args_dict = vars(args)
    args_dict["ffmpeg_path"] = config_dict["ffmpeg_path"]

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
            run_inference_track(video_path.as_posix(), version_id, **args_dict)
        elif video_path.is_dir():
            # Fanout to number of CPUs
            video_files = list(video_path.rglob("*.mp4"))
            video_files = [v for v in video_files]
            process_videos(video_files, version_id, **args_dict)
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
        process_videos(video_files, version_id, **args_dict)

    logger.info("Finished processing videos")
