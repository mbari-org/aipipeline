# aipipeline, Apache-2.0 license
# Filename: projects/bio/core/predict.py
# Description: Predictor class for bio projects
import logging
from pathlib import Path
from typing import Any

from aipipeline.projects.bio.core.bioutils import show_boxes, filter_blur_pred, get_ancillary_data
from biotrack.tracker import BioTracker
import torch

from aipipeline.projects.bio.core.video import VideoSource

logger = logging.getLogger(__name__)

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
        self.output_path = Path("/tmp") / source.name
        frame_path = self.output_path / "frames"
        self.crop_path = self.output_path / "crops"
        frame_path.mkdir(parents=True, exist_ok=True)
        self.crop_path.mkdir(parents=True, exist_ok=True)
        self.device = torch.device(f"cuda:{self.device_id}" if torch.cuda.is_available() else "cpu")
        self.tracker = tracker
        self.duration_secs = source.duration_secs
        self.fps = source.frame_rate
        self.stride_fps = kwargs.get("stride_fps", 5)
        self.total_frames = int(self.duration_secs * self.fps)
        self.frame_stride = int(self.fps / self.stride_fps)
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
        if self.version_id < 0 and not self.skip_load:
            raise ValueError("Need to set the database version,e.g. --version Baseline if loading to the database")

    def run_callbacks(self, method_name, *args):
        for callback in self.callbacks:
            method = getattr(callback, method_name, None)
            if callable(method):
                method(*args)

    def predict(self):
        self.run_callbacks("on_predict_start", self.redis_queue, self, self.source.name)
        if self.md is None or 'dive' not in self.md:
            logger.error("No dive metadata found")
            return

        date_start = get_ancillary_data(self.md['dive'], self.config, self.md['start_timestamp'])
        if date_start is None or "depthMeters" not in date_start:
            logger.error(f"Failed to get ancillary data for {self.md['dive']} {date_start}")
            return

        depth = date_start["depthMeters"]

        if depth < self.min_depth:
            logger.warning(f"Depth {depth} < {self.min_depth} skip processing {self.source.name}")
            return

        frame_num = 0
        batch_pred = []

        for batch_num, self.batch in enumerate(self.source):

            batch_d, batch_c = self.batch
            frame_num += len(batch_d)

            self.run_callbacks("on_predict_batch_start", self.batch)

            current_time_secs = float(frame_num * self.frame_stride / self.source.frame_rate)
            print(f'Processing batch of {len(batch_d)} images starting at {current_time_secs}')

            predictions = self.detection_model.predict_images(batch_d, self.min_score_det)
            print(f"Predictions: {predictions}")
            batch_pred.extend(predictions)

            len_before = len(batch_c)
            filtered_pred = filter_blur_pred(batch_c, batch_pred, self.crop_path, self.source.width, self.source.height)
            len_after = len(filtered_pred)
            print(f"Filtered {len_before - len_after} blurry detections")

            start_frame = max(0, batch_num*len(batch_d))
            end_frame = batch_num * len(batch_d)

            # Convert the x, y to the image coordinates
            det_n = []
            for i, d in enumerate(filtered_pred):
                t_d = { "x": d["x"] * self.source.width,
                        "y": d["y"] * self.source.height,
                        "xx": (d["x"] + d["w"]) * self.source.width,
                        "xy": (d["y"] + d["h"]) * self.source.height,
                        "frame": d["frame"],
                        "batch_idx": d["batch_idx"],
                        "score": d["confidence"],
                        "crop_path": d["crop_path"]}
                det_n.append(t_d)
            print(f"Tracking {len(det_n)} detections from frame {start_frame} to {end_frame}")
            batch_pred = []

            tracks = self.tracker.update_batch((start_frame, end_frame),
                                          self.source.frame_stack(),
                                          detections=det_n,
                                          max_empty_frames=5,
                                          max_frames=self.max_frames_tracked,
                                          max_cost=0.5)

            # Display the results
            if self.imshow:
                show_boxes(batch_d, predictions)

            self.run_callbacks("on_predict_batch_end", (self.skip_load, self.redis_queue, self.version_id, self.config, self, tracks, self.min_frames, self.min_score_track))

            self.tracker.purge_closed_tracks()

            '''if self.max_seconds and current_time_secs > self.max_seconds:
                logger.info(f"Stopping at {current_time_secs} seconds")
                break'''
