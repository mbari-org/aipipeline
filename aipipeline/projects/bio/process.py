# aipipeline, Apache-2.0 license
# Filename: projects/bio/process.py
# Description: Compute stats for downloaded datasets and save to a csv file
from datetime import datetime

import cv2
import dotenv
import logging
import os
import redis

from biotrack.tracker import BioTracker
from pandas import read_csv

from aipipeline.config_setup import setup_config
from aipipeline.prediction.library import init_api_project
from aipipeline.projects.bio.core.args import parse_args
from aipipeline.projects.bio.core.callback import AncillaryCallback, ExportCallback
from aipipeline.db_utils import get_version_id

from aipipeline.projects.bio.core.predict import Predictor
from aipipeline.projects.bio.core.video import VideoSource
from aipipeline.prediction.inference import FastAPIYV5, YV5, YV10

# Global variables
idv = 1  # video index
idl = 1  # localization index

# Secrets
dotenv.load_dotenv()
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
TATOR_TOKEN = os.getenv("TATOR_TOKEN")

# Multiprocessing; spawn is the only method that works with CUDA
import torch.multiprocessing as mp
mp.set_start_method('spawn', force=True)

# Logging
logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)
# and log to file
now = datetime.now()
log_filename = f"process_bio_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

if __name__ == "__main__":

    args = parse_args()
    config_files, config_dict = setup_config(args.config)
    args_dict = vars(args)
    args_dict["ffmpeg_path"] = config_dict["ffmpeg_path"]

    if not args.skip_load:
        if TATOR_TOKEN is None:
            logger.error("TATOR_TOKEN environment variable not set")
            exit(1)

        if REDIS_PASSWORD is None:
            logger.error("REDIS_PASSWORD environment variable not set")
            exit(1)

        # Connect to Redis
        redis_host = config_dict["redis"]["host"]
        redis_port = config_dict["redis"]["port"]
        redis_queue = redis.Redis(host=redis_host, port=redis_port, password=os.getenv("REDIS_PASSWORD"))
        if not redis_queue.ping():
            logger.error(f"Failed to connect to REDIS queue at {redis_host}:{redis_port}")
            exit(1)

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

        # Get the version track_id from the database
        project_name = config_dict["tator"]["project"]
        host = config_dict["tator"]["host"]
        if args.version:  # Override the version in the config file
            config_dict["data"]["version"] = args.version
        version = config_dict["data"]["version"]
        api, project_id = init_api_project(host=host, token=TATOR_TOKEN, project_name=project_name)
        version_id = get_version_id(api, project_id, version)
        if version_id is None:
            logger.error(f"Failed to get version id for {version}")
            exit(1)

    if args.endpoint_url: # Initialize the YOLOv5 detector instance if we have an endpoint
        model = FastAPIYV5(args.endpoint_url)
        batch_size = 1
    else: # Load the YOLOv5 model from a local file
        if 'yolov5' in args.det_model:
            model = YV5(args.det_model, device_num=args.gpu_id)
        elif 'yolov10' in args.det_model:
            model = YV10(args.det_model)
        else:
            # Assume YOLOv5 if no model is specified
            model = YV5(args.det_model, device_num=args.gpu_id)

        batch_size = args.batch_size
 
    source = VideoSource(**args_dict)

    # Create a tracker and predictor
    tracker = BioTracker(source.width, source.height, **args_dict)
    if args.skip_load:
        callbacks = [ExportCallback]
        predictor = Predictor(model, source, tracker, config_dict, redis_queue=None, callbacks=callbacks, version_id=1,
                              **args_dict)
    else:
        callbacks = [AncillaryCallback(), ExportCallback()]
        predictor = Predictor(model, source, tracker, config_dict, redis_queue=redis_queue, callbacks=callbacks, version_id=version_id, **args_dict)

    # Run the predictor
    predictor.predict(args.skip_load)

    # Create video with tracks if requested
    if args.create_video:
        if not predictor.best_pred_path.exists():
            logger.error(f"No best tracks found in {predictor.best_pred_path}")
            exit(1)
        # Load the best tracks, remove any duplicates by track_id and sort by frame
        tracks_best_csv = read_csv(predictor.best_pred_path)
        tracks_best_csv.drop_duplicates(subset=["track_id"], keep="first", inplace=True)
        tracks_best_csv.sort_values(by=["frame"], inplace=True)
        columns_best = tracks_best_csv.columns

        if tracks_best_csv.empty:
            logger.error(f"No tracks found in {tracks_best_csv}")
            exit(1)

        # Create the video with the best track annotations
        out_video_path = predictor.output_path / "tracks.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out_video = cv2.VideoWriter(out_video_path.as_posix(), fourcc, source.fps, source.size)
        logger.info(f"Creating video {out_video_path} with {len(tracks_best_csv)} tracks")
        max_frame = int(tracks_best_csv["frame"].max() + 10) # Add 10 frames to the end to ensure all tracks are included
        by_frame = tracks_best_csv.groupby("frame") # Group by frame
        frame_num = 0
        source.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        while True:
            # Read the frame and create the annotations if the frame is in the best tracks
            ret, frame = source.cap.read()
            if not ret or frame_num > max_frame:
                break
            if frame_num not in by_frame.groups:
                out_video.write(frame)
                frame_num += 1
                continue
            in_frame = by_frame.get_group(frame_num)
            for row in in_frame.itertuples():
                track_id = row.track_id
                label = row.label
                x1 = int(row.x1)
                y1 = int(row.y1)
                x2 = int(row.x2)
                y2 = int(row.y2)
                # Color the rectangle based on a hash of the first 3 characters of the label to get a unique color for each label
                color = int(hash(label[:3]) % 256)
                # Adjust the position of the label if it is too close to the edge
                if x1 < 50:
                    x1 = 50
                if y1 < 50:
                    y1 = 50
                cv2.putText(frame, f"{track_id}: {label}", (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            out_video.write(frame)
            frame_num += 1