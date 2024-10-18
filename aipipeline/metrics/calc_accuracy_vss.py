# aipipeline, Apache-2.0 license
# Filename: aipipeline/metrics/calc_accuracy.py
# Description: Calculate accuracy of models. Useful for measuring model performance, drift, etc.
import glob
import os
from datetime import datetime
import dotenv
import logging
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

from aidata.predictors.process_vits import ViTWrapper
from aipipeline.config_setup import setup_config
from aipipeline.prediction.library import remove_multicrop_views

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
# and log to file
now = datetime.now()
log_filename = f"vss_calc_acc{now:%Y%m%d}.log"
handler = logging.FileHandler(log_filename, mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Constants
dotenv.load_dotenv()
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
from pathlib import Path
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import precision_score, recall_score, accuracy_score
import redis


def calc_accuracy(config: dict, image_dir: str, password: str):
    base_path = Path(image_dir)
    project = config["vss"]["project"]
    r = redis.Redis(
        host=config["redis"]["host"],
        port=config["redis"]["port"],
        password=password,
    )
    model_name = config["vss"]["model"]
    v = ViTWrapper(r, "cuda:0", model_name=model_name,reset=False, batch_size=32)

    # Get all the class names and exemplar ids from the redis server
    logger.info("Getting all class names and exemplar ids")
    labels, ids = v.get_ids()

    # If there are no labels, return
    if not labels:
        logger.info("No labels found in the redis server")
        return

    labels_unique = list(set(labels))
    logger.info(f"Classes: {labels_unique}")

    # Get all the classes that have less than 10 exemplars - we want to keep these
    low_sample_exemplars = [c for c in labels_unique if labels.count(c) < 10]
    logger.info(f"Low exemplar classes: {low_sample_exemplars}")
    # Get the ids for each class - we will use these to remove exemplars from the test set
    exemplar_ids = {c: [i for i, l in zip(ids, labels) if l == c] for c in labels_unique}
    # Print a summary of the classes and exemplars
    for label, exemplar_id in exemplar_ids.items():
        logger.info(f"Class {label} has {len(exemplar_id)} exemplars")

    true_labels = []
    predicted_labels = []
    true_ids = []
    predicted_ids = []
    predicted_scores = []

    for l in labels_unique:
        logger.info(f"Processing {l}")
        image_root = base_path / l
        image_paths = list(image_root.glob("*.jpg"))
        if not image_paths:
            logger.info(f"No images found in {image_root}")
            continue

        logger.info(f"Found {len(image_paths)} images for {l}")
        # Remove any images that are in the exemplar list by id, unless
        # the class has less than 10 exemplars
        if l not in low_sample_exemplars:
            for image_path in image_paths:
                if image_path.stem in exemplar_ids[l]:
                    logger.info(f"Removing exemplar {image_path}")
                    image_paths.remove(image_path)

        # If there are no images left, alert and continue
        if len(image_paths) == 0:
            logger.debug(f"No images left for {l}")
            continue

        logger.info(f"Predicting top-3 {len(image_paths)} images for {l}")
        for image_path in image_paths:
            logger.debug(f"Processing {image_path}")
            predictions, scores, ids = v.predict([str(image_path)], top_n=3)
            logger.debug(f"True: {l} predictions: {predictions}")
            predicted_labels.append(predictions)
            true_labels.append(l)
            true_ids.append(image_path.stem)
            predicted_ids.append(ids[0])
            predicted_scores.append(scores[0])

    if not true_labels:
        logger.error(f"No images found to calculate accuracy in {base_path}")
        return

    # Create a dictionary to encode the labels
    label_encoder = LabelEncoder()
    # Combine both the found labels and the database labels in case there are missing labels
    combined = predicted_labels + [labels_unique]
    flattened = [item for sublist in combined for item in sublist]
    labels_unique_all = list(set(flattened))
    label_encoder.fit(labels_unique_all)
    label_dict = {label: i for i, label in enumerate(label_encoder.classes_)}
    LABELS_VAL = ", ".join(labels_unique_all)

    # Convert predictions to encoded labels
    true_labels_encoded = [label_dict[label] for label in true_labels]
    predicted_labels_encoded = [[label_dict[label] for label in preds] for preds in predicted_labels]

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
        f"CM {project} exemplars. Top-1 Accuracy: {accuracy_top1:.2f}, Top-3 Accuracy: {accuracy_top3:.2f}, "
        f"Precision: {precision:.2f}, Recall: {recall:.2f}")
    d = f"{datetime.now():%Y-%m-%d %H%M%S}"
    plt.title(d)
    plot_name = f"confusion_matrix_{project}_{d}.png"
    logger.info(f"Saving confusion matrix to {plot_name}")
    plt.savefig(plot_name)
    plt.close()

    # Export the confusion matrix to a csv file
    cm_df = pd.DataFrame(cm, columns=label_encoder.classes_, index=label_encoder.classes_)
    cm_df.to_csv(f"confusion_matrix_{project}_{d}.csv")

    # Print a report of all the confused id
    df = pd.DataFrame({"true_label": true_labels,
                       "pred_label": [preds[0] for preds in predicted_labels],
                       "true_id": true_ids, 'predicted_id': predicted_ids,
                       "predicted_score": [1. - float(preds[0]) for preds in predicted_scores]})
    # Only save the confused labels, those where the true label is not the same as the predicted label
    confused = df[df["true_label"] != df["pred_label"]]

    def add_comment(x):
        if float(x["predicted_score"]) > 0.9:
            return f"Very similar to {x['pred_label']}"

    # Add another column noting creating a comment if the predicted score is above 0.9
    confused["comment"] = confused.apply(add_comment, axis=1)
    confused = confused.groupby("true_label").apply(lambda x: x.sort_values("pred_label"))
    confused = confused.reset_index(drop=True)
    confused["predicted_score"] = confused["predicted_score"].map("{:.2f}".format)
    confused.to_csv(f"confused_ids_{project}_{d}.csv")
    logger.info(f"Saved confused labels to confused_{project}_{d}.csv")


def main(argv=None):
    import argparse

    example_project = Path(__file__).resolve().parent.parent / "projects" / "biodiversity" / "config" / "config.yml"
    parser = argparse.ArgumentParser(description="Calculate the accuracy of the vss")
    parser.add_argument("--config", required=False, help="Config file path", default=example_project)
    parser.add_argument("--images", required=False, help="Path to images")
    args = parser.parse_args(argv)

    _, config_dict = setup_config(args.config)

    if not os.getenv("REDIS_PASSWORD"):
        logger.error("REDIS_PASSWORD environment variable is not set.")
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
    remove_multicrop_views(image_path)

    calc_accuracy(config_dict, image_path, REDIS_PASSWORD)


if __name__ == "__main__":
    main()
