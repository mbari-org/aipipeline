# Copy ROI from Fernanda generated csv to a directory for clustering evaluation.
import shutil
from pathlib import Path
import pandas as pd

def copy_roi_from_csv(csv_path:Path, output_dir:Path):
    """Copy ROI from csv to a directory.

    Args:
        csv_path (str): Path to the csv file.
        output_dir (str): Output directory to copy ROI files to.
    """
    if not csv_path.exists():
        print(f"Error: Input file '{csv_path}' not found.")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(csv_path)
    print(f"Copying {len(df)} ROI files...")
    for _, row in df.iterrows():
        roi_path = row["file_path"]
        print(f"Copying {roi_path} to {output_dir}...")
        shutil.copy(roi_path, output_dir)

    print("Done.")



if __name__ == "__main__":
    scratch_dir = Path("/mnt/ML_SCRATCH/isiis")
    this_dir = Path(__file__).parent
    csv_path = this_dir / "data" / "ood_alpha_0.3_high.csv"
    output_dir = scratch_dir / "ood_alpha_0.3_high_roi"
    copy_roi_from_csv(csv_path, output_dir)