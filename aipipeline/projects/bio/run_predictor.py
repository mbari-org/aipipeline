# aipipeline, Apache-2.0 license
# Filename: projects/bio/run_predictor.py
# Description: Utility functions to run the video processing prediction pipeline
from concurrent.futures import ThreadPoolExecutor

from biotrack.tracker import BioTracker

import concurrent.futures
from aipipeline.projects.bio.core.callback import AncillaryCallback, ExportCallback, VideoExportCallback
from aipipeline.projects.bio.core.predict import Predictor
from aipipeline.projects.bio.core.video import VideoSource
from aipipeline.prediction.inference import FastAPIYV5, YV5, YV8_10


def run_predictor(video, args_dict, config_dict, version_id):
    import os
    source = VideoSource(video, **args_dict)

    tracker = None if args_dict.get("skip_track") else BioTracker(source.width, source.height, **args_dict)

    if args_dict.get("endpoint_url"):
        model = FastAPIYV5(args_dict["endpoint_url"])
    else:
        if "yolov5" in args_dict["det_model"]:
            model = YV5(args_dict["det_model"], device=args_dict["device"])
        else:
            model = YV8_10(args_dict["det_model"], device=args_dict["device"])

    callbacks = [ExportCallback]
    if args_dict.get("create_video"):
        callbacks.append(VideoExportCallback)
    if not args_dict.get("skip_load"):
        callbacks.append(AncillaryCallback)

    redis_queue = None
    if not args_dict.get("skip_load"):
        import redis
        redis_queue = redis.Redis(
            host=config_dict["redis"]["host"],
            port=config_dict["redis"]["port"],
            password=os.getenv("REDIS_PASSWORD")
        )

    predictor = Predictor(
        model, source, tracker, config_dict,
        redis_queue=redis_queue,
        callbacks=callbacks,
        version_id=version_id,
        **args_dict
    )
    return predictor.predict(args_dict.get("skip_load", False))


def process_batch_parallel(batch, args_dict, config_dict, version_id):
    import random
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        futures = [
            executor.submit(
                process_single_file,
                path,
                random.randint(0, 1), # randomly assign GPU0 or GPU1
                args_dict.copy(),
                config_dict,
                version_id
            )
            for path in batch
        ]
        return [f.result() for f in concurrent.futures.as_completed(futures)]



def process_single_file(path, gpu_id, args_dict, config_dict, version_id):
    import time
    args_copy = args_dict.copy()
    device = f"cuda:{gpu_id}"
    args_copy["device"] = device
    start = time.time()
    run_predictor(path, args_copy, config_dict, version_id)
    end = time.time()
    return f"Processed file: {path} on GPU {device} with args {args_copy} in {end - start:.2f} seconds"