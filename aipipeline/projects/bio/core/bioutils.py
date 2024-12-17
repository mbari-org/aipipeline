# aipipeline, Apache-2.0 license
# Filename: projects/bio/core/bioutils.py
# Description: General utility functions for bio projects

import io
import json
import logging
import os
import random
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import List

import cv2
import torch
import requests
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
    for batch_idx, img in enumerate(batch):
        # Convert the Tensor to a numpy array
        img = img.cpu().numpy().transpose(1, 2, 0)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        for pred in predictions:
            if pred['batch_idx'] != batch_idx:
                continue
            x1, y1, x2, y2 = pred['x'], pred['y'], pred['x'] + pred['w'], pred['y'] + pred['h']
            # Scale the bounding box
            x1, y1, x2, y2 = int(x1 * scale_w), int(y1 * scale_h), int(x2 * scale_w), int(y2 * scale_h)
            # class_name = pred['class_name']
            # conf = pred['confidence']
            img = cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            # img = cv2.putText(img, f'{self.model.class_names[int(cls)]} {conf:.2f}', (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.imshow('frame', img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


def filter_blur_pred(images: torch.Tensor,
                     predictions: List[dict],
                     crop_path: Path,
                     image_width: int,
                     image_height: int):
    filtered_pred = []
    # TODO: get image width and height from the images tensor
    for p in predictions:
        loc = {
            "x": p["x"],
            "y": p["y"],
            "xx": p["x"] + p['w'],
            "xy": p["y"] + p['h'],
            "w": p['w'],
            "h": p['h'],
            "frame": p['frame'],
            "image_width": image_width,
            "image_height": image_height,
            "confidence": p['confidence'],
            "batch_idx": p['batch_idx'],
            "crop_path": (crop_path / f"{uuid.uuid5(uuid.NAMESPACE_DNS, str(p['x']) + str(p['y']) + str(p['w']) + str(p['h']))}.jpg").as_posix()
        }

        crop_square_image(images, loc, 224)

        # Return true the crop if it has a blurriness score of less than the threshold
        def detect_blur(image_path, threshold):
            image = cv2.imread(image_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            _, binary_image = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            _, max_val, _, _ = cv2.minMaxLoc(gray)
            laplacian_variance = laplacian.var()
            print(f"laplacian_variance: {laplacian_variance} for {image_path}")
            if laplacian_variance < threshold:
                return True
            return False

        if detect_blur(loc["crop_path"], 2.0):
            print(f"Detected blur in {loc['crop_path']}")
            os.remove(loc["crop_path"])
        else:
            filtered_pred.append(loc)

    return filtered_pred

