# aipipeline, Apache-2.0 license
# Filename: projects/bio/model/inference.py
# Description: Base class for detection models
import glob
import logging
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any

import numpy as np
import requests
from torch import Tensor
from ultralytics import YOLO
import torch
import yolov5
from PIL import Image
from io import BytesIO

from aipipeline.prediction.utils import top_majority

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)
# and log to file
now = datetime.now()
log_filename = f"bio_model_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

class YV5:
    def __init__(self, model_dir: str, device_num:int = 0):
        """
        Model class for YOLOv5
        :param model_dir: Directory containing the model .pt files
        """
        logger.info(f'Initializing YV5 with model_dir: {model_dir}')
        files = glob.glob(f"{model_dir}/*.pt")
        if len(files) == 0:
            logger.error(f"No .pt file found in {model_dir}")
            raise FileNotFoundError(f"No .pt file found in {model_dir}")
        weights = files[0]
        if torch.cuda.is_available():
            self.device = torch.device(f'cuda:{device_num}')
        else:
            self.device = torch.device('cpu')
        self.model = yolov5.load(weights)
        self.model.to(self.device)
        self.model.shape = (1280, 1280)
        self.model.conf = 0.01 # confidence threshold (0-1)
        self.model.max_det = 500  # maximum number of detections per image
        self.shape = (1280, 1280)  # resize to this shape
        self.last_frame = 0
        self.has_gpu = torch.cuda.is_available()
        self.device_id = device_num

    @property
    def class_names(self):
        return self.model.names

    @property
    def model_shape(self):
        return self.shape

    def yolo_to_corner_format(self, boxes):
        # boxes: Tensor of shape (N, 4) with (cx, cy, w, h)
        x1 = boxes[:, 0] - boxes[:, 2] / 2
        y1 = boxes[:, 1] - boxes[:, 3] / 2
        x2 = boxes[:, 0] + boxes[:, 2] / 2
        y2 = boxes[:, 1] + boxes[:, 3] / 2
        return torch.stack((x1, y1, x2, y2), dim=1)

    def predict_images(self, images: Tensor, min_score_det:float = 0.1) -> list[dict[str, int | float | str | Any]]:
        """
        Predicts on a batch of images.
        :param min_score_det:  Minimum score for a detection to be considered
        :param images: List of images
        :return: A list of detections for each image, where each detection is a list of dictionaries.
        """
        raw_detections = self.model(images, size=self.model_shape[0])
        threshold = 0.01  # 1% threshold
        iou_threshold = 0.5
        batch_size = raw_detections.shape[0]

        all_detections = []
        for batch_idx in range(batch_size):
            predictions = raw_detections[batch_idx]
            scores = predictions[:, 4]
            labels = predictions[:, 5]
            detections = predictions[scores > min_score_det]

            # Apply Non-Maximum Suppression (NMS)
            boxes = detections[:, :4]  # x1, y1, x2, y2
            correct_boxes = self.yolo_to_corner_format(boxes)
            scores = detections[:, 4] #* detections[:, 5]
            indices = torch.ops.torchvision.nms(correct_boxes, scores, iou_threshold)
            filtered_boxes = correct_boxes[indices]
            filtered_scores = scores[indices]
            filter_labels = labels[indices]
            names = self.model.detection_model.names

            for box, score, label in zip(filtered_boxes, filtered_scores, filter_labels):
                box = box.numpy()
                score = score.numpy()
                label_id = int(label)
                label = names[label_id]
                x1, y1, x2, y2 = box
                w = x2 - x1
                h = y2 - y1
                xx = x1 + w
                xy = y1 + h
                x = x1
                y = y1
                class_name = "marine organism" #label
                score = score.item()
                # Remove any detections in the corner of the frame or not in the allowed class names or below the confidence threshold
                x = x / self.model_shape[0]
                y = y / self.model_shape[1]
                xx = xx / self.model_shape[0]
                xy = xy / self.model_shape[1]
                w = w / self.model_shape[0]
                h = h / self.model_shape[1]
                if (
                        (0 <= x <= threshold or 1 - threshold <= x <= 1) or
                        (0 <= y <= threshold or 1 - threshold <= y <= 1) or
                        (0 <= xx <= threshold or 1 - threshold <= xx <= 1) or
                        (0 <= xy <= threshold or 1 - threshold <= xy <= 1)
                ):
                    continue
                all_detections.append({
                    "frame": self.last_frame,
                    "batch_idx": self.last_frame % batch_size,
                    "x": x,
                    "y": y,
                    "w": w,
                    "h": h,
                    "class_name": class_name,
                    "confidence": score
                })
            self.last_frame += 1

        return all_detections

class YV10:
    def __init__(self, model_dir: str):
        """
        Model class for YOLOv10
        :param model_dir: Directory containing the vits_model files
        """
        logger.info(f'Initializing YV10 with model_dir: {model_dir}')
        # Get the .pt file from the vits_model directory
        files = glob.glob(f"{model_dir}/*.pt")
        if len(files) == 0:
            logger.error(f"No .pt file found in {model_dir}")
            raise FileNotFoundError(f"No .pt file found in {model_dir}")
        model_file = files[0]
        # Load the YOLOv10 vits_model
        self.model = YOLO(model_file)  # Replace with the path to your YOLOv10 vits_model

    def predict_image(self, image) -> List[List[dict]]:
        data = self.model.predict(image)

        all_detections = []
        for loc in data:
            for bbox in loc.boxes:
                # Move the bounding box to the CPU and convert to numpy
                bbox = bbox.cpu()
                x, y, w, h = bbox.xywh.numpy().flatten()
                class_id = int(bbox.cls)
                class_name = loc.names[class_id]
                confidence = float(bbox.conf)
                all_detections.append({
                    "x": x,
                    "y": y,
                    "w": w,
                    "h": h,
                    "class_name": class_name,
                    "confidence": confidence
                })
        return all_detections

class FastAPIYV5:

    def __init__(self, endpoint_url: str):
        """
        FastAPI vits_model class for YOLOv5
        :param endpoint_url: Endpoint for the FastAPI app, e.g. 'localhost:3000/predict_to_json'
        """
        # Make sure there is a / at the end of the path for handling file uploads
        self.last_frame = 0
        endpoint = endpoint_url
        if not endpoint_url.endswith('/'):
            endpoint = endpoint_url + '/'
        logger.info(f'Initializing FastAPIYV5 with endpoint: {endpoint_url}')
        self.endpoint_url = endpoint

    def predict_images(self, images: List[np.array], confidence_threshold:float = .01) -> list[dict[str, float | Any]]:
        all_detections = []
        batch_size = len(images)
        # TODO: get image width and height from the images tensor
        image_height, image_width = 1280, 1280
        for image in images:
            for n_try in range(5):
                try:
                    logger.info(f"Sending frame to {self.endpoint_url}")
                    image_array = (image.cpu().numpy().transpose() * 255.0).astype(np.uint8)
                    image_buffer = Image.fromarray(image_array)
                    buffer = BytesIO()
                    image_buffer.save(buffer, format="JPEG")
                    buffer.seek(0)
                    files = {'file': ('image.jpg', buffer.getbuffer().tobytes(), 'image/jpeg')}
                    data = {'confidence_threshold': f'{confidence_threshold:.5f}'}
                    headers = {'accept': 'application/json'}
                    response = requests.post(self.endpoint_url, headers=headers, files=files, data=data)
                    logger.debug(response.text)
                    logger.info(f"resp: {response}")
                    if response.status_code == 200:
                        data = response.json()
                        logger.debug(data)
                        for loc in data:
                            all_detections.append({
                                "frame": self.last_frame,
                                "batch_idx": self.last_frame % batch_size,
                                "x": loc["y"] / image_width,
                                "y": loc["x"] / image_height,
                                "w": loc["height"] / image_width,
                                "h": loc["width"] / image_height,
                                "class_name": loc["class_name"],
                                "confidence": loc["confidence"]
                            })
                except Exception as e:
                    logger.exception(f'Error {e}')
                    # delay to avoid overloading the server
                    time.sleep(5)
                    continue
                self.last_frame += 1
        return all_detections

    def predict_bytes(self, image_bytes: bytes) -> dict:
        for n_try in range(5):
            try:
                logger.info(f"Sending frame to {self.endpoint_url}")
                response = requests.post(self.endpoint_url,files=[('file', image_bytes)])
                logger.debug(response.text)
                logger.info(f"resp: {response}")
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logger.exception(f'Error {e}')
                # delay to avoid overloading the server
                time.sleep(5)
                continue
        return None

class FastAPIVSS:

        def __init__(self, base_url: str, project: str, threshold: float, top_k: int = 3):
            """
            FastAPI vits_model class for VSS
            :param base_url: Endpoint for the FastAPI app, e.g. 'localhost:3000/predict_to_json'
            """
            # Make sure there is a / at the end of the path for handling file uploads
            if not base_url.endswith('/'):
                base_url = base_url + '/'
            self.endpoint_url = f"{base_url}{top_k}/{project}"
            self.threshold = threshold
            logger.info(f'Initializing FastAPIBaseModel with endpoint: {self.endpoint_url}')

        def predict(self, image_batch: List[tuple[np.array, str]], top_k: int = 3):
            """
            Run vector similarity
            :param image_batch: batch of images path/binary tuples to process, maximum of 3 as supported by the inference
            :return:
            """
            logger.info(f"Processing {len(image_batch)} images")
            logger.debug(f"URL: {self.endpoint_url} threshold: {self.threshold} top_k: {top_k}")
            files = []
            for img, path in image_batch:
                files.append(("files", (path, img)))

            # TODO: get image width and height from the images tensor
            # TODO: redo image from tensor to numpy array (see YV5 above)
            # TODO: normalize the results to 0-1
            logger.info(f"Processing {len(files)} images with {self.endpoint_url}")
            for n_try in range(5):
                try:
                    response = requests.post(self.endpoint_url, headers={"accept": "application/json"}, files=files)
                    logger.debug(f"Response: {response.status_code}")

                    if response.status_code != 200:
                        logger.error(f"Error processing images: {response.text}")
                    break
                except Exception as e:
                    logger.exception(f"Error processing images: {e}")
                    time.sleep(5)
                    continue

            predictions = response.json()["predictions"]
            scores = response.json()["scores"]
            # Scores are  1 - score, so we need to invert them
            scores = [[1 - float(x) for x in y] for y in scores]
            logger.debug(f"Predictions: {predictions}")
            logger.debug(f"Scores: {scores}")

            if len(predictions) == 0:
                img_failed = [x[0] for x in image_batch]
                return [f"No predictions found for {img_failed} images"]

            # Workaround for bogus prediction output - put the predictions in a list
            # top_k predictions per image
            batch_size = len(image_batch)
            predictions = [predictions[i:i + top_k] for i in range(0, batch_size * top_k, top_k)]
            file_paths = [x[1][0] for x in files]
            best_predictions = []
            best_scores = []
            for i, element in enumerate(zip(scores, predictions)):
                score, pred = element
                score = [float(x) for x in score]
                logger.info(f"Prediction: {pred} with score {score} for image {file_paths[i]}")
                best_pred, best_score = top_majority(pred, score, threshold=self.threshold, majority_count=-1)
                best_predictions.append(best_pred)
                best_scores.append(best_score)
                logger.info(f"Best prediction: {best_pred} with score {best_score} for image {file_paths[i]}")

            return file_paths, best_predictions, best_scores

