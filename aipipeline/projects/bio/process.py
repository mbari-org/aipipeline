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
from aipipeline.projects.bio.core.callback import AncillaryCallback, ExportCallback, VideoExportCallback
from aipipeline.db_utils import get_version_id

from aipipeline.projects.bio.core.predict import Predictor
from aipipeline.projects.bio.core.video import VideoSource
from aipipeline.prediction.inference import FastAPIYV5, YV5, YV8_10

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
            model = YV8_10(args.det_model)
        else:
            # Assume YV8 or 10 if no model is specified
            model = YV8_10(args.det_model, device_num=args.gpu_id)

        batch_size = args.batch_size
 
    source = VideoSource(**args_dict)

    # Create a tracker
    tracker = BioTracker(source.width, source.height, **args_dict)

    # Create the callbacks for capturing ancillary data and exporting the results
    callbacks = [ExportCallback]

    if args.create_video:
        callbacks.append(VideoExportCallback)

    if args.skip_load:
        redis_queue = None
        version_id = 1
    else:
        callbacks.append(AncillaryCallback)
        redis_queue = redis_queue
        version_id = version_id

    # Create the predictor and run
    predictor = Predictor(model, source, tracker, config_dict, redis_queue=redis_queue, callbacks=callbacks, version_id=version_id, **args_dict)
    predictor.predict(args.skip_load)