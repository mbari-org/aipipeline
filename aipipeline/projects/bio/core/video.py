# aipipeline, Apache-2.0 license
# Filename: projects/bio/core/video.py
# Description: Video wrapper to handle indexing and preprocessing video frames for bio projects

from pathlib import Path
import cv2
import numpy as np
import torch

class VideoSource:

    def __init__(self, video, batch_size:int, device_id: int = 0, det_size=(1280, 1280), track_size=(640,480), **kwargs):
        self.video = video
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
        self.batch_size = batch_size
        self.stride = kwargs.get("stride", 4)
        self.det_size = det_size
        self.track_size = track_size
        self.device = torch.device(f"cuda:{device_id}" if torch.cuda.is_available() else "cpu")
        self.current_frame = 0
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.image_stack = []

    def __del__(self):
        self.close()

    @property
    def name(self):
        return Path(self.video).name

    @property
    def video_path(self):
        return self.video

    def preprocess(self, images):
        imgs = []
        imgs_classify = []
        for img in images:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img_det = cv2.resize(img, self.det_size)
            imgs.append(img_det)
            imgs_classify.append(img)

        # Transpose to match PyTorch format: (channels, height, width)
        img = np.stack(imgs)
        img = img[..., ::-1].transpose((0, 3, 1, 2))
        img = np.ascontiguousarray(img)  # contiguous
        img = torch.from_numpy(img)
        img = img.float() / 255.0 # Normalize to [0, 1]
        self.image_stack = img

        imgs_classify = np.stack(imgs_classify)
        imgs_classify = imgs_classify[..., ::-1].transpose((0, 3, 1, 2))
        imgs_classify = np.ascontiguousarray(imgs_classify)  # contiguous
        imgs_classify = torch.from_numpy(imgs_classify)
        imgs_classify = imgs_classify.float() / 255.0 # Normalize to [0, 1]
        return img, imgs_classify

    def __iter__(self):
        return self

    def __next__(self):
        frames = []
        batch_cnt = 0
        while batch_cnt < self.batch_size: #or self.current_frame >= self.frame_count:
            ret, frame = self.cap.read()
            if not ret:
                raise StopIteration
            if self.current_frame % self.stride == 0 and self.current_frame > 0:
                frames.append(frame)
                batch_cnt += 1
            self.current_frame += 1
        if not frames:
            raise StopIteration
        return self.preprocess(frames)

    def frame_stack(self):
        # Convert the images back to numpy array from a contiguous tensor
        img = (self.image_stack * 255.0).byte()  # Denormalize and convert to uint8
        img = img.cpu().numpy()  # Convert to NumPy array
        img = img.transpose(0, 2, 3, 1)[..., ::-1]  # Reverse transpose and channel order (BGR to RGB)
        return img

    def close(self):
        self.cap.release()

    @property
    def duration(self):
        return self.duration_secs

    @property
    def frame_rate(self):
        return self.fps

    @property
    def width(self):
        return self.frame_width

    @property
    def height(self):
        return self.frame_height
