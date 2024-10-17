import json
import logging
import multiprocessing
import os
import shutil
import time
from datetime import datetime
import numpy as np
from pathlib import Path
from typing import Dict, List, Any

import cv2
import requests
import tator
from tator.openapi.tator_openapi import TatorApi

from aipipeline.docker.utils import run_docker
import apache_beam as beam
from albumentations.pytorch import ToTensorV2

from aipipeline.config_setup import CONFIG_KEY
from aipipeline.prediction.utils import top_majority

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.DEBUG)
# # and log to file
now = datetime.now()
log_filename = f"pred_lib_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

MULTIVIEW_SUFFIX = "view"


def remove_multicrop_views(data_dir: str):
    data_path = Path(data_dir)
    search = f"*{MULTIVIEW_SUFFIX}*.jpg"
    logger.info(f"Removing augmented data matching {search} in {data_dir}")
    for file in data_path.rglob(search):
        logger.info(f"Removing augmented {file}")
        file.unlink()


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


def generate_multicrop_views2(image) -> List[tuple]:
    data = []
    small_crop_augmentations = simclr_augmentations(image_size=190)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    multicrop = [small_crop_augmentations(image=image)['image'] for _ in range(2)]
    for i, crop in enumerate(multicrop):
        # Extract the augmented image and convert it back to BGR
        augmented_image = crop.numpy()
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        augmented_image = std[:, None, None] * augmented_image + mean[:, None, None]
        augmented_image = np.clip(augmented_image.transpose(1, 2, 0) * 255, 0, 255).astype(np.uint8)
        augmented_image = cv2.cvtColor(augmented_image, cv2.COLOR_RGB2BGR)
        data.append(augmented_image)
    return data


def generate_multicrop_views(elements) -> List[tuple]:
    data = []
    small_crop_augmentations = simclr_augmentations(image_size=224)
    for count, crop_path, save_path in elements:
        if count > 100:
            logger.info(f"Skipping {count} crops in {crop_path}")
            data.append((count, crop_path, save_path))
            continue

        logger.info(f"Augmenting {count} crops in {crop_path}....")
        num_aug = 0
        for image_path in Path(crop_path).glob("*.jpg"):
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
                save_file = image_path.parent / f"{image_path.stem}{MULTIVIEW_SUFFIX}{i}.jpg"
                logger.info(f"Saving {save_file}")
                cv2.imwrite(save_file.as_posix(), augmented_image)
                num_aug += 1
        data.append((num_aug, crop_path, save_path))
    return data


def cluster(data, config_dict: Dict) -> List[tuple]:
    logger.info(f'Clustering {data}')
    num_images, crop_dir, cluster_dir = data
    project = config_dict["tator"]["project"]
    sdcat_config = config_dict["sdcat"]["ini"]
    cluster_results = []
    tmp_config = Path('/tmp') / project / sdcat_config
    if not tmp_config.exists():
        logger.error(f"Cannot find {tmp_config}. Did the config_setup run successfully?")
        return []
    short_name = get_short_name(project)
    logger.info(data)

    logger.info(f"Clustering {num_images} images in {crop_dir} ....")
    min_cluster_size = 2

    logger.info(f"Running clustering on {num_images} images with min-cluster-size=2")
    args = [
        "cluster",
        "roi",
        "--skip-visualization",
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
            image=config_dict["docker"]["sdcat"],
            name=f"{short_name}-sdcat-clu-{machine_friendly_label}",
            args_list=args,
            bind_volumes=config_dict["docker"]["bind_volumes"],
        )
        if container:
            logger.info(f"Clustering {label}....")
            container.wait()
            logger.info(f"Done clustering {label}....")
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
        if len(batch) > 1:
            num_processes = min(1, len(batch))
        else:
            num_processes = 1
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


def crop_rois_voc(labels: List[str], config_dict: Dict, processed_dir: str = None, image_dir: str = None) -> List[tuple]:
    project = config_dict["tator"]["project"]
    short_name = get_short_name(project)
    if processed_dir is None:
        processed_data = config_dict["data"]["processed_path"]
    else:
        processed_data = processed_dir
    base_path = os.path.join(processed_data, config_dict["data"]["version"])
    if image_dir is None:
        image_dir = (Path(base_path) / "images").as_posix()
    args = [
        "-d",
        f"{base_path}/voc",
        "--image_dir",
        f"{image_dir}",
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
                image=config_dict["docker"]["voccropper"],
                name=f"{short_name}-voccrop-{now}",
                args_list=args,
                bind_volumes=config_dict["docker"]["bind_volumes"]
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
    stats_file = Path(f"{base_path}/crops/stats.json")
    if not stats_file.exists():
        logger.error(f"Cannot find {stats_file}. Did voc-cropper run successfully?")
        return []

    data = []
    with stats_file.open("r") as f:
        stats = json.load(f)
        logger.info(f"Found stats: {stats}")
        total_labels = stats["total_labels"]
        labels = list(total_labels.keys())
        logger.info(f"Found labels: {labels}")
        for label, count in total_labels.items():
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


def download(labels: List[str], conf_files: Dict, config_dict: Dict, additional_args: List[str] = [],
             download_dir: str = None) -> List[
    str]:
    TATOR_TOKEN = os.getenv("TATOR_TOKEN")
    if download_dir is None:
        processed_data = config_dict["data"]["processed_path"]
    else:
        processed_data = download_dir
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
        conf_files[CONFIG_KEY],
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
        image=config_dict["docker"]["aidata"],
        name=f"{short_name}-download-{now}",
        args_list=args,
        bind_volumes=config_dict["docker"]["bind_volumes"]
    )
    if container:
        container.wait()
        logger.info(f"Done downloading data for labels: {labels}....")
    else:
        logger.error(f"Failed to download data for labels: {labels}....")

    return labels


def run_vss(image_batch: List[tuple[np.array,str]], config_dict: dict, top_k: int = 3):
    """
    Run vector similarity
    :param image_batch: batch of images path/binary tuples to process, maximum of 3 as supported by the inference
    :param config_dict: dictionary of config for vss server
    :param top_k: number of vss to use for prediction; 1, 3, 5 etc.
    :return:
    """
    logger.info(f"Processing {len(image_batch)} images")
    project = config_dict["tator"]["project"]
    vss_threshold = float(config_dict["vss"]["threshold"])
    url_vs = f"{config_dict['vss']['url']}/{top_k}/{project}"
    logger.debug(f"URL: {url_vs} threshold: {vss_threshold}")
    files = []
    for img, path in image_batch:
        files.append(("files", (path, img)))

    logger.info(f"Processing {len(files)} images with {url_vs}")
    response = requests.post(url_vs, headers={"accept": "application/json"}, files=files)
    logger.debug(f"Response: {response.status_code}")

    if response.status_code != 200:
        logger.error(f"Error processing images: {response.text}")
        return [f"Error processing images: {response.text}"]

    predictions = response.json()["predictions"]
    scores = response.json()["scores"]
    # Scores are  1 - score, so we need to invert them
    scores = [[1 - float(x) for x in y] for y in scores]
    logger.debug(f"Predictions: {predictions}")
    logger.debug(f"Scores: {scores}")

    if len(predictions) == 0:
        img_failed = [x[0] for x in image_batch]
        return [f"No predictions found for {img_failed} images"]

    # Workaround for bogus prediction output - put the predictions in a list
    # top_k predictions per image
    batch_size = len(image_batch)
    predictions = [predictions[i:i + top_k] for i in range(0, batch_size * top_k, top_k)]
    file_paths = [x[1][0] for x in files]
    best_predictions = []
    best_scores = []
    for i, element in enumerate(zip(scores, predictions)):
        score, pred = element
        score = [float(x) for x in score]
        logger.info(f"Prediction: {pred} with score {score} for image {file_paths[i]}")
        best_pred, best_score = top_majority(pred, score, threshold=vss_threshold, majority_count=-1)
        best_predictions.append(best_pred)
        best_scores.append(best_score)
        logger.info(f"Best prediction: {best_pred} with score {best_score} for image {file_paths[i]}")

    return file_paths, best_predictions, best_scores


def get_box_type(api: TatorApi, project_id: int) -> Any | None:
    types = api.get_localization_type_list(project=project_id)
    for t in types:
        if t.name == 'Box':
            return t
    return None


def init_api_project(host: str, token: str, project_name: str) -> tuple[Any, int]:
    """
    Fetch the Tator API and project
    :param host: hostname, e.g. localhost
    :param token: api token
    :param project_name:  project name
    :return: Tator API and project id
    """
    try:
        logger.info(f"Connecting to Tator at {host}")
        api = tator.get_api(host, token)
    except Exception as e:
        raise e

    logger.info(f"Searching for project {project_name} on {host}.")
    projects = api.get_project_list()
    logger.info(f"Found {len(projects)} projects")
    project = None
    for p in projects:
        if p.name == project_name:
            project = p
            break
    if project is None:
        raise Exception(f"Could not find project {project_name}")

    logger.info(f"Found project {project.name} with id {project.id}")
    if project is None:
        raise Exception(f"Could not find project {project}")

    return api, project.id

