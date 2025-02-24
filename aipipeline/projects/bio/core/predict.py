# aipipeline, Apache-2.0 license
# Filename: projects/bio/core/predict.py
# Description: Predictor class for bio projects
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from aipipeline.projects.bio.core.bioutils import show_boxes, filter_blur_pred, get_ancillary_data
from biotrack.tracker import BioTracker
import torch

from aipipeline.projects.bio.core.video import VideoSource

# Logging
logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)
# and log to file
now = datetime.now()
log_filename = f"predict_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

class Predictor:
    def __init__(self, detection_model: Any, source: VideoSource, tracker: BioTracker, config_dict:dict, redis_queue=None,callbacks=None, **kwargs):
        self.md = {}
        self.callbacks = callbacks or []
        self.config = config_dict
        self.min_depth = kwargs.get("min_depth", -1)
        self.detection_model = detection_model
        self.source = source
        self.device_id = kwargs.get("device_id", 0)
        self.has_gpu = torch.cuda.is_available()
        self.output_path = Path("/tmp") / source.video_name
        frame_path = self.output_path / "frames"
        self.crop_path = self.output_path / "crops"
        frame_path.mkdir(parents=True, exist_ok=True)
        self.crop_path.mkdir(parents=True, exist_ok=True)
        self.device = torch.device(f"cuda:{self.device_id}" if torch.cuda.is_available() else "cpu")
        self.tracker = tracker
        self.duration_secs = source.duration_secs
        self.fps = source.frame_rate
        self.total_frames = int(self.duration_secs * self.fps)
        self.batch_size = source.batch_size
        self.max_seconds = kwargs.get("max_seconds", None)
        self.imshow =  kwargs.get("imshow", False)
        self.max_frames_tracked = kwargs.get("max_frames_tracked", 100)
        self.redis_queue = redis_queue
        self.min_score_det = kwargs.get("min_score_det", 0.1)
        self.min_frames = kwargs.get("min_frames", 5)
        self.min_score_track = kwargs.get("min_score_track", 0.1)
        self.skip_load = kwargs.get("skip_load", False)
        self.version_id = kwargs.get("version_id", -1)
        self.best_csv_path = self.output_path / "best_track.csv"
        if self.version_id < 0 and not self.skip_load:
            raise ValueError("Need to set the database version, e.g. --version Baseline if loading to the database")

    def run_callbacks(self, method_name:str, *args: Any) -> None:
        for callback in self.callbacks:
            method = getattr(callback, method_name, None)
            if callable(method):
                bound_method = method.__get__(callback)  # Ensure correct binding
                bound_method(*args)

    @property
    def best_pred_path(self):
        return self.best_csv_path

    def predict(self, skip_load:bool=False):
        self.run_callbacks("on_predict_start", self)

        if not skip_load:
            if self.md is None or 'dive' not in self.md:
                logger.error("No dive metadata found")
                return

            date_start = get_ancillary_data(self.md['dive'], self.config, self.md['start_timestamp'])
            if date_start is None or "depthMeters" not in date_start:
                logger.error(f"Failed to get ancillary data for {self.md['dive']} {date_start}")
                input("All ancillary data will be missing for this dive. Press any key to continue")
            else:
                depth = date_start["depthMeters"]

                if depth < self.min_depth:
                    logger.warning(f"Depth {depth} < {self.min_depth} skip processing {self.source.name}")
                    return

        true_frame_num = 0

        for batch_num, self.batch in enumerate(self.source):

            batch_t = self.batch # Batch tensor of images preprocessed
            true_frame_range = np.arange(true_frame_num, true_frame_num + len(batch_t)).tolist()

            current_time_secs = float(true_frame_num / self.source.frame_rate)
            logger.info(f'Processing batch of {len(batch_t)} images ending at {current_time_secs}')

            batch_s = batch_t[::self.source.stride]  # Only detect in every stride image
            image_stack_p = torch.nn.functional.interpolate(batch_s, size=(1280,1280), mode='bilinear', align_corners=False) # Resize for detection
            predictions = self.detection_model.predict_images(image_stack_p, self.min_score_det)

            logger.info(f"Filtering blurry detections")
            filtered_pred = filter_blur_pred(batch_s, predictions, self.crop_path, self.source.width, self.source.height)

            # Convert the x, y to the image coordinates and adjust the frame number to reflect the stride
            det_n = []
            for i, d in enumerate(filtered_pred):
                t_d = { "x": d["x"],
                        "y": d["y"],
                        "xx": (d["x"] + d["w"]),
                        "xy": (d["y"] + d["h"]),
                        "w": d["w"],
                        "h": d["h"],
                        "frame":d["frame"] * self.source.stride,
                        "score": d["confidence"],
                        "crop_path": d["crop_path"]}
                det_n.append(t_d)
                logger.info(f"Detection {i} {t_d}")
            logger.info(f"Tracking {len(det_n)} detections from frame {true_frame_range[0]} to {true_frame_range[-1]}")

            image_stack_t = torch.nn.functional.interpolate(batch_t, size=(self.tracker.model_height, self.tracker.model_width), mode='bilinear', align_corners=False)
            image_stack = (image_stack_t * 255.0).byte()  # Denormalize and convert to uint8
            image_stack = image_stack.cpu().numpy()  # Convert to NumPy array
            image_stack = image_stack.transpose(0, 2, 3, 1)[..., ::-1]  # Reverse transpose and channel order (BGR to RGB)

            tracks = self.tracker.update_batch(true_frame_range[0],
                                          image_stack.copy(),
                                          detections=det_n,
                                          max_empty_frames=self.source.stride*5,
                                          max_frames=self.max_frames_tracked,
                                          save_cotrack_video=True,
                                          imshow=self.imshow)

            # Display the predictions
            if self.imshow:
                image_stack_s = torch.nn.functional.interpolate(batch_t, size=(1280, 1280), mode='bilinear',
                                                                align_corners=False)  # Resize for detection
                show_boxes(image_stack_s, det_n)

            # Report how many tracks are greater than the minimum frames
            good_tracks = [t for t in tracks if t.num_frames > self.min_frames]
            logger.info("===============================================")
            logger.info(f"Number of tracks {len(tracks)}")
            logger.info(f"Number of good tracks {len(good_tracks)}")
            for t in good_tracks:
                t.dump()

            predictor = self
            if self.max_seconds and current_time_secs > self.max_seconds:
                logger.info(f"Reached {self.max_seconds}. Stopping at {current_time_secs} seconds")
                self.tracker.close_all_tracks()
                self.run_callbacks("on_predict_batch_end", predictor, tracks)
                self.tracker.purge_closed_tracks(true_frame_num)
                self.run_callbacks("on_end", predictor)
                return

            self.run_callbacks("on_predict_batch_end", predictor, tracks)
            self.tracker.purge_closed_tracks(true_frame_num)
            true_frame_num += len(batch_t)