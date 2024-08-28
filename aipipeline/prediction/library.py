import json
import logging
import multiprocessing
import os
import shutil
import time
from datetime import datetime
import numpy as np
from pathlib import Path
from typing import Dict, List

import cv2

from aipipeline.docker.utils import run_docker
import apache_beam as beam
from albumentations.pytorch import ToTensorV2

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)
# # and log to file
now = datetime.now()
log_filename = f"library-{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


def simclr_augmentations(image_size):
    import albumentations as albu
    return albu.Compose([
        albu.RandomResizedCrop(height=image_size, width=image_size, scale=(0.2, 1.0), p=1.0),
        albu.HorizontalFlip(p=0.5),
        albu.ColorJitter(brightness=0.4, contrast=0.4, saturation=0.4, hue=0.1, p=0.8),
        albu.GaussianBlur(blur_limit=(3, 7), sigma_limit=0.1, p=0.5),
        albu.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        ToTensorV2()
    ])


def generate_multicrop_views(elements) -> List[tuple]:
    data = []
    small_crop_augmentations = simclr_augmentations(image_size=112)
    for count, crop_path, save_path in elements:
        if count > 100:
            logger.info(f"Skipping {count} crops in {crop_path}")
            data.append((count, crop_path, save_path))
            continue

        logger.info(f"Augmenting {count} crops in {crop_path}....")
        for image_path in Path(crop_path).glob("*.jpg"):
            num_aug = 0
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Failed to read {image_path}")
                continue

            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            small_crops = [small_crop_augmentations(image=image)['image'] for _ in range(6)]
            multicrop = small_crops
            for i, crop in enumerate(multicrop):
                # Extract the augmented image and convert it back to BGR
                augmented_image = crop.numpy()
                mean = np.array([0.485, 0.456, 0.406])
                std = np.array([0.229, 0.224, 0.225])
                augmented_image = std[:, None, None] * augmented_image + mean[:, None, None]
                augmented_image = np.clip(augmented_image.transpose(1, 2, 0) * 255, 0, 255).astype(np.uint8)
                augmented_image = cv2.cvtColor(augmented_image, cv2.COLOR_RGB2BGR)

                # Save the augmented image using the same name as the original image with an index
                # This avoids overwriting the original image and allows the loader to still use the database index stem
                save_file = image_path.parent / f"{image_path.stem}.{i}.jpg"
                logger.info(f"Saving {save_file}")
                cv2.imwrite(save_file.as_posix(), augmented_image)
            num_aug += 1
        data.append((num_aug, crop_path, save_path))
    return data


def cluster(data, config_dict: Dict) -> List[tuple]:
    logger.info(data)
    logger.info(config_dict)
    num_images, crop_dir, cluster_dir = data
    project = config_dict["tator"]["project"]
    sdcat_config = config_dict["sdcat"]["clu_det_ini"]
    cluster_results = []
    tmp_config = Path('/tmp') / project / sdcat_config
    if not tmp_config.exists():
        logger.error(f"Cannot find {tmp_config}. Did the config_setup run successfully?")
        return []
    short_name = get_short_name(project)
    logger.info(data)

    logger.info(f"Clustering {num_images} images in {crop_dir} ....")
    # Scale the min-cluster-size based on the number of images
    if num_images > 1000:
        min_cluster_size = 7
    elif num_images > 500:
        min_cluster_size = 4
    elif num_images > 100:
        min_cluster_size = 3
    else:
        min_cluster_size = 2

    logger.info(f"Running clustering on {num_images} images with min-cluster-size=2")
    args = [
        "cluster",
        "roi",
        "--config-ini",
        tmp_config.as_posix(),
        "--min-cluster-size",
        f"{min_cluster_size}",
        "--roi-dir",
        f"'{crop_dir}'",
        "--save-dir",
        f"'{cluster_dir}'",
        "--device",
        "cuda:0",
    ]
    label = Path(crop_dir).name
    machine_friendly_label = gen_machine_friendly_label(label)
    try:
        container = run_docker(
            config_dict["docker"]["sdcat"],
            f"{short_name}-sdcat-clu-{machine_friendly_label}",
            args,
            config_dict["docker"]["bind_volumes"],
        )
        if container:
            logger.info(f"Clustering {label}....")
            container.wait()
            logger.info(f"Done clustering for {label}....")
            if not Path(cluster_dir).exists():
                logger.error(f"Failed to cluster {label}")
                return []
            cluster_results.append((Path(crop_dir).name, cluster_dir))
        else:
            logger.error(f"Failed to cluster for {label}....")
    except Exception as e:
        logger.error(f"Failed to cluster for {label}....{e}")

    return cluster_results


class ProcessClusterBatch(beam.DoFn):

    def __init__(self, config_dict: Dict):
        self.config_dict = config_dict

    def process(self, batch):
        num_processes = min(1, len(batch))
        with multiprocessing.Pool(num_processes) as pool:
            args = [(data, self.config_dict) for data in batch]
            results = pool.starmap(cluster, args)
        return results


def batch_elements(elements, batch_size=3):
    batch = []
    for element in elements:
        batch.append(element)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def get_short_name(project: str) -> str:
    return project.split("_")[-1]


def gen_machine_friendly_label(label: str) -> str:
    label_machine_friendly = label.replace(" ", "_").lower()
    label_machine_friendly = label_machine_friendly.replace("(", "")
    label_machine_friendly = label_machine_friendly.replace(")", "")
    label_machine_friendly = label_machine_friendly.replace(",", "")
    label_machine_friendly = label_machine_friendly.replace(".", "")
    return label_machine_friendly


def crop_rois(labels: List[str], config_dict: Dict) -> List[tuple]:
    project = config_dict["tator"]["project"]
    short_name = get_short_name(project)
    processed_data = config_dict["data"]["processed_path"]
    base_path = os.path.join(processed_data, config_dict["data"]["version"])
    args = [
        "-d",
        f"{base_path}/voc",
        "--image_dir",
        f"{base_path}/images",
        "-o",
        f"{base_path}/crops",
        "--resize",
        "224x224",
    ]
    # This is not currently working. Need to fix this
    #
    # if labels != "all":
    #     labels_str = ",".join(labels)
    #     args.extend(["--labels", f'"{labels_str}"'])

    now = datetime.now().strftime("%Y%m%d")

    n = 3  # Number of retries
    delay_secs = 30  # Delay between retries

    for attempt in range(1, n + 1):
        try:
            container = run_docker(
                config_dict["docker"]["voccropper"], f"{short_name}-voccrop-{now}", args,
                config_dict["docker"]["bind_volumes"]
            )
            if container:
                logger.info(f"Cropping ROIs in {base_path}....")
                container.wait()
                logger.info(f"Done cropping ROIs in {base_path}....")
                break  # Exit loop if successful
            else:
                logger.error(f"Failed to crop ROIs in {base_path}....")
                return []
        except Exception as e:
            logger.error(f"Attempt {attempt}/{n}: Failed to crop ROIs in {base_path}....{e}")
            if attempt < n:
                logger.info(f"Retrying in {delay_secs} seconds...")
                time.sleep(delay_secs)
            else:
                logger.error(f"All {n} attempts failed. Giving up.")
                return []

    # Find the file stats.txt and read it as a json file
    stats_file = Path(f"{base_path}/crops/stats.txt")
    if not stats_file.exists():
        logger.error(f"Cannot find {stats_file}. Did voc-cropper run successfully?")
        return []

    data = []
    with stats_file.open("r") as f:
        stats = json.load(f)
        logger.info(f"Found stats: {stats}")
        total_concepts = stats["total_concepts"]
        labels = list(total_concepts.keys())
        logger.info(f"Found labels: {labels}")
        for label, count in total_concepts.items():
            if count == 0:
                logger.info(f"Skipping label {label} with 0 crops")
                continue
            logger.info(f"Found {count} crops for label {label}")
            # Total number of crops, and paths to crops and cluster output respectively
            data.append((count, f"{base_path}/crops/{label}", f"{base_path}/cluster/{label}"))
        logger.debug(data)
    return data


def clean(base_path: str) -> str:
    # Remove any existing data, except for downloaded images
    for f in Path(base_path).glob("*"):
        if f.is_dir() and f.name != "images":
            try:
                logger.info(f"Removing {f}")
                shutil.rmtree(f)
            except Exception as e:
                logger.error(f"Failed to remove {f}: {e}")
                return f"Failed to remove {f}: {e}"

    return f"Cleaned {base_path} but not images"


def download(labels: List[str], config_dict: Dict, additional_args: List[str] = []) -> List[str]:
    TATOR_TOKEN = os.getenv("TATOR_TOKEN")
    processed_data = config_dict["data"]["processed_path"]
    version = config_dict["data"]["version"]
    project = config_dict["tator"]["project"]
    short_name = get_short_name(project)
    args = [
        "download",
        "dataset",
        "--voc",
        "--token",
        TATOR_TOKEN,
        "--config",
        f"/tmp/{project}/config.yml",
        "--base-path",
        processed_data,
        "--version",
        version,
    ]
    args.extend(additional_args)
    if labels != "all":
        labels_str = ",".join(labels)
        args.extend(["--labels", f'"{labels_str}"'])
    else:
        labels = []

    now = datetime.now().strftime("%Y%m%d")
    logger.info(f"Downloading data for labels: {labels}....")
    container = run_docker(
        config_dict["docker"]["aidata"], f"{short_name}-vss-download-{now}", args, config_dict["docker"]["bind_volumes"]
    )
    if container:
        container.wait()
        logger.info(f"Done downloading data for labels: {labels}....")
    else:
        logger.error(f"Failed to download data for labels: {labels}....")

    return labels
