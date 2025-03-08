# Utility to read in all ROIS and pad using the long side of each ROI
import argparse
import cv2
import os
from pathlib import Path

def pad_and_rescale(input_path: Path, output_path: Path):
    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)

    for roi_file in input_path.rglob("*.png"):
        roi = cv2.imread(str(roi_file))
        h, w, _ = roi.shape
        max_dim = max(h, w)
        pad_h = (max_dim - h) // 2
        pad_w = (max_dim - w) // 2

        # Pad the ROI black, rescale and save
        roi_padded = cv2.copyMakeBorder(roi, pad_h, pad_h, pad_w, pad_w, cv2.BORDER_CONSTANT, value=[0, 0, 0])
        roi_padded_rescaled = cv2.resize(roi_padded, (224, 224))
        cv2.imwrite(str(output_path / roi_file.name), roi_padded_rescaled)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pad and rescale ROIs to square format.")
    parser.add_argument("input_dir", type=Path, help="Path to the input directory containing ROI images.")
    parser.add_argument("output_dir", type=Path, help="Path to the output directory where processed images will be saved.")
    args = parser.parse_args()

    pad_and_rescale(args.input_dir, args.output_dir)