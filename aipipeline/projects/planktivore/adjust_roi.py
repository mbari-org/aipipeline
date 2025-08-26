# Utility to read in all ROIS and pad using the long side of each ROI
# Preserve parent directory structure
import argparse
import cv2
from pathlib import Path
import multiprocessing as mp
import os

def process_roi(roi_file, output_path):
    roi = cv2.imread(str(roi_file))

    if roi is None:
        print(f"Warning: Unable to read {roi_file}")
        return

    h, w, _ = roi.shape
    max_dim = max(h, w)
    pad_h = (max_dim - h) // 2
    pad_w = (max_dim - w) // 2

    # Preserve only immediate parent directory
    parent_dir = roi_file.parent.name
    output_file = output_path / parent_dir / roi_file.name
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Pad the ROI black, rescale, and save
    roi_padded = cv2.copyMakeBorder(roi, pad_h, pad_h, pad_w, pad_w, cv2.BORDER_CONSTANT, value=[0, 0, 0])
    roi_padded_rescaled = cv2.resize(roi_padded, (224, 224))
    cv2.imwrite(str(output_file), roi_padded_rescaled)


def pad_and_rescale(input_path: Path, output_path: Path):
    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)

    roi_files = list(input_path.rglob("*.png"))
    roi_files += list(input_path.rglob("*.jpg"))

    num_workers = max(1, os.cpu_count() - 1)  # Use all but one CPU core

    with mp.Pool(processes=num_workers) as pool:
        pool.starmap(process_roi, [(roi_file, output_path) for roi_file in roi_files])

    return output_path.as_posix()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pad and rescale ROIs to square format.")
    parser.add_argument("--input_dir", type=Path, required=True, help="Path to the input directory containing ROI images.")
    parser.add_argument("--output_dir", type=Path, required=True, help="Path to the output directory where processed images will be saved.")
    args = parser.parse_args()

    pad_and_rescale(args.input_dir, args.output_dir)