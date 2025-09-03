import numpy as np
import pandas as pd
import xarray as xr
import glob
from pathlib import Path

# Directory containing .nc files
data_dir = "/Users/dcline/Dropbox/code/ai/aipipeline/aipipeline/projects/bio/data"
vel = "/Users/dcline/Dropbox/code/ai/aipipeline/aipipeline/projects/bio/data/tator_data_ptvr_lm_velella_08_22_25.csv"

# Get all .nc and .nc4 files
nc_files = glob.glob(f"{data_dir}/*.nc4")
print(f"Found {len(nc_files)} NetCDF files:")
for file in nc_files:
    print(f"  {Path(file).name}")

# Load Velella data once
df = pd.read_csv(vel, parse_dates=['(media) iso_datetime'])
df_time_np = df['(media) iso_datetime'].values.astype('datetime64[s]')

print(f"\nVelella time range: {df_time_np.min()} to {df_time_np.max()}")
print(f"Total Velella records: {len(df_time_np)}")

# Initialize final results
final_matches = []
final_matches_lat = []
all_matched_indices = set()

# Process each .nc file
for i, file in enumerate(nc_files):
    print(f"\n{'=' * 60}")
    print(f"Processing file {i + 1}/{len(nc_files)}: {Path(file).name}")

    try:
        # Load NetCDF file
        ds = xr.open_dataset(file)

        # Check if time needs conversion
        if ds.time.dtype == 'int64' or ds.time.dtype == 'float64':
            ds_time_dt = pd.to_datetime(ds.time.values, unit='s', origin='unix')
            ds = ds.assign_coords(time=ds_time_dt)
            print("Converted time to datetime")

        print(f"Velella time range: {df_time_np.min()} to {df_time_np.max()}")
        print(f"AHI time range: {ds.time.values.min()} to {ds.time.values.max()}")
        print(f"Total AHI records: {ds.sizes['time']}")

        # Get nearest matches and calculate time differences
        matched_xr_times = ds.time.sel(time=df_time_np, method='nearest')
        time_diffs = matched_xr_times.values - df_time_np
        time_diffs_seconds = time_diffs.astype('timedelta64[s]').astype(float)

        # Filter for matches within 3 seconds
        within_tolerance = np.abs(time_diffs_seconds) <= 3.0
        valid_indices = np.where(within_tolerance)[0]

        print(f"Matches within 3 seconds: {len(valid_indices)}")

        if len(valid_indices) > 0:
            # Only keep indices not already matched
            new_indices = [idx for idx in valid_indices if idx not in all_matched_indices]

            if new_indices:
                print(f"New unique matches: {len(new_indices)}")

                # Filter data for new matches
                df_filtered = df.iloc[new_indices].copy()
                df_filtered_times = df_time_np[new_indices]
                ds_selected = ds.sel(time=df_filtered_times, method='nearest')
                ds_lat = ds.sel(latitude_time=df_filtered_times, method='nearest')
                ds_lon = ds.sel(longitude_time=df_filtered_times, method='nearest')
                ds_depth = ds.sel(depth_time=df_filtered_times, method='nearest')
                ds_chl = ds.sel(mass_concentration_of_chlorophyll_in_sea_water_time=df_filtered_times, method='nearest')

                # Add metadata about the source file
                df_filtered['source_file'] = Path(file).name
                df_filtered['time_diff_seconds'] = time_diffs_seconds[new_indices]

                #  Add latitude, longitude, depth, chlorophyll data from ds
                df_filtered['latitude'] = ds_lat.latitude.values
                df_filtered['longitude'] = ds_lon.longitude.values
                df_filtered['depth'] = ds_depth.depth.values
                df_filtered['mass_concentration_of_chlorophyll_in_sea_water'] = ds_chl.mass_concentration_of_chlorophyll_in_sea_water.values

                # Store the match
                final_matches.append(df_filtered)
                all_matched_indices.update(new_indices)

                print(f"Time diff stats - Mean: {np.mean(time_diffs_seconds[new_indices]):.3f}s, "
                      f"Max: {np.max(np.abs(time_diffs_seconds[new_indices])):.3f}s")
            else:
                print("No new unique matches found")
        else:
            print("No matches within tolerance")

    except Exception as e:
        print(f"Error processing {file}: {e}")

# Combine all matches into final DataFrame
if final_matches:
    final_df = pd.concat(final_matches, ignore_index=True)

    print(f"\n{'=' * 60}")
    print("FINAL RESULTS:")
    print(f"Total unique matches found: {len(final_df)}")
    print(f"Total Velella records processed: {len(df)}")
    print(f"Match percentage: {len(final_df) / len(df) * 100:.1f}%")

    print(f"\nFinal time difference statistics:")
    print(f"Mean: {final_df['time_diff_seconds'].mean():.3f} seconds")
    print(f"Median: {final_df['time_diff_seconds'].median():.3f} seconds")
    print(f"Max: {final_df['time_diff_seconds'].abs().max():.3f} seconds")
    print(f"Std: {final_df['time_diff_seconds'].std():.3f} seconds")

    print(f"\nMatches by source file:")
    print(final_df['source_file'].value_counts())

    # Save results
    output_file = f"{data_dir}/velella_matched_results.csv"
    final_df.to_csv(output_file, index=False)
    print(f"\nResults saved to: {output_file}")

else:
    print("No matches found across all files!")
    final_df = None