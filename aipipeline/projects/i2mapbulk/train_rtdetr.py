import json
import os
import shutil
import random
from collections import defaultdict
import xml.etree.ElementTree as ET
from pathlib import Path
from rfdetr import RFDETRLarge

def split(original_coco, images_dir, output_base):
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

    # Split into train (70%), valid (20%), test (10%)
    n = len(image_ids)
    train_ids = image_ids[:int(0.7 * n)]
    val_ids = image_ids[int(0.7 * n):int(0.9 * n)]
    test_ids = image_ids[int(0.9 * n):]

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

        # Copy images
        for img in split_images:
            src = os.path.join(images_dir, img['file_name'])
            dst = os.path.join(split_dir, img['file_name'])
            shutil.copy(src, dst)
            print(f"Copied {src} to {dst}")

    print("Dataset split completed.")
def voc_to_coco(voc_dir, images_dir, output_json):
    coco_data = {
        "images": [],
        "annotations": [],
        "categories": []
    }
    # Define categories (adjust based on your classes)
    categories = ["Beroe"]
    for i, cat in enumerate(categories):
        coco_data["categories"].append({"id": i, "name": cat, "supercategory": "none"})

    ann_id = 0
    img_id = 0

    for xml_file in Path(voc_dir).glob("*.xml"):
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Image info
        filename = root.find("filename").text
        width = int(root.find("size/width").text)
        height = int(root.find("size/height").text)
        coco_data["images"].append({
            "id": img_id,
            "file_name": filename,
            "width": width,
            "height": height
        })

        # Annotations
        for obj in root.findall("object"):
            name = obj.find("name").text
            if name not in categories:
                continue
            cat_id = categories.index(name)
            bbox = obj.find("bndbox")
            xmin = float(bbox.find("xmin").text)
            ymin = float(bbox.find("ymin").text)
            xmax = float(bbox.find("xmax").text)
            ymax = float(bbox.find("ymax").text)
            coco_data["annotations"].append({
                "id": ann_id,
                "image_id": img_id,
                "category_id": cat_id,
                "bbox": [xmin, ymin, xmax - xmin, ymax - ymin],
                "area": (xmax - xmin) * (ymax - ymin),
                "iscrowd": 0
            })
            ann_id += 1
        img_id += 1

    with open(output_json, "w") as f:
        json.dump(coco_data, f, indent=4)

images_dir = "/mnt/ML_SCRATCH/beroe/Baseline/images/"
voc_dir = "/mnt/ML_SCRATCH/beroe/Baseline/voc/"
original_coco = "output_coco.json"
dataset_location = "/mnt/ML_SCRATCH/beroe_dataset/" # Base directory for train/valid/test

# voc_to_coco(voc_dir, images_dir, original_coco)
# # Clean the dataset location if it exists
# if os.path.exists(dataset_location):
#     shutil.rmtree(dataset_location)
# # Split the dataset
# split(original_coco, images_dir, dataset_location)

model = RFDETRLarge()
model.train(dataset_dir=dataset_location, epochs=10, batch_size=8, grad_accum_steps=2)
#model.train(dataset_dir=dataset_location, epochs=10, batch_size=16, grad_accum_steps=2)
