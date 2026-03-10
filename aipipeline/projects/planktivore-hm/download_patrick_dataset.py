# Open a parquet file and display the first 5 rows
import pandas as pd
import os
import subprocess
from datasets import load_dataset
######################################################################################################
# First, download using huggingface cli to a directory mounted on the nginx server
# hf download patcdaniel/synchro-April2025-cluster-labeled-highMag --repo-type dataset --local-dir /Volumes/DeepSea-AI/data/Planktivore/raw/patrick
######################################################################################################
base_dir = "/mnt/DeepSea-AI/data/Planktivore/raw/patrick"
parquet_file = os.path.join(base_dir, "data", "train-00000-of-00001.parquet")
df = pd.read_parquet(parquet_file)
# Load with datasets to get ClassLabel feature so we can map int -> string names
ds = load_dataset("parquet", data_files=parquet_file, split="train")
label_names = [ds.features["label"].int2str(i) for i in ds["label"]]
print(df.head())

# Save all images to a folder
output_dir = os.path.join(base_dir, "data", "images")
os.makedirs(output_dir, exist_ok=True)
for index, row in df.iterrows():
    filename = row["filename"]
    image_bytes = row["image"]["bytes"]
    out_path = os.path.join(output_dir, filename)
    if os.path.exists(out_path):
        continue
    print(f"Saving {filename} to {out_path}")
    with open(out_path, "wb") as f:
        f.write(image_bytes)

print(f"Saved {len(df)} images to {output_dir}")

# Save annotations in SDCAT format
sdcat_df = pd.DataFrame({
    "image_path": df["filename"].apply(lambda fn: os.path.join(output_dir, fn)),
    "image_height": 224,
    "image_width": 224,
    "label": label_names,
    "score": 1.0,
    "cluster": -1
})
csv_out = os.path.join(base_dir, "data", "train_no_image.csv")
os.makedirs(os.path.dirname(os.path.join(base_dir, "data")), exist_ok=True)
sdcat_df.to_csv(csv_out, index=False)
print(f"Saved SDCAT CSV to {csv_out}")

# Print the unique labels
print(f"Unique labels: {sdcat_df['label'].unique()}")
# Print the count of each label
print(f"Count of each label: {sdcat_df['label'].value_counts()}")

# Load using aidata in a subprocess
# Load images first
token = os.getenv("TATOR_TOKEN")
if not token:
    print("TATOR_TOKEN environment variable not set")
    exit(-1)

#command = ["aidata", "load", "images", "--input", output_dir, "--config", "https://docs.mbari.org/internal/ai/projects/config/config_planktivore_hm.yml", "--section", "huggingface", "--token", token, "--dry-run"]
command = ["aidata", "load", "images", "--input", output_dir, "--config", "https://docs.mbari.org/internal/ai/projects/config/config_planktivore_hm.yml", "--section", "huggingface", "--token", token]
#subprocess.run(command)

# Load boxes
#command = ["aidata", "load", "boxes", "--input", csv_out, "--config", "https://docs.mbari.org/internal/ai/projects/config/config_planktivore_hm.yml", "--version", "patrick", "--token", token, "--dry-run"]
command = ["aidata", "load", "boxes", "--input", csv_out, "--config", "https://docs.mbari.org/internal/ai/projects/config/config_planktivore_hm.yml", "--version", "huggingface_patrick", "--token", token]
subprocess.run(command)