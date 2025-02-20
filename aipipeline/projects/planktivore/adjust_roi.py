# Utility to read in all ROIS and pad using the long side of each ROI

import cv2
import os
from pathlib import Path


def pad_and_rescale(input_path:Path, output_path:Path):
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    for roi_file in input_path.rglob("*.png"):

        roi = cv2.imread(roi_file.as_posix())
        h, w, _ = roi.shape
        max_dim = max(h, w)
        pad_h = (max_dim - h) // 2
        pad_w = (max_dim - w) // 2

        # Pad the ROI black, rescale and save
        roi_padded = cv2.copyMakeBorder(roi, pad_h, pad_h, pad_w, pad_w, cv2.BORDER_CONSTANT, value=[0, 0, 0])
        roi_padded_rescaled = cv2.resize(roi_padded, (224, 224))
        cv2.imwrite(output_path / roi_file.name, roi_padded_rescaled)


if __name__ == "__main__":
    dataset = ["aidata-export-02", "aidata-export-03-low-mag"]
    for d in dataset:
        input_dir = Path(f"/mnt/DeepSea-AI/data/Planktivore/raw/{d}")
        output_dir = Path(f"/mnt/ML_SCRATCH/Planktivore/{d}-square")
        pad_and_rescale(input_dir, output_dir)