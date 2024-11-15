# aipipeline, Apache-2.0 license
# Filename: projects/bio/model/api.py
# Description: Base class for FastAPI models

import logging
import time
from datetime import datetime
from typing import List

import numpy as np
import requests

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

class FastAPIYV5:

    def __init__(self, endpoint_url: str):
        """
        FastAPI model class for YOLOv5
        :param endpoint_url: Endpoint for the FastAPI app, e.g. 'localhost:3000/predict_to_json'
        """
        # Make sure there is a / at the end of the path for handling file uploads
        if not endpoint_url.endswith('/'):
            endpoint = endpoint_url + '/'
        logger.info(f'Initializing FastAPIBaseModel with endpoint: {endpoint_url}')
        self.endpoint_url = endpoint

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
            FastAPI model class for VSS
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

