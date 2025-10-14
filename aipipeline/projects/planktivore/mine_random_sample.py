# Pick a random sample of images from a listing of .txt files containing image paths, one per line and copy them to a new directory
import os
import random
from pathlib import Path
import shutil
from tqdm import tqdm
import argparse
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)
now = datetime.now()

log_filename = f"mine_random_sample{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

def mine_random_sample(input_path, output_path, sample_size=1000, exclude_file=None):
    if exclude_file and os.path.exists(exclude_file):
        with open(exclude_file, "r") as f:
            exclude_paths = set(line.strip() for line in f.readlines())
        logger.info(f"Excluding {len(exclude_paths)} image paths from {exclude_file}")
    else:
        exclude_paths = set()
    all_image_paths = []
    for txt_file in Path(input_path).glob("*.txt"):
        with open(txt_file, "r") as f:
            lines = f.readlines()
            # Exclude paths in the exclude list
            lines = [line for line in lines if line.strip() not in exclude_paths]
            all_image_paths.extend([line.strip() for line in lines if line.strip().endswith(('.jpg', '.png'))])

    logger.info(f"Found {len(all_image_paths)} image paths in {input_path}")

    if len(all_image_paths) == 0:
        logger.warning("No image paths found. Exiting.")
        return

    sample_size = min(sample_size, len(all_image_paths))
    sampled_image_paths = random.sample(all_image_paths, sample_size)

    os.makedirs(output_path, exist_ok=True)

    for img_path in tqdm(sampled_image_paths, desc="Copying images"):
        try:
            shutil.copy(img_path, output_path)
        except Exception as e:
            logger.error(f"Error copying {img_path} to {output_path}: {e}")

    logger.info(f"Copied {len(sampled_image_paths)} images to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mine random sample of images from text files.")
    parser.add_argument(
        "--input_path",
        type=str,
        help="Path to the directory containing .txt files with image paths"
    )
    parser.add_argument(
        "--output_path",
        type=str,
        required=True,
        help="Path to the directory where sampled images will be copied"
    )
    parser.add_argument(
        "--sample_size",
        type=int,
        default=1000,
        help="Number of random images to sample"
    )
    parser.add_argument(
        "exclude",
        type=str,
        default="/u/dcline/Dropbox/code/ai/aipipeline/aipipeline/projects/planktivore-lm/tator_data_section_aidata-export-03-low-mag.csv"
    )
    args = parser.parse_args()

    mine_random_sample(args.input_path, args.output_path, args.sample_size, args.exclude)


