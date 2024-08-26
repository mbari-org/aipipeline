# aipipeline, Apache-2.0 license
# Filename: aipipeline/metrics/calc_accuracy.py
# Description: Calculate accuracy of models. Useful for measuring model performance, drift, etc.

from pathlib import Path
import redis
from sklearn.metrics import precision_score, recall_score, accuracy_score
from sklearn.preprocessing import LabelEncoder
import logging

from aidata.predictors.process_vits import ViTWrapper

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")


def calc_accuracy(config: dict, base_path: Path):
    labels = config["data"]["labels"].strip().split(",")
    r = redis.Redis(
        config["redis"]["host"],
        config["redis"]["port"],
        password=config["redis"]["password"],
    )
    v = ViTWrapper(r, "cuda:0", False, 32)

    # Create a dictionary to encode the labels
    label_encoder = LabelEncoder()
    label_encoder.fit(labels.split(","))
    label_dict = {label: i for i, label in enumerate(label_encoder.classes_)}

    LABELS_VAL = " ".join(labels)
    true_labels = []
    predicted_labels = []

    for l in labels:
        image_root = base_path / l
        image_paths = [str(image_path) for image_path in image_root.rglob("*.jpg")]
        if len(image_paths) == 0:
            print(f"No images found in {image_root}")
            continue

        predictions, scores = v.predict(image_paths, top_n=3)
        for i, prediction in enumerate(predictions):
            class_name = image_paths[i].split("/")[-2]
            predicted_labels.append(prediction)
            true_labels.append(class_name)

    print(true_labels)
    print(predicted_labels)

    true_labels_encoded = [label_dict[label] for label in true_labels]

    # Convert predictions to encoded labels
    predicted_labels_encoded = []
    for preds in predicted_labels:
        encoded_preds = [label_dict[label] for label in preds]
        predicted_labels_encoded.append(encoded_preds)

    print(true_labels_encoded)
    print(predicted_labels_encoded)

    # Calculate top-3 accuracy
    correct_predictions = sum(
        [
            1
            for true_label, pred_labels in zip(true_labels_encoded, predicted_labels_encoded)
            if true_label in pred_labels
        ]
    )
    accuracy_top3 = correct_predictions / len(true_labels_encoded)

    # Precision and recall calculation (for top-1 predictions)
    top1_predicted_labels_encoded = [pred[0] for pred in predicted_labels_encoded]
    precision = precision_score(true_labels_encoded, top1_predicted_labels_encoded, average="micro")
    recall = recall_score(true_labels_encoded, top1_predicted_labels_encoded, average="micro")
    accuracy_top1 = accuracy_score(true_labels_encoded, top1_predicted_labels_encoded)

    print(f"{LABELS_VAL} Top-3 Accuracy: {accuracy_top3}")
    print(f"{LABELS_VAL} Top-1 Accuracy: {accuracy_top1}")
    print(f"{LABELS_VAL} Precision: {precision}")
    print(f"{LABELS_VAL} Recall: {recall}")


if __name__ == "__main__":
    config_dict = {
        "redis": {
            "host": "localhost",
            "port": 6379,
            "password": None,
        },
    }
    calc_accuracy(config_dict, Path("/mnt/UAV/Baseline_all/combined/crops/"))
