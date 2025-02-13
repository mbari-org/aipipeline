# aipipeline, Apache-2.0 license
# Filename: projects/bio/core/bioutils.py
# Description: General utility functions for bio projects
import hashlib
import cv2
import torch
import requests
import io
import json
import logging
import os
import random
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from aipipeline.docker.utils import run_docker
from aipipeline.prediction.utils import crop_square_image

logger = logging.getLogger(__name__)


def get_ancillary_data(dive: str, config_dict: dict, iso_datetime: any) -> dict:
    try:
        # Create a random index for the container name
        index = random.randint(0, 1000)
        platform = dive.split(' ')[:-1]  # remove the last element which is the dive number
        platform = ''.join(platform)
        if isinstance(iso_datetime, str):
            iso_datetime = datetime.fromisoformat(iso_datetime)
        else:
            iso_datetime = iso_datetime
        container = run_docker(
            image=config_dict["docker"]["expd"],
            name=f"expd-{platform}-{iso_datetime:%Y%m%dT%H%M%S%f}-{index}",
            args_list=[platform, iso_datetime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')],
            auto_remove=False,
        )
        if container:
            container.wait()
            # get the output string and convert to a dictionary
            output = container.logs().decode("utf-8")
            data = json.loads(output)
            container.remove()
            return data
        else:
            container.remove()
            logger.error(f"Failed to capture expd data....")
    except Exception as e:
        logger.error(f"Failed to capture expd data....{e}")


def get_video_metadata(video_name):
    """
    Get video metadata from the VAM rest API
    """
    try:
        # Check if the metadata is cached
        cache_file = f"/tmp/{video_name}.json"
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                return json.load(f)
        query = f"http://m3.shore.mbari.org/vam/v1/media/videoreference/filename/{video_name}"
        logger.info(f"query: {query}")
        # Get the video reference uuid from the rest query JSON response
        response = requests.get(query)
        logger.info(f"response: {response}")
        data = json.loads(response.text)[0]
        logger.info(f"data: {data}")
        metadata = {
            "uri": data["uri"],
            "video_reference_uuid": data["video_reference_uuid"],
            "start_timestamp": data["start_timestamp"],
            "mime": data["container"],
            "resolution": (data["width"], data["height"]),
            "size": data["size_bytes"],
            "num_frames": int(data["frame_rate"] * data["duration_millis"] / 1000),
            "frame_rate": data["frame_rate"],
            "dive": data["video_sequence_name"],
        }
        # Cache the metadata to /tmp
        with open(cache_file, "w") as f:
            json.dump(metadata, f)
        return metadata
    except Exception as e:
        print("Error:", e)
        return None


def read_image(file_path: str) -> tuple[bytes, str]:
    with open(file_path, 'rb') as file:
        img = io.BytesIO(file.read()).getvalue()
        return img, file_path


def resolve_video_path(video_path: Path) -> Path:
    # Resolve the video URI to a local path
    md = get_video_metadata(video_path.name)
    if md is None:
        logger.error(f"Failed to get video metadata for {video_path}")
        return None

    resolved_path = Path(f'/mnt/M3/mezzanine' + md['uri'].split('/mezzanine')[-1])
    return resolved_path


def video_to_frame(timestamp: str, video_path: Path, output_path: Path, ffmpeg_path: str = "/usr/bin/ffmpeg"):
    """
    Capture frame with the highest quality jpeg from video at a given time
    """
    command = [
        ffmpeg_path,
        "-loglevel",
        "panic",
        "-nostats",
        "-hide_banner",
        "-ss", timestamp,
        "-i", video_path.as_posix(),
        "-frames:v", "1",
        "-qmin", "1",
        "-q:v", "1",  # Best quality JPG
        "-y",
        output_path.as_posix(),
    ]

    logger.info(f"Running command: {' '.join(command)}")

    # Run the command in a subprocess
    try:
        subprocess.run(command, check=True)
        logger.info("Frames captured successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error occurred: {e}")


def seconds_to_timestamp(seconds):
    # Convert timestamp to hour:minute:second format
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds_ = seconds % 60
    # If the seconds is not an integer, round to the nearest millisecond and format as seconds
    if seconds_ % 1:
        timestamp = f"{seconds:.3f}"
    else:
        timestamp = f"{int(hours):02}:{int(minutes):02}:{int(seconds_):02}"
    return timestamp


def show_boxes(batch, predictions):
    scale_w, scale_h = 1280, 1280
    for frame, img in enumerate(batch):
        # Convert the Tensor to a numpy array
        img = img.cpu().numpy().transpose(1, 2, 0)
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)

        for pred in predictions:
            if pred['frame'] != frame:
                continue
            x1, y1, x2, y2 = pred['x'], pred['y'], pred['x'] + pred['w'], pred['y'] + pred['h']
            # Scale the bounding box
            x1, y1, x2, y2 = int(x1 * scale_w), int(y1 * scale_h), int(x2 * scale_w), int(y2 * scale_h)
            # class_name = pred['class_name']
            # conf = pred['confidence']
            img = cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            # img = cv2.putText(img, f'{self.model.class_names[int(cls)]} {conf:.2f}', (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.imshow('frame', img)
        if cv2.waitKey(500) & 0xFF == ord('q'):
            break


def detect_blur(image_path: str, threshold: float) -> bool:
    """Detect if an image is blurry."""
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    laplacian_variance = laplacian.var()
    logger.info(f"laplacian_variance: {laplacian_variance} for {image_path}")
    return laplacian_variance < threshold


def crop_and_detect_blur(preds: List[Dict],
                         image: torch.Tensor,
                         crop_path: Path,
                         image_width: int,
                         image_height: int) ->  List[Dict]:
    """Crop image and detect blur for detections in an image."""
    locs = []

    for pred in preds:
        # Generate a unique name for the crop
        crop_name = hashlib.md5(f"{pred['x']}_{pred['y']}_{pred['w']}_{pred['h']}".encode()).hexdigest()
        crop_file_path = (crop_path / f"{crop_name}.jpg").as_posix()

        loc = {
            "x": pred["x"],
            "y": pred["y"],
            "xx": pred["x"] + pred['w'],
            "xy": pred["y"] + pred['h'],
            "w": pred['w'],
            "h": pred['h'],
            "frame": pred['frame'],
            "image_width": image_width,
            "image_height": image_height,
            "confidence": pred['confidence'],
            "crop_path": crop_file_path
        }

        # Crop the image
        crop_square_image(image, loc, 224)

        # Check for blurriness
        if detect_blur(crop_file_path, 2.0):
            logger.info(f"Detected blur in {crop_file_path}")
            os.remove(crop_file_path)
        else:
            locs.append(loc)
    return locs

def filter_blur_pred(images: torch.Tensor,
                     predictions: List[dict],
                     crop_path: Path,
                     image_width: int,
                     image_height: int) -> List[Dict]:
    """Filter predictions by detecting blur in crops."""
    if len(predictions) == 0:
        return []

    num_images = images.size(0)
    pred_by_image = {i: [p for p in predictions if p['frame'] == i] for i in range(num_images)}
    filtered_pred = [crop_and_detect_blur(pred_by_image[i], images[i], crop_path, image_width, image_height) for i in range(num_images)]
    filtered_pred = [loc for locs in filtered_pred for loc in locs]
    return filtered_pred
