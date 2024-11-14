# aipipeline, Apache-2.0 license
# Filename: aipiipeline/prediction/vss-_init_pipeline.py
# Description: Run the VSS initialization pipeline
import time
from datetime import datetime

import dotenv
import os
from pathlib import Path
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from typing import Dict
import logging

from aipipeline.docker.utils import run_docker
from aipipeline.config_setup import extract_labels_config, setup_config, CONFIG_KEY
from aipipeline.prediction.library import (
    download,
    crop_rois_voc,
    generate_multicrop_views,
    get_short_name,
    gen_machine_friendly_label,
    clean,
    batch_elements,
    ProcessClusterBatch, remove_multicrop_views, clean_images,
)

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.DEBUG)
# and log to file
now = datetime.now()
log_filename = f"vss_init_pipeline_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Secrets
dotenv.load_dotenv()
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
TATOR_TOKEN = os.getenv("TATOR_TOKEN")


# Load exemplars into Vector Search Server
def load_exemplars(data, config_dict=Dict, conf_files=Dict) -> str:
    project = str(config_dict["tator"]["project"])
    short_name = get_short_name(project)

    logger.info(data)
    num_loaded = 0
    for label, save_dir in data:
        machine_friendly_label = gen_machine_friendly_label(label)
        # Grab the most recent file
        all_exemplars = list(Path(save_dir).rglob("*_exemplars.csv"))
        exemplar_file = sorted(all_exemplars, key=os.path.getmtime, reverse=True)[0] if all_exemplars else None

        # Grab the most recent detections file
        all_detections = list(Path(save_dir).rglob("*cluster_detections.csv"))
        detection_file = sorted(all_detections, key=os.path.getmtime, reverse=True)[0] if all_detections else None

        if exemplar_file is None:
            logger.info(f"No exemplar file found for {label}")
            exemplar_count = 0
        else:
            with open(exemplar_file, "r") as f:
                exemplar_count = len(f.readlines())
        if detection_file is None:
            logger.info(f"No detection file found for {label}")
            detection_count = 0
        else:
            with open(detection_file, "r") as f:
                detection_count = len(f.readlines())

        if exemplar_count == 0 or detection_count == 0:
            logger.info(f"No exemplars or detections found for {label}")
            continue

        if exemplar_count < 10 or detection_count < 100:
            logger.info(f"Too few exemplars, using detections file {detection_file} instead")
            exemplar_file = detection_file

        logger.info(f"Loading {exemplar_count} exemplars for {label} as {label} from {exemplar_file}")
        args = [
            "load",
            "exemplars",
            "--input",
            f"'{exemplar_file}'",
            "--label",
            f"'{label}'",
            "--device",
            "cuda:0",
            "--password",
            REDIS_PASSWORD,
            "--config",
            conf_files[CONFIG_KEY],
            "--token",
            TATOR_TOKEN,
        ]
        n = 3  # Number of retries
        delay_secs = 30  # Delay between retries

        for attempt in range(1, n + 1):
            try:
                container = run_docker(
                    image=str(config_dict["docker"]["aidata"]),
                    name=f"{short_name}-aidata-loadexemplar-{machine_friendly_label}",
                    args_list=args,
                    bind_volumes=dict(config_dict["docker"]["bind_volumes"]),
                )
                if container:
                    logger.info(f"Loading cluster exemplars for {label} from {exemplar_file}...")
                    container.wait()
                    logger.info(f"Loaded cluster exemplars for {label} from {exemplar_file}")
                    num_loaded += 1
                    break
                else:
                    logger.error(f"Failed to load cluster exemplars for {label}")
            except Exception as e:
                logger.error(f"Failed to load v exemplars for {label}: {e}")
                if attempt < n:
                    logger.info(f"Retrying in {delay_secs} seconds...")
                    time.sleep(delay_secs)
                else:
                    logger.error(f"All {n} attempts failed. Giving up.")
                    return f"Failed to load exemplars for {label}"

    return f"Loaded {num_loaded} labels"


# Beam pipeline
def run_pipeline(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Initialize the VSS database")
    example_project = Path(__file__).resolve().parent.parent / "projects" / "uav" / "config" / "config.yml"
    parser.add_argument("--config", required=True, help=f"Config file path, e.g. {example_project}")
    parser.add_argument("--skip-clean", required=False, default=False, help="Skip cleaning of previously downloaded data")
    parser.add_argument("--skip-download", required=False, default=False, help="Skip downloading data")
    parser.add_argument("--batch-size", required=False, type=int, default=2, help="Batch size")
    args, beam_args = parser.parse_known_args(argv)

    conf_files, config_dict = setup_config(args.config)
    batch_size = int(args.batch_size)
    download_args = config_dict["data"]["download_args"]
    processed_data = config_dict["data"]["processed_path"]
    base_path = str(os.path.join(processed_data, config_dict["data"]["version"]))
    labels = extract_labels_config(config_dict)

    options = PipelineOptions(beam_args)

    if not args.skip_clean:
        clean(base_path)

    # Always remove any previous augmented data before starting
    remove_multicrop_views(base_path)

    with beam.Pipeline(options=options) as p:
        start = (
            p
            | "Create labels" >> beam.Create([labels])
        )
        if not args.skip_download:
            start = (
                start
                | "Download labeled data" >> beam.Map(download, conf_files=conf_files, config_dict=config_dict, additional_args=download_args)
            )

        (
            start
            | "Crop ROI" >> beam.Map(crop_rois_voc, config_dict=config_dict)
            | "Generate views" >> beam.Map(generate_multicrop_views)
            | "Clean dark blurry examples" >> beam.Map(clean_images)
            | 'Batch cluster ROI elements' >> beam.FlatMap(lambda x: batch_elements(x, batch_size=batch_size))
            | 'Process cluster ROI batches' >> beam.ParDo(ProcessClusterBatch(config_dict=config_dict))
            | "Load exemplars" >> beam.Map(load_exemplars, config_dict=config_dict, conf_files=conf_files)
            | "Log results" >> beam.Map(logger.info)
        )


if __name__ == "__main__":
    run_pipeline()
