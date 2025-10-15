import os
import shutil
import random
from collections import defaultdict
from rfdetr import RFDETRLarge
import xml.etree.ElementTree as ET
from pathlib import Path
import json
from collections import Counter


def split(original_coco, images_dirs, output_base):
    # Load COCO data
    with open(original_coco, 'r') as f:
        data = json.load(f)

    images = data['images']
    annotations = data['annotations']
    categories = data['categories']

    # Group annotations by image_id
    img_to_anns = defaultdict(list)
    for ann in annotations:
        img_to_anns[ann['image_id']].append(ann)

    # Shuffle image IDs
    image_ids = list(img_to_anns.keys())
    random.shuffle(image_ids)

    # Split into train (75%), valid (20%), test (5%)
    n = len(image_ids)
    train_ids = image_ids[:int(0.75 * n)]
    val_ids = image_ids[int(0.75 * n):int(0.95 * n)]
    test_ids = image_ids[int(0.95 * n):]

    splits = {'train': train_ids, 'valid': val_ids, 'test': test_ids}

    for split_name, ids in splits.items():
        split_dir = os.path.join(output_base, split_name)
        os.makedirs(split_dir, exist_ok=True)

        # Filter images and annotations
        split_images = [img for img in images if img['id'] in ids]
        split_anns = []
        for iid in ids:
            split_anns.extend(img_to_anns[iid])

        # Create split COCO data
        split_data = {
            'images': split_images,
            'annotations': split_anns,
            'categories': categories
        }

        # Save annotations
        with open(os.path.join(split_dir, '_annotations.coco.json'), 'w') as f:
            # Add info license fields to satisfy COCO format
            split_data['info'] = {
                "description": "Dataset split",
                "url": "",
                "version": "1.0",
                "year": 2025,
                "contributor": "",
                "date_created": "2024-01-01"
            }
            json.dump(split_data, f, indent=4)

        # Copy images from appropriate directories
        for img in split_images:
            src = None
            for images_dir in images_dirs:
                potential_src = os.path.join(images_dir, img['file_name'])
                if os.path.exists(potential_src):
                    src = potential_src
                    break
            if src:
                dst = os.path.join(split_dir, img['file_name'])
                shutil.copy(src, dst)
                print(f"Copied {src} to {dst}")
            else:
                print(f"Warning: Image {img['file_name']} not found in any images directory")

    print("Dataset split completed.")
def voc_to_coco(voc_datasets, output_json):
    """
    Combine multiple VOC datasets and convert to COCO format.

    Args:
        voc_datasets (list of tuples): List of (voc_dir, images_dir) tuples.
        output_json (str): Output path for COCO JSON.
    """
    # First, collect all class names from all XML files
    class_names = set()
    for voc_dir, images_dir in voc_datasets:
        xml_files = list(Path(voc_dir).glob("*.xml"))
        for xml_file in xml_files:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            for obj in root.findall("object"):
                name_elem = obj.find("name")
                if name_elem is not None:
                    name = name_elem.text
                    if name:
                        class_names.add(name)

    # Flag duplicates using lower case
    lower_names = [name.lower() for name in class_names]
    if len(lower_names) != len(set(lower_names)):
        print("Error: Duplicate categories found (case-insensitive):")
        counts = Counter(lower_names)
        for name_lower, count in counts.items():
            if count > 1:
                print(f"  {name_lower}: {count} occurrences")
        raise ValueError("Duplicate categories detected. Please resolve naming conflicts before proceeding.")

    # Use unique categories (preserving original case)
    categories = list(class_names)

    coco_data = {
        "images": [],
        "annotations": [],
        "categories": []
    }

    for i, cat in enumerate(categories):
        coco_data["categories"].append({"id": i, "name": cat, "supercategory": "none"})

    ann_id = 0
    img_id = 0
    img_filename_to_id = {}

    # Combine all XML files from all VOC datasets
    all_xml_files = []
    for voc_dir, images_dir in voc_datasets:
        all_xml_files.extend(list(Path(voc_dir).glob("*.xml")))

    for xml_file in all_xml_files:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Image info
        filename = root.find("filename").text
        width = int(root.find("size/width").text)
        height = int(root.find("size/height").text)
        if filename not in img_filename_to_id:
            coco_data["images"].append({
                "id": img_id,
                "file_name": filename,
                "width": width,
                "height": height
            })
            img_filename_to_id[filename] = img_id
            img_id += 1
        image_id = img_filename_to_id[filename]

        # Annotations
        for obj in root.findall("object"):
            name_elem = obj.find("name")
            if name_elem is None:
                continue
            name = name_elem.text
            if not name or name not in categories:
                continue
            cat_id = categories.index(name)
            bbox = obj.find("bndbox")
            xmin = float(bbox.find("xmin").text)
            ymin = float(bbox.find("ymin").text)
            xmax = float(bbox.find("xmax").text)
            ymax = float(bbox.find("ymax").text)
            coco_data["annotations"].append({
                "id": ann_id,
                "image_id": image_id,
                "category_id": cat_id,
                "bbox": [xmin, ymin, xmax - xmin, ymax - ymin],
                "area": (xmax - xmin) * (ymax - ymin),
                "iscrowd": 0
            })
            ann_id += 1

    with open(output_json, "w") as f:
        json.dump(coco_data, f, indent=4)


def main():
    images_dir1 = "/mnt/DeepSea-AI/scratch/i2mapbulk/Baseline_mbari-i2map-vits-b8-20251008-vss/images/"
    images_dir2 = "/mnt/DeepSea-AI/scratch/i2map/Baseline_mbari-i2map-vits-b8-20251008-vss/images/"
    voc_dir1 = "/mnt/DeepSea-AI/scratch/i2mapbulk/Baseline_mbari-i2map-vits-b8-20251008-vss/voc/"
    voc_dir2 = "/mnt/DeepSea-AI/scratch/i2map/Baseline_mbari-i2map-vits-b8-20251008-vss/voc/"
    original_coco = "output_coco.json"
    dataset_location = "/mnt/DeepSea-AI/scratch/i2map_dataset/" # Base directory for train/valid/test

    # Combine two VOC datasets with their respective image directories
    voc_to_coco([(voc_dir1, images_dir1), (voc_dir2, images_dir2)], original_coco)

    # Clean the final dataset location if it exists
    if os.path.exists(dataset_location):
        shutil.rmtree(dataset_location)

    # Split the dataset, providing all image directories
    split(original_coco, [images_dir1, images_dir2], dataset_location)

    model = RFDETRLarge()
    model.train(dataset_dir=dataset_location, epochs=50, batch_size=8, grad_accum_steps=2)
    # model = RFDETRMedium()
    #model.train(dataset_dir=dataset_location, epochs=10, batch_size=16, grad_accum_steps=2)

if __name__ == "__main__":
    main()
