# aipipeline, Apache-2.0 license
# Filename: aipipeline/prediction/saliency.py
# Description: Calculate saliency scores for localizations
import logging
import os
from datetime import datetime
from pathlib import Path

import apache_beam as beam
import cv2
import dotenv
import xml.etree.ElementTree as ET
import tator
from tator.openapi.tator_openapi import TatorApi  # type: ignore
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.io.fileio import MatchFiles, ReadMatches
import json
from aipipeline.prediction.utils import parse_voc_xml
from aipipeline.config_setup import setup_config
from aipipeline.prediction.utils import compute_saliency, compute_saliency_threshold_map, process_contour_blobs, \
    process_contour_box

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# Also log to the console
console = logging.StreamHandler()
logger.addHandler(console)
logger.setLevel(logging.INFO)
# and log to file
now = datetime.now()
log_filename = f"saliency-pipeline_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Secrets
dotenv.load_dotenv()
TATOR_TOKEN = os.getenv("TATOR_TOKEN")


# Function to batch process files (read them, then process)
def process_xml_batch(filenames_batch, scale_percent, min_std, block_size):
    """
    Custom batch processing logic where filenames are passed.
    Each filename is read, and its XML content is processed.
    :param filenames_batch: list of filenames to process
    :param scale_percent: percentage to scale the image
    :param min_std: minimum standard deviation for the blobs
    :param block_size: block size for the thresholding
    """
    results = []
    # Process each XML file
    for xml_filename in filenames_batch:
        parsed_data = parse_voc_xml(xml_filename)
        best_match = compute_saliency_cost(parsed_data,
                                           scale_percent=scale_percent,
                                           min_std=min_std,
                                           block_size=block_size)
        output_json_filename = Path(f"{xml_filename}.json")
        with open(output_json_filename, "w") as f:
            f.write(json.dumps(best_match))
    return results


def read_xml(readable_file):
    return readable_file.metadata.path


def remove_low_saliency(voc_search_pattern: Path, min_saliency: int):
    # Remove VOC XML entries that are lower than a certain saliency score
    json_files = voc_search_pattern.parent.rglob('*.json')
    for json_file in json_files:
        with open(json_file, "r") as f:
            json_data = json.load(f)
            ids = json_data["ids"]
            if len(ids) == 0:
                continue
            xml_file = Path(f"{json_file.parent}/{json_file.stem}")
            best_saliency = json_data["best_saliency"]
            remove_indices = [i for i, saliency in enumerate(best_saliency) if saliency < min_saliency]
            # Remove the XML entries at the indices
            if remove_indices:
                with open(xml_file, "r") as f:
                    xml_data = f.read()
                    root = ET.fromstring(xml_data)
                    for i, obj in enumerate(root.findall('object')):
                        if i in remove_indices:
                            logger.info(f"Removing {obj} from {xml_file}")
                            root.remove(obj)
                # Write the new XML data
                with open(xml_file, "w") as f:
                    f.write(ET.tostring(root).decode())


def update_database(voc_path: Path, api: TatorApi, project_id: int, box_id: int):
    # Get all the JSON files in the directory
    json_files = voc_path.rglob('*.json')
    params = {"type": box_id}
    num_updated = 0
    for json_file in json_files:
        with open(json_file, "r") as f:
            json_data = json.load(f)
            ids = json_data["ids"]
            best_saliency = json_data["best_saliency"]
            logger.debug(json_data)
            for db_id, saliency in zip(ids, best_saliency):
                id_bulk_patch = {
                    "attributes": {"saliency": saliency},
                    "ids": [db_id],
                    "in_place": 1,
                }
                try:
                    logger.info(id_bulk_patch)
                    response = api.update_localization_list(project=project_id, **params,
                                                            localization_bulk_update=id_bulk_patch)
                    logger.debug(response)
                    num_updated += 1
                except Exception as e:
                    print(e)
    logger.info(f"Updated {num_updated} localizations")


def compute_saliency_cost(data,
                          scale_percent: int = 10,
                          min_std: float = 2.0,
                          block_size: int = 39):
    """
    Update the saliency cost of the detection in the image
    :param data: tuple with image path, boxes, labels, poses, ids
    :param scale_percent: percentage to scale the image
    :param min_std: minimum standard deviation for the blobs
    :param block_size: block size for the thresholding
    :return: dataframe with the saliency cost
    """
    image_path, boxes, labels, poses, ids = data

    image_path = Path(image_path[0])

    # If no boxes are found, cannot assign saliency cost
    if len(boxes) == 0:
        return 0

    if not image_path.exists():
        logger.error(f"Could not find image {image_path}")
        return 0

    # Load the image and resize it
    image = cv2.imread(image_path.as_posix())
    scale_factor = scale_percent / 100.
    dim = (int(image.shape[1] * scale_factor), int(image.shape[0] * scale_factor))
    image = cv2.resize(image, dim, interpolation=cv2.INTER_AREA)
    saliency_map = compute_saliency(image)

    # Extract blobs from the saliency map
    # Compute the threshold saliency map
    saliency_map_thres_c = compute_saliency_threshold_map(block_size, saliency_map)
    img_lum = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)[:, :, 0]
    df_blob = process_contour_blobs(min_std, saliency_map_thres_c, img_lum)

    # If no blobs are found, cannot assign saliency cost
    if df_blob.empty:
        return 0

    matches = {}
    for index, db_id in enumerate(ids):
        matches[db_id] = {"best_iou": 0.0, "best_saliency": -1, "index": index}

    # Find the box that has the highest IOU with the blob
    for idx, row in df_blob.iterrows():

        blob_box = row.x, row.y, row.xx, row.xy
        # Iterate through the array of arrays of boxes
        for id, box in zip(ids, boxes):
            scaled_box = [int(scale_factor * f) for f in box]
            # Some simple math to compute the intersection over union
            x_min_inter = max(blob_box[0], scaled_box[0])
            y_min_inter = max(blob_box[1], scaled_box[1])
            x_max_inter = min(blob_box[2], scaled_box[2])
            y_max_inter = min(blob_box[3], scaled_box[3])
            inter_width = max(0, x_max_inter - x_min_inter)
            inter_height = max(0, y_max_inter - y_min_inter)
            intersection_area = inter_width * inter_height
            box1_area = (blob_box[2] - blob_box[0]) * (blob_box[3] - blob_box[1])
            box2_area = (scaled_box[2] - scaled_box[0]) * (scaled_box[3] - scaled_box[1])
            union_area = box1_area + box2_area - intersection_area
            iou_value = intersection_area / union_area if union_area > 0 else 0

            if iou_value > matches[id]["best_iou"] and iou_value > 0.5:
                matches[id]["best_iou"] = iou_value
                matches[id]["best_saliency"] = row.saliency

    match_dict = {"ids": [], "best_iou": [], "best_saliency": []}
    for id, match in matches.items():
        # If the best saliency is -1, no match was found so compute the saliency cost manually
        if match["best_saliency"] == -1:
            idx = matches[id]["index"]
            x, y, xx, xy = boxes[idx]
            x = int(x * scale_factor)
            y = int(y * scale_factor)
            xx = int(xx * scale_factor)
            xy = int(xy * scale_factor)
            df = process_contour_box(x, y, xx, xy, min_std, saliency_map_thres_c, img_lum)
            print(f"Manual saliency cost for {id} is {df.saliency.max()}")
            if not df.empty:
                matches[id]["best_saliency"] = int(df.saliency.max())

        match_dict["ids"].append(id)
        match_dict["best_iou"].append(match["best_iou"])
        match_dict["best_saliency"].append(match["best_saliency"])

    return match_dict


# Beam pipeline
def run_pipeline(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Download data and assign saliency values.")
    parser.add_argument("--config", required=True, help="Config file path")
    parser.add_argument("--voc-search-pattern", required=True, help="VOC XML files search pattern,"
                                                                    "e.g. /tmp/aipipeline/data/Baseline/voc/*.xml "
                                                                    "or /tmp/aipipeline/data/Baseline/voc")
    parser.add_argument("--scale-percent", default=50, type=int, help="Scale percent (downsized) "
                                                                      "for saliency computation")
    parser.add_argument("--min-std", default=2.0, type=float, help="Minimum standard deviation for saliency")
    parser.add_argument("--block-size", default=39, type=int, help="Block size for saliency blob detection")
    parser.add_argument("--update", default=False, action="store_true", help="Update the database with saliency scores")
    parser.add_argument("--min-saliency", type=int, help="Remove VOC xml entries that are lower than a certain "
                                                         "saliency score")
    args, beam_args = parser.parse_known_args(argv)
    options = PipelineOptions(beam_args)
    conf_files, config_dict = setup_config(args.config, silent=True)

    if not os.getenv("TATOR_TOKEN"):
        logger.error("TATOR_TOKEN environment variable is not set.")
        return

    # Some cleaning; remove all .json files in the directory
    voc_search_pattern = Path(args.voc_search_pattern) / "*.xml" if "*" not in args.voc_search_pattern else Path(
        args.voc_search_pattern)
    logger.info(f"Cleaning up {voc_search_pattern.parent}")
    # for f in voc_search_pattern.parent.rglob('*.json'):
    #     f.unlink()

    # Get the Tator API
    api = tator.get_api(config_dict["tator"]["host"], TATOR_TOKEN)

    # Get the project and box IDs
    projects = api.get_project_list()
    project_name = config_dict["tator"]["project"]
    project = [p for p in projects if p.name == project_name]
    if not project:
        logger.error(f"Project {project_name} not found")
        return
    project_id = project[0].id
    boxes = api.get_localization_type_list(project=project_id)
    box = [b for b in boxes if b.name == "Boxes" or b.name == "Box"]
    if not box:
        logger.error(f"Box type not found in project {project_name}")
        return
    box_id = box[0].id

    # The block size must be odd; if it is even, make it odd
    if args.block_size % 2 == 0:
        args.block_size += 1

    batch_size = 10
    # with beam.Pipeline(options=options) as p:
    #     (
    #             p
    #             | "Match XML Filenames" >> MatchFiles(args.voc_search_pattern)  # Match files by pattern
    #             | "ReadMatches" >> ReadMatches()
    #             | "ReadImages" >> beam.Map(read_xml)
    #             | "BatchXML" >> beam.BatchElements(min_batch_size=batch_size, max_batch_size=batch_size)
    #             | "ProcessXMLBatches" >> beam.Map(process_xml_batch,
    #                                               scale_percent=args.scale_percent,
    #                                               min_std=args.min_std,
    #                                               block_size=args.block_size)
    #     )

    if args.min_saliency:
        remove_low_saliency(voc_search_pattern, args.min_saliency)

    if args.update:
        update_database(voc_search_pattern.parent, api, project_id, box_id)


if __name__ == "__main__":
    run_pipeline()
