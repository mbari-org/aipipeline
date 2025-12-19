#!/usr/bin/env python
# This script filters sdcat output, assigning outputs based on the best threshold that maximizes F1 score per class
# This is experimental to see if this improves performance by removing the difficult examples
from pathlib import Path
import pandas as pd

threshold_csv = "/mnt/DeepSea-AI/models/i2MAP/mbari-i2map-vits-b8-20251212/optimal_thresholds_mbari-i2map-vits-b8-20251212_20251212_211746.csv"
sdcat_csv = "/mnt/DeepSea-AI/scratch/i2mapbulkall/Baseline/predictions/_mnt_DeepSea-AI_models_i2MAP_mbari-i2map-vits-b8-20251212_20251214_071648_cluster_detections.csv"

class_to_threshold = {}
df_thresh = pd.read_csv(threshold_csv)
df_pred = pd.read_csv(sdcat_csv)

# Create a mapping of class to threshold
for index, row in df_thresh.iterrows():
    class_to_threshold[row["class_name"]] = float(row["threshold"])

print(f"Processing {df_pred}...")
# Add a new column with the threshold per the class
df_pred["threshold"] = df_pred["class"].apply(lambda x: class_to_threshold[x])

# Add a new column that is the score if it exceeds the threshold, otherwise assign to 1
# Those that cannot be assigned based on threshold are assigned to the "Unknown" class with a score 1
# Assigning the score to 1 makes sure when versions are merged via NMS, the difficult examples are not included
df_pred["score_new"] = df_pred.apply(lambda x: 1 if x["score"] >= x["threshold"] else 0, axis=1)

# Add a new column that is the predicted class if it exceeds the threshold, otherwise assign to Unknown
df_pred["class_new"] = df_pred.apply(lambda x: x["class"] if x["score"] >= x["threshold"] else "Unknown", axis=1)

# Drop anything that is now Unknown
df_pred = df_pred[df_pred["class_new"] != "Unknown"]

# Save the filtered dataframe to a new CSV file with renamed columns that are sdcat compatible
df_pred = df_pred.drop(columns=["score", "class"])
df_pred = df_pred.rename(columns={"score_new": "score", "class_new": "class"})
sdcat_csv_path = Path(sdcat_csv)
new_sdcat_csv = Path(sdcat_csv_path.parent) / f"{sdcat_csv_path.stem}_filtered.csv"
df_pred.to_csv(new_sdcat_csv, index=False)

# Report how many predictions were filtered to Unknown
num_unknown = len(df_pred[df_pred["class"] == "Unknown"])
print(f"Filtered {num_unknown} predictions to Unknown.")
print(f"Saved filtered predictions to {new_sdcat_csv}")