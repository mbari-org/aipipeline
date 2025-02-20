# Utility to read in all ROIS and pad using the long side of each ROI

import cv2
import os
from pathlib import Path

input_dir = Path("/mnt/DeepSea-AI/data/Planktivore/raw/aidata-export-02")
output_dir = Path("/mnt/ML_SCRATCH/Planktivore/aidata-export-02-square")

# Create output directory if it doesn't exist
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

for roi_file in input_dir.rglob("*.png"):

    roi = cv2.imread(roi_file.as_posix())
    h, w, _ = roi.shape
    max_dim = max(h, w)
    pad_h = (max_dim - h) // 2
    pad_w = (max_dim - w) // 2

    # Pad the ROI black, rescale and save
    roi_padded = cv2.copyMakeBorder(roi, pad_h, pad_h, pad_w, pad_w, cv2.BORDER_CONSTANT, value=[0, 0, 0])
    roi_padded_rescaled = cv2.resize(roi_padded, (224, 224))
    cv2.imwrite(output_dir / roi_file.name, roi_padded_rescaled)

