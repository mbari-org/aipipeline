import io
import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path

import requests
from aipipeline.docker.utils import run_docker

logger = logging.getLogger(__name__)


def get_ancillary_data(dive: str, config_dict: dict, iso_datetime: datetime) -> dict:
    try:
        platform = dive.split(' ')[:-1]  # remove the last element which is the dive number
        platform = ''.join(platform)
        container = run_docker(
            image=config_dict["docker"]["expd"],
            name=f"expd-{platform}-{iso_datetime:%Y%m%dT%H%M%S%f}",
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
        import pdb; pdb.set_trace()
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


def video_to_frame(timestamp: str, video_path: Path, output_path: Path):
    """
    Capture frame with the highest quality jpeg from video at a given time
    """
    command = [
        "/opt/homebrew/bin/ffmpeg",
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