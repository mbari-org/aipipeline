# Utility to read in all ROIS and pad using the long side of each ROI and color the background the median
import argparse
import cv2
from pathlib import Path
import numpy as np

def pad_and_rescale(input_path: Path, output_path: Path):
    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)

    for roi_file in input_path.rglob("*.png"):
        roi = cv2.imread(str(roi_file),cv2.IMREAD_GRAYSCALE)
        h, w = roi.shape
        max_dim = max(h, w)
        pad_h = (max_dim - h) // 2
        pad_w = (max_dim - w) // 2

        border_pixels = np.hstack([
            roi[0, :], roi[-1, :],
            roi[:, 0], roi[:, -1]
        ])
        bg_color = int(np.median(border_pixels))

        # Pad the ROI black, rescale and save
        roi_padded = cv2.copyMakeBorder(roi, pad_h, pad_h, pad_w, pad_w, cv2.BORDER_CONSTANT, value=bg_color)
        roi_padded_rescaled = cv2.resize(roi_padded, (224, 224))
        cv2.imwrite(str(output_path / roi_file.name), roi_padded_rescaled)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pad and rescale ROIs to square format.")
    parser.add_argument("--input_dir", type=Path, help="Path to the input directory containing ROI rois.")
    parser.add_argument("--output_dir", type=Path, help="Path to the output directory where processed rois will be saved.")
    args = parser.parse_args()

    pad_and_rescale(args.input_dir, args.output_dir)