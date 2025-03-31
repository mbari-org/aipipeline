# aipipeline, Apache-2.0 license
# Filename: projects/bio/core/callback.py
# Description: Custom callback for bio projects
import csv
import json
import logging
from datetime import datetime, timedelta

import cv2
import numpy as np
from pandas import read_csv

from aipipeline.projects.bio.core.bioutils import get_ancillary_data, get_video_metadata
from aipipeline.projects.bio.core.predict import Predictor
from biotrack.track import Track

# Logging
logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)
# and log to file
now = datetime.now()
log_filename = f"callback{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)
global redis_queue

class Callback:

    """Base class for callbacks."""

    def on_predict_batch_end(self, predictor: Predictor, tracks: list[Track]):
        """Called at the end of each prediction batch."""
        pass

    def on_predict_start(self, predictor: Predictor):
        """Called at the start of prediction for a video."""
        pass

    def on_end(self, predictor: Predictor):
        """Called at the end of prediction for a video."""
        pass

class AncillaryCallback(Callback):

    """Custom callback to fetch ancillary data for bio projects."""
    def on_predict_start(self, predictor: Predictor):
        video_name = predictor.source.video_name
        redis_queue = predictor.redis_queue
        print(f"Getting metadata for video: {video_name}")
        try:
            md = get_video_metadata(video_name)
            if md is None:
                logger.error(f"Failed to get video metadata for {video_name}")
            else:
                predictor.md = md
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
            if predictor.md is None:
                predictor.md = {}
            else:
                # Remove the video reference from the queue
                video_ref_uuid = predictor.md["video_reference_uuid"]
                redis_queue.delete(f"video_refs_start:{video_ref_uuid}")
                redis_queue.delete(f"video_refs_load:{video_ref_uuid}")

class ExportCallback(Callback):
    
    num_loaded = 0
    def on_predict_start(self, predictor: Predictor):
        output_path = predictor.output_path
        best_pred_path = predictor.best_pred_path
        logger.info(f"Removing {output_path}")
        if best_pred_path.exists():
            best_pred_path.unlink()

    def on_predict_batch_end(self, predictor: Predictor, tracks: list[Track]):
        """ Queue track localizations in REDIS and export to CSV """
        min_frames = predictor.min_frames
        min_score_track = predictor.min_score_track
        version_id = predictor.version_id
        skip_load = predictor.skip_load
        redis_queue = predictor.redis_queue

        config_dict = predictor.config

        for track in tracks:
            best_frame, best_label, best_box, best_score = track.get_best(False)
            best_frame += 1 # Convert to 1-based frame number
            best_time_secs = float(best_frame / predictor.source.frame_rate)
            box_str = ", ".join([f"{box:.4f}" for box in best_box])
            score_str = ", ".join([f"{score:.2f}" for score in best_score])
            logger.info(f"Best track {track.id} is {box_str},{best_label},{score_str} in frame {best_frame}")

            new_loc = {
                "x1": max(float(best_box[0]*predictor.source.width), 0.),
                "y1": max(float(best_box[1]*predictor.source.height), 0.),
                "x2": min(float(best_box[2]*predictor.source.width), predictor.source.width),
                "y2": min(float(best_box[3]*predictor.source.height), predictor.source.height),
                "width": int(predictor.source.width),
                "height": int(predictor.source.height),
                "frame": best_frame,
                "version_id": int(version_id),
                "score": float(best_score[0]),
                "score_s": float(best_score[1]),
                "cluster": "-1",
                "label": best_label[0],
                "label_s": best_label[1],
            }
            if skip_load:
                logger.warning("======>Skipping load through REDIS queue<======")
            is_valid = True
            if track.is_closed():
                logger.info(f"Track {track.id} is closed")
            if track.num_frames < min_frames or best_score[0] < min_score_track:
                logger.info(
                    f"Track {track.id} is too short num frames {track.num_frames} or "
                    f"best score {best_score[0]:.2f} is < {min_score_track}, skipping")
                is_valid = False

            if not skip_load and track.is_closed() and is_valid:
                start_datetime = datetime.fromisoformat(predictor.md["start_timestamp"])
                loc_datetime = start_datetime + timedelta(seconds=best_time_secs)
                ancillary_data = get_ancillary_data(predictor.md['dive'], config_dict, loc_datetime)

                if ancillary_data is None or "depthMeters" not in ancillary_data:
                    logger.error(f"Failed to get ancillary data for {predictor.md['dive']} {start_datetime}")
                    new_loc["dive"] = predictor.source.video_name
                    new_loc["depth"] = "-1"
                    new_loc["iso_datetime"] = loc_datetime.strftime("%Y-%m-%dT%H:%M:%S")
                    new_loc["latitude"] = "-1"
                    new_loc["longitude"] = "-1"
                    new_loc["temperature"] = "-1"
                    new_loc["oxygen"] = "-1"
                else:
                    # Add in the ancillary data
                    new_loc["dive"] = predictor.md["dive"]
                    new_loc["depth"] = ancillary_data["depthMeters"]
                    new_loc["iso_datetime"] = loc_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
                    new_loc["latitude"] = ancillary_data["latitude"]
                    new_loc["longitude"] = ancillary_data["longitude"]
                    new_loc["temperature"] = ancillary_data["temperature"]
                    new_loc["oxygen"] = ancillary_data["oxygen"]

                new_loc = {k: int(v) if isinstance(v, np.integer) else float(v) if isinstance(v, np.floating) else v for
                           k, v in new_loc.items()} # Convert numpy types to python types
                logger.info(f"queuing loc: {new_loc} {predictor.md['dive']} {loc_datetime}")
                redis_queue.hset(f"locs:{predictor.md['video_reference_uuid']}", str(self.num_loaded), json.dumps(new_loc))
                logger.info(f"{predictor.source.video_name} found total possible {self.num_loaded} localizations")
                self.num_loaded += 1

            # Add in the track_id to the new_loc - this is used for displaying an ID with the tracks post-processing
            new_loc["track_id"] = track.id
            new_loc["is_valid"] = is_valid
            if not predictor.best_pred_path.exists():
                with predictor.best_pred_path.open("w") as f:
                    writer = csv.DictWriter(f, fieldnames=list(new_loc.keys()))
                    writer.writeheader()

            with predictor.best_pred_path.open("a") as f:
                writer = csv.DictWriter(f, fieldnames=list(new_loc.keys()))
                writer.writerow(new_loc)
            logger.info(f"Saved track {track.id} to {predictor.best_pred_path}")


class VideoExportCallback(Callback):
    def on_predict_start(self, predictor: Predictor):
        pass

    def on_predict_batch_end(self, predictor: Predictor, tracks: list[Track]):
        pass

    def on_end(self, predictor: Predictor):
        if not predictor.best_pred_path.exists():
            logger.error(f"No best tracks found in {predictor.best_pred_path}")
            return
        # Load the best tracks, remove any duplicates by track_id and sort by frame
        tracks_best_csv = read_csv(predictor.best_pred_path)
        # A duplicate has the same x, y, width, height, frame, score, label
        tracks_best_csv.drop_duplicates(subset=["x1", "y1", "x2", "y2", "frame", "score", "label"], keep="first", inplace=True)

        # Rename the track_id in increasing order from 1
        tracks_best_csv["track_id"] = range(1, len(tracks_best_csv) + 1)
        tracks_best_csv.sort_values(by=["frame"], inplace=True)

        if tracks_best_csv.empty:
            logger.error(f"No tracks found in {tracks_best_csv}")
            return

        # Create the video with the best track annotations
        out_video_path = predictor.output_path / "tracks.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out_video = cv2.VideoWriter(out_video_path.as_posix(), fourcc, predictor.source.fps, predictor.source.size)
        logger.info(f"Creating video {out_video_path} with {len(tracks_best_csv)} tracks")
        max_frame = int(tracks_best_csv["frame"].max() + 10)  # Add 10 frames to the end to ensure all tracks are included
        by_frame = tracks_best_csv.groupby("frame")  # Group by frame
        frame_num = 0
        predictor.source.cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # Set the video to the beginning
        while True:
            # Read the frame and create the annotations if the frame is in the best tracks
            ret, frame = predictor.source.cap.read()
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
                label_s = row.label_s
                score = row.score
                score_s = row.score_s
                is_valid = row.is_valid
                x1 = int(row.x1)
                y1 = int(row.y1)
                x2 = int(row.x2)
                y2 = int(row.y2)
                # Color the rectangle based on a hash of the first 3 characters of the label to get a unique color for each label
                label_color = int(hash(label[:3]) % 256)
                text_color = (255, 255, 255)  # White
                thickness = 1
                if is_valid:
                    thickness = 2
                # Adjust the position of the label if it is too close to the edge
                if x1 < 50:
                    x1 = 50
                if y1 < 50:
                    y1 = 50
                if is_valid:
                    label_str = f"{track_id}:{label}:{score:.2f},{label_s}:{score_s:.2f}"
                else:
                    label_str = f"{track_id}"#:{score:.2f},{label_s}:{score_s:.2f}"
                cv2.putText(frame, label_str, (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 1,
                            text_color, thickness)
                cv2.rectangle(frame, (x1, y1), (x2, y2), label_color, 1)
            out_video.write(frame)
            frame_num += 1