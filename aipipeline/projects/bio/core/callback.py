# aipipeline, Apache-2.0 license
# Filename: projects/bio/core/callback.py
# Description: Custom callback for bio projects
import json
import logging
from datetime import datetime, timedelta

from projects.bio.core.bioutils import get_ancillary_data, get_video_metadata

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
        """ Check if any tracks are closed and queue the localizations in REDIS"""
        skip_load, redis_queue, version_id, config_dict, predictor, tracks = batch
        if skip_load:
            return
        closed_tracks = [t for t in tracks if t.is_closed()]

        if len(closed_tracks) > 0:
            start_datetime = datetime.fromisoformat(predictor.md["start_timestamp"])
            config_dict = config_dict

            for track in closed_tracks:
                logger.info(f"Closed track {track.id}")
                best_frame, best_pt, best_label, best_box, best_score = track.get_best(False)
                best_time_secs = float(best_frame * predictor.frame_stride / predictor.source.frame_rate)
                logger.info(f"Best track {track.id} is {best_pt},{best_box},{best_label},{best_score} in frame {best_frame}")

                loc_datetime = start_datetime + timedelta(seconds=best_time_secs)
                ancillary_data = get_ancillary_data(predictor.md['dive'], config_dict, loc_datetime)

                if ancillary_data is None or "depthMeters" not in ancillary_data:
                    logger.error(f"Failed to get ancillary data for {predictor.md['dive']} {start_datetime}")
                    continue

                new_loc = {
                    "x1": float(max(best_box[0], 0.0)),
                    "y1": float(max(best_box[1], 0.0)),
                    "x2": float(best_box[2]),
                    "y2": float(best_box[3]),
                    "width": int(predictor.source.width),
                    "height": int(predictor.source.height),
                    "frame": int(best_frame * predictor.frame_stride),
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
                json.dumps(new_loc)
                redis_queue.hset(f"locs:{predictor.md['video_reference_uuid']}", str(self.num_loaded), json.dumps(new_loc))
                logger.info(f"{predictor.source.name} found total possible {self.num_loaded} localizations")
                self.num_loaded += 1
