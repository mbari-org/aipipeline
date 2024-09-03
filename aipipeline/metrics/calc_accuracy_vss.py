# aipipeline, Apache-2.0 license
# Filename: aipipeline/metrics/calc_accuracy.py
# Description: Calculate accuracy of models. Useful for measuring model performance, drift, etc.
import glob
import os
from datetime import datetime
import dotenv
import logging
import numpy as np
from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

from aidata.predictors.process_vits import ViTWrapper
from aipipeline.config_setup import setup_config

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# and log to file
now = datetime.now()
log_filename = f"vss-calc-acc_vss_{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Constants
dotenv.load_dotenv()
REDIS_PASSWD = os.getenv("REDIS_PASSWD")
from pathlib import Path
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import precision_score, recall_score, accuracy_score
import redis


def calc_accuracy(config: dict, image_dir: str, password: str):
    base_path = Path(image_dir)
    project = config["tator"]["project"]
    r = redis.Redis(
        host=config["redis"]["host"],
        port=config["redis"]["port"],
        password=password,
    )
    v = ViTWrapper(r, "cuda:0", False, 32)

    # Get all the class names and exemplar ids from the redis server
    logger.info("Getting all class names and exemplar ids")
    labels, ids = v.get_ids()

    labels_unique = list(set(labels))
    logger.info(f"Classes: {labels_unique}")
    # Get all the classes that have only one exemplar
    single_exemplar_classes = [c for c in labels_unique if labels.count(c) == 1]
    logger.info(f"Single exemplar classes: {single_exemplar_classes}")

    # Create a dictionary to encode the labels
    label_encoder = LabelEncoder()
    label_encoder.fit(labels)
    label_dict = {label: i for i, label in enumerate(label_encoder.classes_)}

    LABELS_VAL = ", ".join(labels)
    true_labels = []
    predicted_labels = []

    for l in labels_unique:
        logger.info(f"Processing {l}")
        image_root = base_path / l
        image_paths = list(image_root.rglob("*.jpg"))
        image_ids = [int(image_path.stem) for image_path in image_paths]
        if not image_paths:
            logger.info(f"No images found in {image_root}")
            continue

        # Predict the top 3 labels for each image
        logger.info(f"Predicting {len(image_paths)} images")
        predictions, scores, exemplar_ids = v.predict([str(image_path) for image_path in image_paths], top_n=3)
        for i, prediction in enumerate(predictions):
            class_name = image_paths[i].parent.name  # Correctly handle spaces in directory names
            # Exclude exemplars from the accuracy calculation, except for classes with only one exemplar
            if image_ids[i] not in ids or class_name in single_exemplar_classes:
                predicted_labels.append(prediction)
                true_labels.append(class_name)

    if not true_labels:
        logger.error(f"No images found to calculate accuracy in {base_path}")
        return

    true_labels_encoded = [label_dict[label] for label in true_labels]

    # Convert predictions to encoded labels
    predicted_labels_encoded = [[label_dict[label] for label in preds] for preds in predicted_labels]

    logger.info(true_labels_encoded)
    logger.info(predicted_labels_encoded)

    # Calculate top-3 accuracy
    correct_predictions = sum(
        1
        for true_label, pred_labels in zip(true_labels_encoded, predicted_labels_encoded)
        if true_label in pred_labels
    )
    accuracy_top3 = correct_predictions / len(true_labels_encoded)

    # Precision and recall calculation (for top-1 predictions)
    top1_predicted_labels_encoded = [pred[0] for pred in predicted_labels_encoded]
    precision = precision_score(true_labels_encoded, top1_predicted_labels_encoded, average="micro")
    recall = recall_score(true_labels_encoded, top1_predicted_labels_encoded, average="micro")
    accuracy_top1 = accuracy_score(true_labels_encoded, top1_predicted_labels_encoded)

    logger.info(f"{LABELS_VAL} Top-3 Accuracy: {accuracy_top3}")
    logger.info(f"{LABELS_VAL} Top-1 Accuracy: {accuracy_top1}")
    logger.info(f"{LABELS_VAL} Precision: {precision}")
    logger.info(f"{LABELS_VAL} Recall: {recall}")

    # Save the confusion matrix
    cm = confusion_matrix(true_labels_encoded, top1_predicted_labels_encoded)
    # Normalize the confusion matrix to range 0-1
    cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

    plt.figure(figsize=(12, 12))
    sns.heatmap(cm_normalized, annot=True, fmt=".1f", xticklabels=label_encoder.classes_,
                yticklabels=label_encoder.classes_, cmap='Blues')
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.title("Confusion Matrix")
    plt.suptitle(
        f"CM {project} exemplars. Top-1 Accuracy: {accuracy_top1:.2f}, Top-3 Accuracy: {accuracy_top3:.2f}, Precision: {precision:.2f}, Recall: {recall:.2f}")
    d = f"{datetime.now():%Y-%m-%d %H:%M:%S}"
    plt.title(d)
    plot_name = f"confusion_matrix_{project}_{datetime.now():%Y-%m-%d %H%M%S}.png"
    logger.info(f"Saving confusion matrix to {plot_name}")
    plt.savefig(plot_name)
    plt.close()


def main(argv=None):
    import argparse

    example_project = Path(__file__).resolve().parent.parent / "projects" / "biodiversity" / "config" / "config.yml"
    parser = argparse.ArgumentParser(description="Calculate the accuracy of the vss")
    parser.add_argument("--config", required=False, help="Config file path", default=example_project)
    parser.add_argument("--images", required=False, help="Path to images")
    args = parser.parse_args(argv)

    _, config_dict = setup_config(args.config)

    if not os.getenv("REDIS_PASSWD"):
        logger.error("REDIS_PASSWD environment variable is not set.")
        return

    processed_data = config_dict["data"]["processed_path"]
    base_path = os.path.join(processed_data, config_dict["data"]["version"])

    if not args.images:
        # Get the crops from the config_dict if not provided
        image_path = os.path.join(base_path, "crops")
        logger.error(f"Crops path is not set. Using {image_path}")
    else:
        image_path = args.images

    # Remove any previous augmented data before starting
    logger.info("Removing augmented data")
    pattern = os.path.join(processed_data, '*.*.png')
    files = glob.glob(pattern)
    for file in files:
        logger.info(f"Removing augmented {file}")
        os.remove(file)

    calc_accuracy(config_dict, image_path, REDIS_PASSWD)


if __name__ == "__main__":
    main()
