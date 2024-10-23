import uuid
from datetime import datetime
from typing import List

import cv2
import requests
import io
import logging
from collections import Counter
from pathlib import Path

from aipipeline.prediction.utils import compute_saliency, compute_saliency_threshold_map, process_contour_blobs

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)
# and log to file
now = datetime.now()
log_filename = f"mine_isiis_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


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

    # If there are no majority predictions, return None
    if len(majority_predictions) == 0:
        # We could, alternatively, pick the prediction with the highest score which would look like
        # best_pred, max_score = max_score_p(model_predictions, model_scores)
        return None, None

    best_pred = majority_predictions[0]
    best_score = 0.0
    # Sum all the scores for the majority predictions
    for pred, score in zip(model_predictions, model_scores):
        if pred in majority_predictions:
            best_score += float(score)
    best_score /= len(model_predictions)

    return best_pred, best_score


def process_frame(out_path: Path, frame_path: Path, target_labels: List[str], vss_threshold=0.8):
    top_n = 3  # Number of top predictions to return
    url_vs = f"http://doris.shore.mbari.org:8000/knn/{top_n}/902111-CFE"
    # Get the frame width and height
    image = cv2.imread(frame_path.as_posix())
    if image is None:
        logger.error(f"Error reading image {frame_path}")
        return
    frame_width = image.shape[1]
    frame_height = image.shape[0]
    min_std = 4.0

    out_csv = out_path / 'csv' / f"{frame_path.stem}_blob_vss.csv"
    out_crop_base = out_path / 'crop'

    with out_csv.open("w") as f:
        f.write("image_path,class,score,area,saliency,x,y,xx,xy,w,h,cluster,image_width,image_height,crop_path\n")

        saliency_map = compute_saliency(image) # Compute the saliency map
        saliency_map_thres_c = compute_saliency_threshold_map(33, saliency_map)
        img_lum = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)[:, :, 0]
        df_blob = process_contour_blobs(min_std, saliency_map_thres_c, img_lum)

        # If no blobs are found, cannot assign saliency cost
        if df_blob.empty:
            return

        # remove any contours that have a saliency of 1000 or less
        df_blob = df_blob[df_blob.saliency > 1000]

        # skip if no contours found or too many contours
        if len(df_blob) == 0:
            logger.error(f"No contours found for {frame_path}")
            return

        logger.info(f"Found {len(df_blob)} blobs for {frame_path}")

        if len(df_blob) > 50:
            logger.error(f"Too many contours found for {frame_path}")
            return

        for idx, row in df_blob.iterrows():
            x, y, w, h = row.x, row.y, row.xx, row.xy
            saliency = row.saliency
            area = row.area
            logger.info(f"Processing blob {idx} at {x}, {y}, {w}, {h} with saliency {saliency}")

            # Crop the box, keeping the longest side
            width = w
            height = h
            shorter_side = min(height, width)
            longer_side = max(height, width)
            delta = abs(longer_side - shorter_side)
            padding = delta // 2
            if width == shorter_side:
                x -= padding
                w += padding
            else:
                y -= padding
                h += padding
            cropped_frame = image[y:y + h, x:x + w]

            # Normalize the bounding box
            x /= frame_width
            y /= frame_height
            xx = (x + w) / frame_width
            xy = (y + h) / frame_height

            # Resize to 224x224, which is the input size for the model
            try:
                cropped_frame = cv2.resize(cropped_frame, (224, 224))
            except Exception as e:
                logger.error(f"Error resizing image: {e}")
                continue

            # Create a unique ID based on the bounding box coordinates
            crop_file = out_crop_base / f"{frame_path.stem}_blob_{uuid.uuid5(uuid.NAMESPACE_DNS, str(row['x']) + str(row['y']) + str(row['xx']) + str(row['xy']))}.png.jpg"

            cv2.imwrite(crop_file.as_posix(), cropped_frame)

            files = []
            # Read the image as a byte array
            with open(crop_file, "rb") as file:
                img = file.read()
                bytes_io = io.BytesIO(img)
                files.append(("files", (crop_file.as_posix(), bytes_io.getvalue())))

            response = requests.post(url_vs, headers={"accept": "application/json"}, files=files)
            logger.debug(f"Response: {response.status_code}")
            crop_file.unlink()

            if response.status_code != 200:
                logger.error(f"Error processing images: {response.text}")
                exit(1)

            predictions = response.json()["predictions"]
            scores = response.json()["scores"]
            # Scores are  1 - score, so we need to invert them
            score = [[1 - float(x) for x in y] for y in scores]
            logger.debug(f"Predictions: {predictions}")
            logger.debug(f"Scores: {scores}")

            best_pred, best_score = top_majority(predictions, score[0], threshold=vss_threshold, majority_count=-1)

            if best_pred is None:
                logger.error(f"No majority prediction for {frame_path}")
                continue

            if best_score < vss_threshold or best_pred not in target_labels:
                logger.error(
                    f"Score {best_score} below threshold {vss_threshold} or {best_pred} not in {target_labels} for {frame_path}")
                continue

            # Write to  a simple CSV format. Most importantly, it includes the bounding box in
            # normalized coordinates and the image width and height. Note that we are not keeping the crop_file
            # image_path,class,score,area,saliency,x,y,xx,xy,w,h,cluster,image_width,image_height,crop_path,frame
            logger.info(f"Found {best_pred} with score {best_score} for {frame_path} ")
            f.write(
                f"{frame_path.as_posix()}, {best_pred}, {best_score}, {area}, {saliency}, {x}, {y}, {xx}, {xy}, {w}, {h}, -1, {frame_width}, {frame_height}, {crop_file}\n")



if __name__ == "__main__":
    import multiprocessing
    import time

    vss_threshold = 0.1  # Threshold for the VSS model
    time_start = time.time()
    target_labels = ["copepod", "rhizaria", "particle_blur",
                     "larvacean", "fecal_pellet", "football",
                     "centric_diatom", "gelatinous"]
    image_path = Path('/mnt/CFE/Data_archive/Images/ISIIS/COOK/Videos2framesdepth/')

    num_processes = multiprocessing.cpu_count()
    logger.info(f"Number of processes: {num_processes}")
    out_path = Path.cwd() / 'output'
    (out_path / 'csv').mkdir(parents=True, exist_ok=True)
    (out_path / 'crop').mkdir(parents=True, exist_ok=True)

    with multiprocessing.Pool(processes=num_processes) as pool:
        # Only process the m.jpg files which have the depth information computed
        for image in image_path.rglob("*m.jpg"):
            image_file = Path(image_path) / image
            out_path = Path.cwd() / 'output'
            pool.apply_async(process_frame, args=(out_path, image_file, target_labels, vss_threshold))
        pool.close()
        pool.join()

    time_end = time.time()
    logger.info(f"total processing time: {time_end - time_start}")
