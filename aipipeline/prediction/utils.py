# aipipeline, Apache-2.0 license
# Filename: prediction/utils.py
# Description: Utility functions for prediction pipelines

import logging
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np
import piexif
from PIL import Image
import pandas as pd
import xml.etree.ElementTree as ET

from pandas import DataFrame

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


def parse_voc_xml(xml_file) -> tuple[
    list[str | None], list[list[int]], list[str | None], list[str | None], list[str | None]]:
    """
    Parse a VOC XML file and return the bounding boxes, labels, poses, and ids
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()

    boxes = []
    labels = []
    poses = []
    ids = []
    paths = []

    image_size = root.find('size')
    image_width = int(image_size.find('width').text)
    image_height = int(image_size.find('height').text)
    path = root.find('path').text

    for obj in root.findall('object'):
        label = obj.find('name').text
        pose = obj.find('pose').text if obj.find('pose') is not None else "Unspecified"
        id = obj.find('id').text if obj.find('id') is not None else ""
        bbox = obj.find('bndbox')
        xmin = int(bbox.find('xmin').text)
        ymin = int(bbox.find('ymin').text)
        xmax = int(bbox.find('xmax').text)
        ymax = int(bbox.find('ymax').text)

        # Make sure to bound the coordinates are within the image
        if xmin < 0:
            xmin = 0
        if ymin < 0:
            ymin = 0
        if xmax < 0:
            xmax = 0
        if ymax < 0:
            ymax = 0
        if xmax > image_width:
            xmax = image_width
        if ymax > image_height:
            ymax = image_height

        paths.append(path)
        boxes.append([xmin, ymin, xmax, ymax])
        labels.append(label)
        poses.append(pose)
        ids.append(id)

    return paths, boxes, labels, poses, ids


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

        # Encode the cropped coordinates in the exif data
        bounding_box = f"{x1},{y1},{x2},{y2}"
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}}
        exif_dict["Exif"][piexif.ExifIFD.UserComment] = f"bbox:{bounding_box}".encode("utf-8")
        exif_bytes = piexif.dump(exif_dict)
        img.save(row.crop_path, exif=exif_bytes)
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


def compute_saliency(image) -> np.ndarray:
    img_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    img_lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

    # Blur the saturation channel to remove noise
    img_hsv[:, :, 1] = cv2.GaussianBlur(img_hsv[:, :, 1], (15, 15), 0)

    filtered_lum = img_lab[:, :, 0]
    filtered_saturation = img_hsv[:, :, 1]

    img_sl = cv2.merge((filtered_saturation, filtered_lum))

    # Initialize an empty saliency map
    saliency_map = np.zeros_like(image[:, :, 0], dtype=np.float32)

    blurred_saturation = cv2.GaussianBlur(img_sl[:, :, 1], (5, 5), 0)
    blurred_lum = cv2.GaussianBlur(img_sl[:, :, 1], (5, 5), 0)

    # Calculate the center and surround regions for each channel
    center_lum = cv2.GaussianBlur(blurred_lum, (3, 3), 2)
    surround_lum = blurred_lum - center_lum

    center_saturation = cv2.GaussianBlur(blurred_saturation, (3, 3), 2)
    surround_saturation = blurred_saturation - center_saturation

    # Normalize the values to the range [0, 255]
    center_lum = cv2.normalize(center_lum, None, 0, 255, cv2.NORM_MINMAX)
    surround_lum = cv2.normalize(surround_lum, None, 0, 255, cv2.NORM_MINMAX)

    center_saturation = cv2.normalize(center_saturation, None, 0, 255, cv2.NORM_MINMAX)
    surround_saturation = cv2.normalize(surround_saturation, None, 0, 255, cv2.NORM_MINMAX)

    # Combine the center and surround regions for each channel
    # Reduce the weight of the saturation channel
    saliency_lum = 1.2 * (center_lum - surround_lum)
    saliency_saturation = (center_saturation - surround_saturation) / 4

    # Combine the saliency maps into the final saliency map
    saliency_level = (saliency_saturation + saliency_lum) / 2

    # Resize the saliency map to the original image size
    saliency_level = cv2.resize(saliency_level, (image.shape[1], image.shape[0]))

    # Accumulate the saliency map at each level
    saliency_map += saliency_level

    # Normalize the final saliency map
    saliency_map = cv2.normalize(saliency_map, None, 0, 255, cv2.NORM_MINMAX)

    # Blur the saliency map to remove noise
    saliency_map = cv2.GaussianBlur(saliency_map, (15, 15), 0)

    return saliency_map


def compute_saliency_contour(contour, min_std: float, img_saliency: np.ndarray, img_luminance: np.ndarray) -> int:
    """
    Calculate the saliency cost of a contour. Lower saliency contours are more likely to be difficult to identify or
    bad for training.
    :param contour: the contour
    :param min_std: minimum standard deviation of the contour to be considered
    :param img_saliency: saliency image
    :param img_luminance: luminance image
    :return: saliency cost (int)
    """
    # Calculate brightness and other statistics of the contour
    mask = np.zeros_like(img_saliency)
    cv2.drawContours(mask, [contour], 0, 255, thickness=cv2.FILLED)
    mean_intensity_l = cv2.mean(img_luminance, mask=mask)[0]
    mean_intensity_s = cv2.mean(img_saliency, mask=mask)[0]

    # Calculate area of the contour
    area = cv2.contourArea(contour)

    # Calculate variance of pixel intensities within the contour
    x, y, w, h = cv2.boundingRect(contour)
    roi = img_luminance[y:y + h, x:x + w]
    variance = np.var(roi)
    std = np.std(roi)

    # Create a factor to normalize the cost for different image sizes
    factor = img_luminance.size / 10000

    # The cost function penalizes smaller areas with low variance
    cost = (area * (mean_intensity_l + mean_intensity_s + 0.1 * area) - variance) / factor

    # If cost is NaN, set it to 1
    if np.isnan(cost):
        cost = 1

    # If the std is too low, then the contour is not interesting; set the cost to 1
    if std < min_std:
        cost = 1

    return int(cost)


def compute_saliency_threshold_map(block_size: int, saliency_map: np.ndarray) -> np.ndarray:
    """
    Base function to extract blobs from a saliency map
    :param block_size: block size for adaptive thresholding
    :param saliency_map: normalized saliency map
    :return: pandas dataframe of blobs, image with contours drawn
    """

    # Blur the saliency map to remove noise
    saliency_map = cv2.GaussianBlur(saliency_map, (15, 15), 0)

    # Threshold the saliency map using gradient thresholding
    saliency_map_thres_c = cv2.adaptiveThreshold(
        saliency_map.astype(np.uint8),
        255,  # Max pixel value
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        block_size,  # Block size (size of the local neighborhood)
        3  # Constant subtracted from the mean
    )

    # Invert the saliency map so that the salient regions are white
    saliency_map_thres_c = cv2.bitwise_not(saliency_map_thres_c)

    # Connect blobs by dilating then eroding them
    # For images > 3000 pixels, use a 9x9 kernel, otherwise use a 5x5 kernel
    width, height = saliency_map_thres_c.shape
    logger.info(f'Saliency map image size: {width} x {height}')
    if width > 3000 or height > 3000:
        kernel1 = np.ones((5, 5), np.uint8)
        kernel2 = np.ones((3, 3), np.uint8)
        saliency_map_thres_c = cv2.dilate(saliency_map_thres_c, kernel1, iterations=4)
        saliency_map_thres_c = cv2.erode(saliency_map_thres_c, kernel2, iterations=4)
    else:
        kernel1 = np.ones((4, 4), np.uint8)
        kernel2 = np.ones((3, 3), np.uint8)
        saliency_map_thres_c = cv2.dilate(saliency_map_thres_c, kernel1, iterations=1)
        saliency_map_thres_c = cv2.erode(saliency_map_thres_c, kernel2, iterations=1)

    return saliency_map_thres_c


def process_contour_box(x: int, y: int, xx: int, xy: int, min_std: float, saliency_map_thres_c: np.ndarray,
                        img_lum: np.ndarray) \
        -> (pd.DataFrame, np.ndarray):
    """
    Base function to extract blobs from a saliency map
    :param min_std:
    :param saliency_map_thres_c:
    :param img_lum:
    :return:
    """
    # Create a contour around the box
    contour = np.array([[x, y], [x, xy], [xx, xy], [xx, y]])
    return process_contour([contour], min_std, saliency_map_thres_c.astype(np.uint8), img_lum)


def process_contour_blobs(min_std: float, saliency_map_thres_c: np.ndarray, img_lum: np.ndarray) \
        -> (pd.DataFrame, np.ndarray):
    """
    Base function to extract blobs from a saliency map
    :param min_std: minimum standard deviation of the contour to be considered
    :param saliency_map_thres_c: threshold saliency map
    :param img_lum: luminance image
    :return: pandas dataframe of blobs, image with contours drawn
    """

    # Find the contours in the thresholded saliency map
    contours, _ = cv2.findContours(saliency_map_thres_c, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_L1)
    df = process_contour(contours, min_std, saliency_map_thres_c.astype(np.uint8), img_lum)
    return df


def process_contour(contours: np.ndarray, min_std: float, img_s: np.ndarray, img_l: np.ndarray) -> DataFrame:
    """
    Process a single contour. Save the results to a csv file.
    This is a separate function, so it can be run in parallel.
    :param contours:  List of contours
    :param min_std: minimum standard deviation of the contour to be considered
    :param img_s: Saliency image
    :param img_l: Luminance image
    :return: dataframe of blobs
    """
    df = pd.DataFrame()
    for i, c in enumerate(contours):
        x, y, w, h = cv2.boundingRect(c)

        area = cv2.contourArea(c)
        saliency = compute_saliency_contour(c, min_std, img_s, img_l)

        logger.debug(f'Found blob area: {area}, saliency: {saliency}, area: {area}')
        df = pd.concat([df, pd.DataFrame({
            'class': 'Unknown',
            'score': 0.,
            'area': area,
            'saliency': saliency,
            'x': x,
            'y': y,
            'xx': x + w,
            'xy': y + h,
            'w': w,
            'h': h,
        }, index=[i])])

    return df
