# aipipeline, Apache-2.0 license
# Filename: projects/bio/core/callback.py
# Description: Custom callback for bio projects
import json
import logging
import math
from datetime import datetime, timedelta

from aipipeline.projects.bio.core.bioutils import get_ancillary_data, get_video_metadata

logger = logging.getLogger(__name__)

global redis_queue

class Callback:

    """Base class for callbacks."""
    def on_predict_batch_start(self, batch):
        """Called at the start of each prediction batch."""
        pass

    def on_predict_batch_end(self, predictions):
        """Called at the end of each prediction batch."""
        pass

    def on_predict_start(self, redis_queue, predictor, video_name):
        """Called at the start of prediction for a video."""
        pass

class AncillaryCallback(Callback):

    """Custom callback to fetch ancillary data for bio projects."""
    def on_predict_start(self, redis_queue, predictor, video_name):
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
    def on_predict_start(self, redis_queue, predictor, video_name):
        output_path = predictor.output_path
        logger.info(f"Removing {output_path}")
        for output_path in output_path.rglob("*.jpg"):
            output_path.unlink()
        for output_path in output_path.rglob("*.json"):
            output_path.unlink()

    def on_predict_batch_end(self, batch):
        """ Queue track localizations in REDIS"""
        skip_load, redis_queue, version_id, config_dict, predictor, tracks, min_frames, min_score_track = batch
        if skip_load:
            return

        if len(tracks) > 0:
            start_datetime = datetime.fromisoformat(predictor.md["start_timestamp"])
            config_dict = config_dict

            for track in tracks:
                logger.info(f"Closed track {track.id}")
                best_frame, best_pt, best_label, best_box, best_score = track.get_best(False)
                best_time_secs = float(best_frame * predictor.source.stride / predictor.source.frame_rate)
                logger.info(f"Best track {track.id} is {best_pt},{best_box},{best_label},{best_score} in frame {best_frame}")

                if track.num_frames <= min_frames or best_score[0] <= min_score_track:
                    logger.info(
                        f"Track {track.id} is too short num frames {track.num_frames} or best score {best_score[0]} is < {min_score_track}, skipping")
                    continue

                loc_datetime = start_datetime + timedelta(seconds=best_time_secs)
                ancillary_data = get_ancillary_data(predictor.md['dive'], config_dict, loc_datetime)

                if ancillary_data is None or "depthMeters" not in ancillary_data:
                    logger.error(f"Failed to get ancillary data for {predictor.md['dive']} {start_datetime}")
                    continue

                new_loc = {
                    "x1": max(float(best_box[0]*predictor.source.width), 0.),
                    "y1": max(float(best_box[1]*predictor.source.height), 0.),
                    "x2": float(best_box[2]*predictor.source.width),
                    "y2": float(best_box[3]*predictor.source.height),
                    "width": int(predictor.source.width),
                    "height": int(predictor.source.height),
                    "frame": int((best_frame + 1) * predictor.source.stride),
                    "version_id": int(version_id),
                    "score": float(best_score[0]),
                    "score_s": float(best_score[1]),
                    "cluster": "-1",
                    "label": best_label[0],
                    "label_s": best_label[1],
                    "dive": predictor.md["dive"],
                    "depth": ancillary_data["depthMeters"],
                    "iso_datetime": loc_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "latitude": ancillary_data["latitude"],
                    "longitude": ancillary_data["longitude"],
                    "temperature": ancillary_data["temperature"],
                    "oxygen": ancillary_data["oxygen"],
                }
                logger.info(f"queuing loc: {new_loc} {predictor.md['dive']} {loc_datetime}")
                redis_queue.hset(f"locs:{predictor.md['video_reference_uuid']}", str(self.num_loaded), json.dumps(new_loc))
                logger.info(f"{predictor.source.name} found total possible {self.num_loaded} localizations")
                self.num_loaded += 1
