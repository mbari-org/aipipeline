# aipipeline, Apache-2.0 license
# Filename: aipiipeline/projects/planktivore/add_depth_time_parquet.py
# Description: Adds depth and time data from LRAUV .nc files into a single DataFrame for planktivore ROIs
import re
import warnings
import sys
import numpy as np
import pandas as pd
import xarray as xr
from pathlib import Path
from xarray.conventions import SerializationWarning

warnings.filterwarnings("ignore", category=SerializationWarning)

def _time_to_datetime64ns(time_values: np.ndarray) -> np.ndarray:
    time_values = np.asarray(time_values)

    if np.issubdtype(time_values.dtype, np.datetime64):
        return time_values.astype("datetime64[ns]")

    if np.issubdtype(time_values.dtype, np.number):
        return pd.to_datetime(time_values, unit="s", origin="unix").to_numpy(dtype="datetime64[ns]")

    return pd.to_datetime(time_values).to_numpy(dtype="datetime64[ns]")

def fetch_nc_data(data_dir: Path) -> pd.DataFrame:
    if not data_dir.exists():
        print(f"Year directory does not exist: {data_dir}")
        return pd.DataFrame(columns=["time", "depth"])

    nc_files: list[Path] = []
    # Match files like 202510271813_202510301715.nc4 only
    pattern = re.compile(r"^\d{12}_\d{12}\.nc4$")
    for file in data_dir.rglob("*.nc4"):
        if pattern.match(file.name):
            nc_files.append(file)
            break

    nc_files = sorted(nc_files)

    if not nc_files:
        print(f"No .nc files found under {data_dir}")
        return pd.DataFrame(columns=["time", "depth"])

    per_file_frames: list[pd.DataFrame] = []

    for i, file in enumerate(nc_files):
        print(f"\n{'=' * 60}")
        print(f"Processing file {i + 1}/{len(nc_files)}: {file.name}")

        try:
            with xr.open_dataset(file.as_posix()) as ds:
                time_1d = ds["depth_time"].values
                depth_1d = ds["depth"].values
                per_file_frames.append(pd.DataFrame({"time": time_1d, "depth": depth_1d}))
        except Exception as e:
            print(f"Error processing file {file}: {e}")
            continue

    if not per_file_frames:
        return pd.DataFrame(columns=["time", "depth"])

    df = pd.concat(per_file_frames, ignore_index=True)
    df = df.sort_values("time")
    return df

def process_year(*, year: int, nc_path: Path, parquet_path: Path, skip_existing: bool = True) -> None:
    print(f"Searching for parquet files for year {year} in {parquet_path}...")
    # First find all directories that start with the year in the parquet path
    all_dirs = sorted(parquet_path.glob(f"{year}*"))
    if not all_dirs:
        print(f"No directories found under {parquet_path} for year={year}")
        return
    roi_parquet_files = []
    for d in all_dirs:
        print(f"Searching {d.name}...")
        roi_parquet_files.extend(d.glob("*_lowmag_level2.parquet"))
        roi_parquet_files.extend(d.glob("*_highmag_level2.parquet"))

    if not roi_parquet_files:
        print(f"No parquet files found under {parquet_path} for year={year}")
        return

    # Load the list of timestamps/depths from the .nc files ONCE per year
    df_times = fetch_nc_data(nc_path)
    if df_times.empty:
        print(f"[{year}] No (time, depth) pairs could be extracted from .nc4 files; skipping year.")
        return

    df_times["matched_flag"] = True

    for parquet_file in roi_parquet_files:
        print(f"[{year}] Processing {parquet_file.name}")

        new_parquet_file = parquet_file.with_name(f"{parquet_file.stem}_with_depth_time.parquet")
        if new_parquet_file.exists():
            if skip_existing:
                print(f"File {new_parquet_file.name} already exists, skipping...")
                continue
            else:
                print(f"File {new_parquet_file.name} already exists, removing...")
                new_parquet_file.unlink()

        df_roi = pd.read_parquet(parquet_file, engine="fastparquet")
        if df_roi.shape[1] < 1:
            print(f"Parquet file {parquet_file.name} has no columns, skipping...")
            continue

        df_roi = df_roi.rename(columns={df_roi.columns[0]: "filename"})

        # 20240415T224300/low_mag_cam-1713221002411232-...
        epoch_us = df_roi["filename"].str[28:44].astype(np.int64)
        df_roi["epoch_seconds"] = np.array(epoch_us, dtype=np.int64)

        df_roi["time"] = pd.to_datetime(df_roi["epoch_seconds"], unit="us").astype("datetime64[ns]")
        df_roi = df_roi.sort_values("time").reset_index(drop=True)

        merged = pd.merge_asof(
            df_roi,
            df_times[["time", "depth", "matched_flag"]],
            on="time",
            direction="nearest",
            tolerance=pd.Timedelta(seconds=5),
        )

        # Flag anything that didn't have a match with NaN for depth
        merged.loc[merged["matched_flag"] == False, "depth"] = np.nan

        # Drop the matched_flag and time columns since these are no longer needed
        merged.drop(columns=["matched_flag", "time"], inplace=True)

        if merged.empty:
            print(f"No matched rows found in {parquet_file.name}; skipping...")
            continue

        # For debugging - the depth should be populated here
        print(f"First row of merged dataframe: {merged.iloc[0]}")
        print(f"Last row of merged dataframe: {merged.iloc[-1]}")
        print(f"First row of times dataframe: {df_times.iloc[0]}")
        print(f"Last row of times dataframe: {df_times.iloc[-1]}")
        merged.to_parquet(new_parquet_file)

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python add_depth_time_parquet.py <year> [--no-skip]")
        print("Example: python add_depth_time_parquet.py 2024")
        print("         python add_depth_time_parquet.py 2024 --no-skip")
        return

    try:
        year = int(sys.argv[1])
        nc_path = Path(f"/mnt/ML_SCRATCH/LRAUV/ahi/missionlogs/{year}")
        parquet_path = Path(f"/mnt/DeepSea-AI/data/Planktivore/raw")
        skip_existing = "--no-skip" not in sys.argv
    except ValueError:
        print(f"Year must be an integer, got: {sys.argv[1]!r}")
        return

    process_year(year=year, nc_path=nc_path, parquet_path=parquet_path, skip_existing=skip_existing)



if __name__ == "__main__":
    main()
