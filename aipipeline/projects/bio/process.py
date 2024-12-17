import logging
import os
from datetime import datetime

import dotenv

from biotrack.tracker import BioTracker

from aipipeline.config_setup import setup_config
from aipipeline.prediction.library import init_api_project
from projects.bio.core.args import parse_args
from projects.bio.core.callback import AncillaryCallback, ExportCallback
from aipipeline.db_utils import get_version_id
import redis

from projects.bio.core.predict import Predictor
from projects.bio.core.video import VideoSource
from projects.bio.model.inference import FastAPIYV5, YV5

# Global variables
idv = 1  # video index
idl = 1  # localization index

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
log_filename = f"predictor_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

if __name__ == "__main__":

    args = parse_args()
    config_files, config_dict = setup_config(args.config)
    args_dict = vars(args)
    args_dict["ffmpeg_path"] = config_dict["ffmpeg_path"]

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
        model = YV5(args.model)
        batch_size = args.batch_size

    source = VideoSource(args.video, batch_size=batch_size)

    # Create a tracker and predictor
    callbacks = [AncillaryCallback(), ExportCallback()]
    tracker = BioTracker(source.width, source.height, **args_dict)
    predictor = Predictor(model, source, tracker, config_dict, redis_queue=redis_queue, callbacks=callbacks, version_id=version_id, **args_dict)

    # Run the predictor
    predictor.predict()