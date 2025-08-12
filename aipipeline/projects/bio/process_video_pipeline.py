# aipipeline, Apache-2.0 license
# Filename: projects/bio/process_video_pipeline.py
# Description: Process video files using Apache Beam with or without tracking
from datetime import datetime

import dotenv
import logging
import os

import apache_beam as beam
from apache_beam.io.fileio import MatchFiles, ReadMatches
from apache_beam.options.pipeline_options import PipelineOptions

from aipipeline.config_setup import setup_config
from aipipeline.projects.bio.core.args import parse_args
from aipipeline.projects.bio.run_predictor import process_batch_parallel
from mbari_aidata.plugins.loaders.tator.common import init_api_project, get_version_id

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
log_filename = f"process_video_pipeline_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


def main():
    args = parse_args()
    config_files, config_dict = setup_config(args.config)
    video = args.video

    args_dict = vars(args)
    # Remove the dictionary item video as this is defined at batch time through FlatMap
    del args_dict["video"]
    args_dict["ffmpeg_path"] = config_dict["ffmpeg_path"]
    for mount in config_dict["mounts"]:
        if mount["name"] == "video":
            args_dict["video_mount"] = mount
            break

    version_id = 1
    if not args.skip_load:
        import redis, os
        redis_host = config_dict["redis"]["host"]
        redis_port = config_dict["redis"]["port"]
        redis_queue = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=os.getenv("REDIS_PASSWORD")
        )

        if args.flush:
            keys = []
            keys += redis_queue.keys("video_refs_start:*")
            keys += redis_queue.keys("video_refs_load:*")
            keys += redis_queue.keys("locs:*")
            keys += redis_queue.keys("tator_ids_v:*")
            for key in keys:
                redis_queue.delete(key)

        host = config_dict["tator"]["host"]
        project = config_dict["tator"]["project"]
        if args.version:
            config_dict["data"]["version"] = args.version
        api, project_id = init_api_project(host=host, token=os.getenv("TATOR_TOKEN"), project=project)
        version_id = get_version_id(api, project_id, config_dict["data"]["version"])

    # For debugging purposes, uncomment to process a single file
    # from aipipeline.projects.bio.run_predictor import process_single_file
    # process_single_file(video,0,args_dict,config_dict,version_id)
    print(f"Processing video: {video}")
    options = PipelineOptions()
    with beam.Pipeline(options=options) as p:
        (
            p
            | "Match Files" >> MatchFiles(file_pattern=video)
            | "Read Matches" >> ReadMatches()
            | "Get File Paths" >> beam.Map(lambda f: f.metadata.path)
            | "Batch into 6" >> beam.BatchElements(min_batch_size=6, max_batch_size=6)
            | "Run in Parallel on GPUs" >> beam.Map(
                lambda batch: process_batch_parallel(
                    batch,
                    args_dict=args_dict,
                    config_dict=config_dict,
                    version_id=version_id
                )
            )
        )


if __name__ == "__main__":
    main()
