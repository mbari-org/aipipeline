# aipipeline, Apache-2.0 license
# Filename: projects/bio/core/predict.py
# Description: Predictor class for bio projects
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from aipipeline.projects.bio.core.bioutils import show_boxes, filter_blur_pred, get_ancillary_data
from biotrack.embedding import ViTWrapper
from biotrack.track import Track
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
    def __init__(self, detection_model: Any, source: VideoSource, tracker: BioTracker, config_dict:dict, redis_queue=None, callbacks=None, **kwargs):
        self.md = {}
        self.callbacks = callbacks or []
        self.config = config_dict
        self.min_depth = kwargs.get("min_depth", -1)
        self.max_depth = kwargs.get("max_depth", -1)
        self.class_name = kwargs.get("class_name", None) # the class name to target for prediction, if None, all classes are used
        self.detection_model = detection_model
        self.fake_track_id = 0 # only used if no tracker is available
        self.source = source
        self.has_gpu = torch.cuda.is_available()
        self.output_path = Path("/tmp") / source.video_name
        frame_path = self.output_path / "frames"
        self.crop_path = self.output_path / "crops"
        frame_path.mkdir(parents=True, exist_ok=True)
        self.crop_path.mkdir(parents=True, exist_ok=True)
        self.device = torch.device(kwargs.get("device", "cpu"))
        self.tracker = tracker
        if self.tracker is None:
            model_name = kwargs.get("vits_model")
            if model_name is None:
                raise ValueError("Need to set the model name for the Vision Transformer if no tracker is provided")
            self.vit_wrapper = ViTWrapper(device=kwargs.get("device", "cpu"), model_name=model_name)
        self.duration_secs = source.duration_secs
        self.fps = source.frame_rate
        self.total_frames = int(self.duration_secs * self.fps)
        self.batch_size = source.batch_size
        self.max_seconds = kwargs.get("max_seconds", None)
        self.imshow =  kwargs.get("imshow", False)
        self.remove_blurry = kwargs.get("remove_blurry", False)
        self.max_frames_tracked = kwargs.get("max_frames_tracked", 100)
        self.save_cotrack_video = kwargs.get("save_cotrack_video", False)
        self.redis_queue = redis_queue
        self.min_score_det = kwargs.get("min_score_det", 0.1)
        self.min_frames = kwargs.get("min_frames", 5)
        self.min_score_track = kwargs.get("min_score_track", 0.1)
        self.skip_load = kwargs.get("skip_load", False)
        self.version_id = kwargs.get("version_id", -1)
        self.best_csv_path = self.output_path / "best_track.csv"
        if self.version_id < 0 and not self.skip_load:
            raise ValueError("Need to set the database version, e.g. --version Baseline if loading to the database")


    # def __del__(self):
    #     torch.cuda.ipc_collect()
    #     torch.cuda.empty_cache()

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

        true_frame_num = 0
        last_depth = self.min_depth

        for batch_num, self.batch in enumerate(self.source):

            batch_t = self.batch # Batch tensor of images preprocessed
            true_frame_range = np.arange(true_frame_num, true_frame_num + len(batch_t)).tolist()

            current_time_secs = float(true_frame_num / self.source.frame_rate)
            logger.info(f'Processing batch of {len(batch_t)} images ending at {current_time_secs}')

            image_stack_p = torch.nn.functional.interpolate(batch_t, size=(1280,1280), mode='bilinear', align_corners=False) # Resize for detection
            predictions = self.detection_model.predict_images(image_stack_p, self.min_score_det)

            logger.info(f"Filtering blurry detections")
            filtered_pred = filter_blur_pred(batch_t, predictions, self.crop_path, self.source.width, self.source.height)

            # Convert the x, y to the image coordinates and adjust the frame number to reflect the stride
            det_n = []
            for i, d in enumerate(filtered_pred):
                t_d = { "x": d["x"],
                        "y": d["y"],
                        "xx": (d["x"] + d["w"]),
                        "xy": (d["y"] + d["h"]),
                        "w": d["w"],
                        "h": d["h"],
                        "frame":d["frame"],
                        "score": d["confidence"],
                        "crop_path": d["crop_path"]}
                det_n.append(t_d)
                logger.info(f"Detection {i} {t_d}")
            logger.info(f"Found {len(det_n)} detections from frame {true_frame_range[0]} to {true_frame_range[-1]}")

            if self.tracker:
                image_stack_t = torch.nn.functional.interpolate(batch_t, size=(self.tracker.model_height, self.tracker.model_width), mode='bilinear', align_corners=False)
                image_stack = (image_stack_t * 255.0).byte()  # Denormalize and convert to uint8
                image_stack = image_stack.cpu().numpy()  # Convert to NumPy array
                image_stack = image_stack.transpose(0, 2, 3, 1)[..., ::-1]  # Reverse transpose and channel order (BGR to RGB)
                tracks = self.tracker.update_batch(true_frame_range[0],
                                              image_stack.copy(),
                                              detections=det_n,
                                              remove_blurry=self.remove_blurry,
                                              max_empty_frames=self.max_frames_tracked*2,
                                              max_frames=self.max_frames_tracked,
                                              save_cotrack_video=self.save_cotrack_video,
                                              imshow=self.imshow)

                # Display the predictions
                if self.imshow:
                    image_stack_s = torch.nn.functional.interpolate(batch_t, size=(1280, 1280), mode='bilinear',
                                                                    align_corners=False)  # Resize for detection
                    show_boxes(image_stack_s, det_n)

                # Remove any tracks that do not match the target class if specified
                if self.class_name:
                    for t in tracks:
                        if t.predicted_classes[0] != self.class_name and t.predicted_classes[1] != self.class_name:
                            logger.info(f"Removing track {t.track_id} with class {t.predicted_classes} - not {self.class_name}")
                            t.close_track()

                # Report how many tracks are greater than the minimum frames and not closed
                good_tracks = [t for t in tracks if t.num_frames >= self.min_frames and not t.is_closed()]
                logger.info("===============================================")
                logger.info(f"Number of tracks {len(tracks)}")
                logger.info(f"Number of good tracks {len(good_tracks)}")
                for t in good_tracks:
                    t.dump()

                predictor = self
                self.run_callbacks("on_predict_batch_end", predictor, tracks)
                self.tracker.purge_closed_tracks(true_frame_num)
            else:
                logger.info("Tracking skipped - tracking disabled")
                tracks = []
                new_tracks = []
                unique_frames = np.unique([d["frame"] for d in det_n])
                for k, i in enumerate(unique_frames):
                    boxes = [[d['x'], d['y'], d['xx'], d['xy']] for d in det_n if d["frame"] == i]
                    images = [d['crop_path'] for d in det_n if d["frame"] == i]
                    embeddings, predicted_classes, predicted_scores, _, _ = self.vit_wrapper.process_images(images, boxes)
                    for img_path, emb, box, scores, labels in zip(images, embeddings, boxes, predicted_scores, predicted_classes):
                        if self.class_name and labels[0] != self.class_name:
                            logger.info(f"Removing track {self.fake_track_id} with class {labels} - not {self.class_name}")
                            continue

                        if 'start_timestamp' in self.md and 'camera_id' in self.md:
                            date_start = get_ancillary_data(self.md, self.config, self.md['start_timestamp'])
                            if date_start is None or "depthMeters" not in date_start:
                                logger.error(f"Failed to get ancillary data for {self.md['camera_id']} {date_start}")
                                # input("All ancillary data will be missing for this dive. Press any key to continue")
                            else:
                                depth = date_start["depthMeters"]

                                if self.min_depth > 0 and depth < self.min_depth:
                                    logger.warning(
                                        f"Depth {depth} < {self.min_depth} skip processing {self.source.video_name}")
                                    # Stop if we are above the min depth and ascending
                                    if depth < last_depth:
                                        logger.info(f"Reached min depth {self.min_depth} and ascending. Stopping at {depth} meters")
                                        return
                                    continue

                                if self.max_depth > 0 and depth > self.max_depth:
                                    logger.warning(
                                        f"Depth {depth} > {self.max_depth} skip processing {self.source.video_name}")
                                    # Stop if we are beyond the max depth and descending
                                    if depth > last_depth:
                                        logger.info(f"Reached max depth {self.max_depth} and descending. Stopping at {depth} meters")
                                        return
                                    continue

                                last_depth = depth
                        t = Track(self.fake_track_id, self.source.width, self.source.height)
                        true_frame = d["frame"] +  true_frame_num
                        logger.info(f"Adding box {box} to frame {true_frame}")
                        t.update_box(frame_num=true_frame, box=box, scores=scores, labels=labels, emb=emb, image_path=img_path)
                        # Force close the track since loading does not happen on open tracks
                        t.close_track()
                        self.fake_track_id += 1
                        tracks.append(t)

            if self.max_seconds and current_time_secs > self.max_seconds:
                logger.info(f"Reached {self.max_seconds}. Stopping at {current_time_secs} seconds")
                if self.tracker:
                    self.tracker.close_all_tracks()
                    self.tracker.purge_closed_tracks(true_frame_num)
                self.run_callbacks("on_predict_batch_end", self, tracks)
                return

            self.run_callbacks("on_predict_batch_end", self, tracks)
            true_frame_num = self.source.frame

        if self.tracker:
            self.tracker.close_all_tracks()
            self.tracker.purge_closed_tracks(true_frame_num)