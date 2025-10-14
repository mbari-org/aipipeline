import warnings
import numpy as np
import pandas as pd
import xarray as xr
from pathlib import Path
from xarray.conventions import SerializationWarning
warnings.filterwarnings("ignore", category=SerializationWarning)

# Directory containing .nc files with AHI data extracted from
# https://data.caloos.org/#search?type_group=all&query=ahi%20planktivore&page=1
this_dir =  Path(__file__).resolve().parent.parent.parent
nc_dir = this_dir / "cencoos"

# Get all .nc and .nc4 files
nc_files = []
for file in nc_dir.rglob("*.nc"):
    print(f"  {Path(file).name}")
    nc_files.append(file)

# Initialize final results
final_matches = []
all_matched_indices = set()

# Process each .nc file
for i, file in enumerate(nc_files):
    print(f"\n{'=' * 60}")
    print(f"Processing file {i + 1}/{len(nc_files)}: {file.name}")

    try:
        # Load NetCDF file
        ds = xr.open_dataset(file.as_posix())

        # Check if time needs conversion
        if ds.time.dtype == 'int64' or ds.time.dtype == 'float64':
            ds_time_dt = pd.to_datetime(ds.time.values, unit='s', origin='unix')
            ds = ds.assign_coords(time=ds_time_dt)
            print("Converted time to datetime")

        # Select records below euphotic zone (depth > 20m)
        print("Filtering records below euphotic zone (depth > 20m)...")
        depth_values = ds.depth.values
        mask = depth_values < -20
        ds_below_euphotic = ds.isel(time=mask)
        # Get the time values as a DataFrame
        ds_below_euphotic = pd.DataFrame(ds_below_euphotic.time.values, columns=['time'])
        print(f"AHI records below euphotic zone: {len(ds_below_euphotic)}")

        # Store the match
        final_matches.append(ds_below_euphotic.time.values)
    except Exception as e:
        print(f"Error processing file {file}: {e}")
        continue


# Combine all matches into final DataFrame
if final_matches:
    print(f"Total records found: {len(final_matches)}")

    # Save results
    final_matches = pd.DataFrame({'time': np.concatenate(final_matches)})
    final_matches = final_matches.drop_duplicates().reset_index(drop=True)
    print(f"Unique records after removing duplicates: {len(final_matches)}")
    output_file = f"{nc_dir}/lm_below_euphotic_results.csv"
    final_matches.to_csv(output_file, index=False)
    print(f"\nResults saved to: {output_file}")

else:
    print("No matches found across all files!")