# Remove noise from the CFE dataset by filtering out samples with noise labels
# For OSM presentation only
import shutil
from pathlib import Path
import pandas as pd
this_dir = Path(__file__).resolve().parent
roi_dir="/mnt/ML_SCRATCH/isiis/ood_alpha_0.3_high_roi"
clean_dir="/mnt/ML_SCRATCH/isiis/ood_alpha_0.3_high_roi_sans_noise"
csv_file=this_dir / "ood_alpha_0.3_high.csv"
df = pd.read_csv(csv_file)

# Remove any rows in the training data, or with noise or artifact labels
print("Removing training data...")
print(f"Total rows before removing training data : {len(df)}")
df = df[df["in_training"] == False]
print(f"Total rows after removing training data: {len(df)}")
print(f"Total rows before removing noise : {len(df)}")
df = df[df["predicted_label"] != "noise"]
print(f"Total rows after removing noise: {len(df)}")
df = df[df["predicted_label"] != "artifact"]
print(f"Total rows after removing artifact: {len(df)}")

# Add a new column file_path_clean that replaces the string  /mnt/ML_SCRATCH/isiis_roi/mnt/ML_SCRATCH/isiis/ with /mnt/ML_SCRATCH/isiis/
def clean_file_path(row):
    return row["file_path"].replace("/mnt/ML_SCRATCH/isiis_roi/", "/mnt/ML_SCRATCH/isiis/")
df["file_path_clean"]=df.apply(clean_file_path, axis=1)

# Copy the clean files to a new directory
print(f"Copying files to {clean_dir}...")
shutil.copytree(roi_dir, clean_dir, dirs_exist_ok=True)






