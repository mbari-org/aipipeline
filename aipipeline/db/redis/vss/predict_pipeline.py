# aipipeline, Apache-2.0 license
# Filename: aipipeline/prediction/predict_pipeline.py
# Description: Batch process images with vector search server VSS
import csv

import apache_beam as beam
import cv2
import numpy as np
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.io.fileio import MatchFiles, ReadMatches
import io
import logging
import os
from datetime import datetime
from pathlib import Path
import dotenv

from aipipeline.config_args import parse_override_args
from aipipeline.config_setup import setup_config
from aipipeline.prediction.library import run_vss

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# and log to file
now = datetime.now()
log_filename = f"vss_predict_save_pipeline_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Secrets
dotenv.load_dotenv()
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")


def read_image(readable_file):
    """
    Read an image from a readable file and return the bytes and file path.
    """
    with readable_file.open() as file:
        img = io.BytesIO(file.read()).getvalue()
        return img, readable_file.metadata.path

def read_image_pad(readable_file):
    """
    Read an image from a readable file, pad it to square, resize to 224x224, and return the bytes.
    This improves compatibility/performance with VSS models that expect square images.
    """
    with readable_file.open() as file:
        img_bytes = file.read()

    # Convert bytes to NumPy array and decode image
    np_arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError(f"Unable to decode image from {readable_file.metadata.path}")

    # Pad image to square
    h, w, _ = img.shape
    max_dim = max(h, w)
    pad_h = (max_dim - h) // 2
    pad_w = (max_dim - w) // 2
    img_padded = cv2.copyMakeBorder(img, pad_h, pad_h, pad_w, pad_w, cv2.BORDER_CONSTANT, value=[0, 0, 0])

    # Resize to 224x224
    img_resized = cv2.resize(img_padded, (224, 224))

    # Encode back to bytes
    _, img_encoded = cv2.imencode(".jpg", img_resized)
    img_final_bytes = img_encoded.tobytes()

    return img_final_bytes, readable_file.metadata.path

class ProcessVSSBatch(beam.DoFn):
    def process(self, batch, config_dict):
        """
        Process a batch of images
        """
        try:
            logger.debug(f"Processing batch of {len(batch)} images")
            results = run_vss(batch, config_dict, top_k=3)
            if results is None:
                logger.error("No results returned from VSS")
                return
            yield results
        except Exception as ex:
            logger.error(f"Error processing batch: {ex}")

def run_pipeline(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Process images with VSS abd save results to a CSV file")
    default_project = (
        Path(__file__).resolve().parent.parent.parent
        / "aipipeline"
        / "projects"
        / "uav"
        / "config"
        / "config.yml"
    )
    parser.add_argument("--input", required=True,
        help="Input image directory, e.g. /mnt/UAV/machineLearning/Unknown/Baseline/crops/Unknown/",
    )
    parser.add_argument("--config", required=False, default=default_project.as_posix(),
                        help="Config yaml file path")
    parser.add_argument("--batch-size", required=False, type=int, default=64, help="Batch size")
    parser.add_argument("--max-images", required=False, type=int, help="Maximum number of images to process")
    parser.add_argument("--resize", action='store_true', help="Resize images to 224x224 and pad to square")
    args, other_args = parser.parse_known_args(argv)
    options = PipelineOptions(other_args)
    conf_files, config_dict = setup_config(args.config, silent=True)
    config_dict = parse_override_args(config_dict, other_args)

    with beam.Pipeline(options=options) as p:
        image_pcoll = (
                p
                | "MatchFiles" >> MatchFiles(file_pattern=f"{args.input}*.jpg")
        )

        # Apply the limit conditionally
        if args.max_images:
            image_pcoll = (
                    image_pcoll
                    | 'Limit Matches' >> beam.combiners.Sample.FixedSizeGlobally(int(args.max_images))
                    | "FlattenMatches" >> beam.FlatMap(lambda x: x)
            )

        (
                image_pcoll
                | "ReadFiles" >> ReadMatches()
                | "ReadImages" >> beam.Map(read_image_pad if args.resize else read_image)
                | "BatchImages" >> beam.BatchElements(min_batch_size=args.batch_size, max_batch_size=args.batch_size)
                | "ProcessBatches" >> beam.ParDo(ProcessVSSBatch(), config_dict)
                | "LogResults" >> beam.Map(logger.info)
        )


if __name__ == "__main__":
    run_pipeline()
