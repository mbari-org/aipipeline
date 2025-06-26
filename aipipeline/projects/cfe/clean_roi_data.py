# Simple script to clean bad images from a large CSV file in parallel.
# Removes blurry, near-duplicates images(keeping least blurry)
# but only for images in the lower 80% of the area
import numpy as np
import logging
import os
import pandas as pd
import tempfile

from typing import List
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from cleanvision import Imagelab
from multiprocessing import cpu_count
from tempfile import TemporaryDirectory

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CROP_COLUMN = "crop_path"  # column for image paths
AREA_COLUMN = "area"  # column for area values

def clean_bad_images(filepaths: List[str]) -> List[str]:
    """Remove blurry images and near-duplicates"""
    imagelab = Imagelab(filepaths=filepaths)

    imagelab._config = {
        "visualize_num_images_per_row": 4,
        "report_num_images": 4,
        "report_max_prevalence": 1.0,
        "report_cell_size": (2, 2),
    }

    issue_types = {
        "blurry": {"threshold": 0.52},
        "near_duplicates": {"hash_size": 4, "hash_types": ["whash", "phash"]},
    }

    imagelab.find_issues(issue_types)
    bad_images = []

    # Remove blurry images
    for issue_key in ["is_blurry_issue"]:
        issue_indices = imagelab.issues[imagelab.issues[issue_key]].index
        bad_images.extend(issue_indices)

    # Remove near-duplicates smaller than min_area
    dup_sets = imagelab.info["near_duplicates"]["sets"]
    blurry_scores = (
        imagelab.issues[imagelab.issues["is_near_duplicates_issue"]]
        .sort_values(by="blurry_score")
        .reset_index()[["index", "blurry_score"]]
        .values.tolist()
    )

    for dup_set in dup_sets:
        if len(dup_set) <= 1:
            continue
        # Find the best (sharpest) image in the set
        best = max((x for x in blurry_scores if x[0] in dup_set), key=lambda x: x[1], default=None)
        if best:
            for img in dup_set:
                if img == best[0]:
                    continue
                bad_images.append(img)

    return list(set(bad_images))


def process_chunk(chunk_df, chunk_idx, min_area, bad_image_log_dir):
    """
    Process a chunk of the DataFrame to identify and log bad images.

    :param chunk_df: DataFrame chunk to process.
    :type chunk_df: pandas.DataFrame
    :param chunk_idx: Index of the chunk.
    :type chunk_idx: int
    :param min_area: Minimum area threshold for filtering.
    :type min_area: int or float
    :param bad_image_log_dir: Directory to save bad image logs.
    :type bad_image_log_dir: str
    :return: Path to the log file containing bad image paths.
    :rtype: str
    """
    logger.info(f"Processing chunk {chunk_idx}")

    # Skip over any rows greater than min_area
    chunk_df = chunk_df[chunk_df[area_column] < min_area]
    filepaths = chunk_df[crop_column].tolist()
    bad_files = clean_bad_images(filepaths)

    bad_log_path = os.path.join(bad_image_log_dir, f"bad_images_chunk_{chunk_idx}.txt")
    with open(bad_log_path, "w") as f:
        for path in bad_files:
            f.write(f"{path}\n")

    return bad_log_path


def clean_csv_images_parallel(
        input_csv: str,
        output_csv: str,
        min_area: int,
        chunk_size: int = 50000,
        max_workers: int = 4,
):

    """
    Clean a CSV file of bad images in parallel by processing in chunks.

    :param input_csv: Path to the input CSV file.
    :type input_csv: str
    :param output_csv: Path to the output cleaned CSV file.
    :type output_csv: str
    :param min_area: Minimum area threshold for filtering images.
    :type min_area: int
    :param chunk_size: Number of rows per chunk (default: 50000).
    :type chunk_size: int, optional
    :param max_workers: Maximum number of parallel workers (default: 4).
    :type max_workers: int, optional"""

    bad_image_log_dir = os.path.splitext(output_csv)[0] + "_bad_logs"
    os.makedirs(bad_image_log_dir, exist_ok=True)

    reader = pd.read_csv(input_csv, chunksize=chunk_size)
    chunks = [(chunk, idx, min_area, bad_image_log_dir) for idx, chunk in enumerate(reader)]

    bad_log_files = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_chunk, *args) for args in chunks]
        for f in futures:
            bad_log_files.append(f.result())

    logger.info("All chunks processed. Compiling results...")

    # Open all bad image logs and remove them from the final DataFrame
    bad_images = set()
    for log_file in bad_log_files:
        with open(log_file, "r") as f:
            bad_images.update(line.strip() for line in f)

    logger.info(f"Found {len(bad_images)} bad images across all chunks.")

    # Read the input CSV again to filter out bad images
    df = pd.read_csv(input_csv)
    initial_row_count = len(df)
    df = df[~df[CROP_COLUMN].isin(bad_images)]
    final_row_count = len(df)
    logger.info(f"Removed {initial_row_count - final_row_count} bad images from the CSV.")
    df.to_csv(output_csv, index=False)
    logger.info(f"Saved cleaned CSV to {output_csv}")
    logger.info(f"Bad image logs saved to {bad_image_log_dir}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Clean bad images from large CSV in parallel.")
    parser.add_argument("input_csv", help="Path to input CSV", type=Path)
    parser.add_argument("output_csv", help="Path to output CSV", type=Path)
    parser.add_argument("--chunk-size", type=int, default=50000, help="Rows per chunk (default: 50000)")
    parser.add_argument("--workers", type=int, default=5, help="Max threads (default: number of CPUs)")

    args = parser.parse_args()

    csv_path = Path(args.input_csv)

    # First calculate the area cutoff
    temp_dir = os.getenv("TMPDIR", tempfile.gettempdir())
    with TemporaryDirectory(dir=temp_dir) as tmp_dir:
        df_combined = pd.read_csv(args.input_csv)
        logger.info(f"Loaded combined CSV with {len(df_combined)} rows.")

        percentile_80 = np.percentile(df_combined['area'], 80)
        logger.info(f"80% of the area values are below: {percentile_80}")

    # Now clean the CSV images in parallel
    clean_csv_images_parallel(
        input_csv=csv_path,
        output_csv=args.output_csv,
        min_area=int(percentile_80),
        chunk_size=args.chunk_size,
        max_workers=args.workers,
    )