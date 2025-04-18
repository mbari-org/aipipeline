# aipipeline, Apache-2.0 license
# Filename: projects/bio/core/video.py
# Description: Video wrapper to handle indexing and preprocessing video frames for bio projects

from pathlib import Path
import cv2
import numpy as np
import torch

class VideoSource:

    def __init__(self, video, **kwargs):
        self.video = video
        self.cap = None
        supported_ext = [".mp4", ".avi", ".mov"]
        if not Path(video).exists() or not Path(video).is_file():
            raise ValueError(f"Video file not found: {video}")
        if not Path(video).suffix in supported_ext:
            raise ValueError(f"Unsupported video format {video}")
        self.cap = cv2.VideoCapture(video)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frames = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.duration_secs = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT) / self.cap.get(cv2.CAP_PROP_FPS))
        self.batch_size = kwargs.get("batch_size", 1)
        self.stride = kwargs.get("stride", 4)
        device_id = kwargs.get("device_id", 0)
        self.device = torch.device(f"cuda:{device_id}" if torch.cuda.is_available() else "cpu")
        self.current_frame = 0
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.video_mount = kwargs.get("video_mount", None)

    def __del__(self):
        self.close()

    @property
    def size(self):
        return self.frame_width, self.frame_height

    @property
    def video_name(self):
        return Path(self.video).name

    @property
    def video_path(self):
        return Path(self.video)

    @property
    def video_url(self):
        if self.video_mount:
            url = self.video_path.as_uri()
            url = url.replace(self.video_mount["path"], self.video_mount["nginx_root"])
            url = url.replace('file://', f'https://{self.video_mount["host"]}')
            return url
        return self.video_path.as_uri()


    def preprocess(self, images):
        imgs = []
        for img in images:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            imgs.append(img)

        # Transpose to match PyTorch format: (channels, height, width)
        img = np.stack(imgs)
        img = img[..., ::-1].transpose((0, 3, 1, 2))
        img = np.ascontiguousarray(img)  # contiguous
        img = torch.from_numpy(img)
        img = img.float() / 255.0 # Normalize to [0, 1]
        return img


    def __iter__(self):
        return self

    def __next__(self):
        frames = []
        if self.batch_size == 1 and self.stride > 1:
            for _ in range(self.stride):
                ret, frame = self.cap.read()
                self.current_frame += 1
                if not ret:
                    raise StopIteration
            frames.append(frame)
        else:
            while len(frames) < self.batch_size:
                ret, frame = self.cap.read()
                if not ret:
                    raise StopIteration
                frames.append(frame)
                self.current_frame += 1
            if not frames:
                raise StopIteration
        return self.preprocess(frames)

    def close(self):
        if self.cap:
            self.cap.release()

    @property
    def frame(self):
        return self.current_frame

    @property
    def frame_rate(self):
        return self.fps

    @property
    def width(self):
        return self.frame_width

    @property
    def height(self):
        return self.frame_height
