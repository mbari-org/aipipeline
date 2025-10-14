import glob
from pathlib import Path
import pandas as pd
import numpy as np

this_dir =  Path(__file__).resolve().parent.parent.parent
data_dir = this_dir
time_file = this_dir / "cencoos" / "lm_below_euphotic_results.csv"
roi_parquet_files = data_dir.glob("*_lowmag_level2.parquet")

# Get times below euphotic zone in the time_file
df_times = pd.read_csv(time_file, parse_dates=['time'])
print(f"Total times below euphotic zone: {len(df_times)}")

df_times = df_times.sort_values('time').reset_index(drop=True)
df_times['matched_flag'] = True  # Add a dummy column to mark matches

# Create a file with a listing of each roi file close to the euphotic zone by time
roi_paths = data_dir.rglob("*_lowmag_level2.parquet")
for path in roi_paths:
    print(f"Processing {Path(path).name}")
    output_file = f"{data_dir}/{Path(path).stem}_below_euphotic.parquet"
    if Path(output_file).exists():
        print(f"Output file {output_file} already exists, skipping...")
        continue
    df_roi = pd.read_parquet(path)
    print(f"Total ROIs in {Path(path).name}: {len(df_roi)}")
    if df_roi.empty:
        print(f"DataFrame is empty for {Path(path).name}, skipping...")
        continue
    print(f"Creating time column from first column")
    # Vectorized extraction of epoch from the first column for speed
    df_roi['epoch'] = df_roi.iloc[:, 0].str.extract(r'-(\d+)-')[0].astype(np.int64)
    df_roi['time'] = pd.to_datetime(df_roi['epoch'], unit='us')
    df_roi = df_roi.sort_values('time').reset_index(drop=True)

    # Use merge_asof to find the nearest time in df_times for each ROI
    merged = pd.merge_asof(
        df_roi,
        df_times[['time', 'matched_flag']],
        on='time',
        direction='nearest',
        tolerance=pd.Timedelta(seconds=5)
    )
    # Only keep rows where a match was found (matched_flag is True)
    matched = merged[merged['matched_flag'] == True]
    print(f"Matched ROIs in {Path(path).name}: {len(matched)}")
    if len(matched) > 0:
        matched.to_parquet(output_file)
        print(f"Wrote matched ROIs to {output_file}")
    else:
        print(f"No matched ROIs found in {Path(path).name}")
