from typing import List

import cv2
import requests
import io
import logging
from collections import Counter
from pathlib import Path

logger = logging.getLogger(__name__)


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


def process_video(out_path: Path, video_path: Path, target_labels: List[str], vss_threshold = 0.8):
    top_n = 3 # Number of top predictions to return
    url_vs = f"http://doris.shore.mbari.org:8000/knn/{top_n}/902111-CFE"
    cap = cv2.VideoCapture(video_path.as_posix())
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_number = 0
    
    out_csv = out_path / 'csv' / f"{video_path.stem}_blob_vss.csv"
    out_crop_base = out_path / 'crop'

    with out_csv.open("w") as f:
        f.write("image_path,class,score,area,saliency,x,y,xx,xy,w,h,cluster,image_width,image_height,crop_path,frame\n")

        while cap.isOpened():
            ret, frame = cap.read()

            if frame_number >= total_frames:
                return

            if not ret:
                logger.error(f"Error reading frame at {frame_number} frame")
                break

            # Run basic blob detection on the frame which is in grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Threshold the image to create a binary mask of pixels > 180
            _, mask = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Find contours in the binary mask
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            filtered_contours = [cnt for cnt in contours if cv2.contourArea(cnt) < 150000 and cv2.contourArea(cnt) > 300]

            # skip if no contours found or too many contours
            if len(filtered_contours) == 0:
                logger.error(f"No contours found for {frame_number} on {video_path}")
                continue

            if len(filtered_contours) > 50:
                logger.error(f"Too many contours found for {frame_number} on {video_path}")
                continue

            for i, contour in enumerate(filtered_contours):
                x, y, w, h = cv2.boundingRect(contour)

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
                cropped_frame = frame[y:y + h, x:x + w]

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

                crop_file = out_crop_base / f"{video_path.stem}_blob_{frame_number}.jpg"

                cv2.imwrite(crop_file.as_posix(), cropped_frame)

                files = []
                # Read the image as a byte array
                with open(crop_file, "rb") as file:
                    img = file.read()
                    bytes_io = io.BytesIO(img)
                    files.append(("files", (crop_file.as_posix(), bytes_io.getvalue())))

                response = requests.post(url_vs, headers={"accept": "application/json"}, files=files)
                logger.debug(f"Response: {response.status_code}")

                if response.status_code != 200:
                    logger.error(f"Error processing images: {response.text}")
                    crop_file.unlink()
                    exit(1)

                predictions = response.json()["predictions"]
                scores = response.json()["scores"]
                # Scores are  1 - score, so we need to invert them
                score = [[1 - float(x) for x in y] for y in scores]
                logger.debug(f"Predictions: {predictions}")
                logger.debug(f"Scores: {scores}")

                best_pred, best_score = top_majority(predictions, score[0], threshold=vss_threshold, majority_count=-1)

                if best_pred is None:
                    crop_file.unlink()
                    logger.error(f"No majority prediction for {frame_number} on {video_path}")
                    continue

                if best_score < vss_threshold or best_pred not in target_labels:
                    crop_file.unlink()
                    logger.error(
                        f"Score {best_score} below threshold {vss_threshold} or {best_pred} not in {target_labels} for {video_path} at {frame_number}")
                    continue

                # Write to  a simple CSV format. Most importantly, it includes the bounding box in
                # normalized coordinates and the image width and height. This should be useful for extracting images
                # for loading from the video. Note that we are not keeping the crop_file
                # image_path,class,score,area,saliency,x,y,xx,xy,w,h,cluster,image_width,image_height,crop_path,frame
                f.write(
                    f"{video_path}, {best_pred}, {best_score}, {w * h}, 0, {x}, {y}, {xx}, {xy}, {w}, {h}, -1, {frame_width}, {frame_height}, {crop_file}, {frame_number}\n")

            frame_number += 1

        cap.release()


if __name__ == "__main__":
    import os
    import time
    time_start = time.time()
    target_labels = ["copepod","rhizaria","particle_blur","larvacean","fecal_pellet","football","centric_diatom","gelatinous"]
    vss_threshold = 0.5
    file_path = Path(os.path.abspath(__file__))
    video_path = file_path.parent / 'data' / 'CFE_ISIIS-077-2024-01-26 13-14-40.686.mp4'
    out_path = Path.cwd() / 'output'
    (out_path / 'csv').mkdir(parents=True, exist_ok=True)
    (out_path / 'crop').mkdir(parents=True, exist_ok=True)
    process_video(out_path, video_path, target_labels, vss_threshold)
    time_end = time.time()
    logger.info(f"total processing time: {time_end - time_start}")
