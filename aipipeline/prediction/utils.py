# aipipeline, Apache-2.0 license
# Filename: prediction/utils.py
# Description: Utility functions for prediction pipelines

import logging
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import List

from PIL import Image
import pandas as pd

logger = logging.getLogger(__name__)

formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)
# and log to file
now = datetime.now()
log_filename = f"pred_utils_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


def crop_square_image(row: pd.Series, square_dim: int):
    """
    Crop the image to a square padding the shortest dimension, then resize it to square_dim x square_dim
    This also adjusts the crop to make sure the crop is fully in the frame, otherwise the crop that
    exceeds the frame is filled with black bars - these produce clusters of "edge" objects instead
    of the detection. Box coordinates are normalized between 0 and 1. Image dimensions are in pixels.
    :param row: dictionary with the following keys: image_path, crop_path, image_width, image_height, x, y, xx, xy
    :param square_dim: dimension of the square image
    :return:
    """
    try:
        if not Path(row.image_path).exists():
            logger.warning(f"Skipping {row.crop_path} because the image {row.image_path} does not exist")
            return

        if Path(row.crop_path).exists():  # If the crop already exists, skip it
            return

        x1 = int(row.image_width * row.x)
        y1 = int(row.image_height * row.y)
        x2 = int(row.image_width * row.xx)
        y2 = int(row.image_height * row.xy)
        width = x2 - x1
        height = y2 - y1
        shorter_side = min(height, width)
        longer_side = max(height, width)
        delta = abs(longer_side - shorter_side)

        # Divide the difference by 2 to determine how much padding is needed on each side
        padding = delta // 2

        # Add the padding to the shorter side of the image
        if width == shorter_side:
            x1 -= padding
            x2 += padding
        else:
            y1 -= padding
            y2 += padding

        # Make sure that the coordinates don't go outside the image
        # If they do, adjust by the overflow amount
        if y1 < 0:
            y1 = 0
            y2 += abs(y1)
            if y2 > row.image_height:
                y2 = row.image_height
        elif y2 > row.image_height:
            y2 = row.image_height
            y1 -= abs(y2 - row.image_height)
            if y1 < 0:
                y1 = 0
        if x1 < 0:
            x1 = 0
            x2 += abs(x1)
            if x2 > row.image_width:
                x2 = row.image_width
        elif x2 > row.image_width:
            x2 = row.image_width
            x1 -= abs(x2 - row.image_width)
            if x1 < 0:
                x1 = 0

        # Crop the image
        img = Image.open(row.image_path)
        img = img.crop((x1, y1, x2, y2))

        # Resize the image to square_dim x square_dim
        img = img.resize((square_dim, square_dim), Image.LANCZOS)

        # Save the image
        img.save(row.crop_path)
        img.close()

    except Exception as e:
        logger.exception(f"Error cropping {row.image_path} {e}")
        raise e


def max_score_p(model_predictions: List[str], model_scores: List[float]):
    """Find the top prediction"""
    max_score = 0.0

    for row in zip(model_predictions, model_scores):
        prediction, score = row
        score = float(score)
        if score > max_score:
            max_score = score
            best_pred = prediction

    return best_pred, max_score


def top_majority(model_predictions, model_scores, threshold: float, majority_count=-1):
    """Find the top prediction"""

    # Only keep predictions with scores above the threshold
    data = [(pred, score) for pred, score in zip(model_predictions, model_scores) if float(score) >= threshold]

    if len(data) == 0:
        return None, None

    p, s = zip(*data)
    model_predictions = list(p)
    model_scores = list(s)

    # Count occurrences of each prediction in the top lists
    counter = Counter(model_predictions)

    if majority_count == -1:
        majority_count = (len(model_predictions) // 2) + 1

    majority_predictions = [pred for pred, count in counter.items() if count >= majority_count]

    # If there are no majority predictions
    if len(majority_predictions) == 0:
        # Pick the prediction with the highest score
        # best_pred, max_score = max_score_p(model_predictions, model_scores)
        return None, None

    best_pred = majority_predictions[0]
    best_score = 0.0
    num_majority = 0
    # Sum all the scores for the majority predictions
    for pred, score in zip(model_predictions, model_scores):
        if pred in majority_predictions:
            best_score += float(score)
            num_majority += 1
    best_score /= num_majority

    return best_pred, best_score
