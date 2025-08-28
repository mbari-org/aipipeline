import json
import glob
from pathlib import Path
from collections import defaultdict


def count_filenames_in_json_files(json_directory_pattern):
    """
    Search through JSON files and count total filenames, skipping Velella_velella_top3 directory.

    Args:
        json_directory_pattern: Pattern to match JSON files (e.g., "/path/to/jsons/*.json" or "/path/to/jsons/**/*.json")
    """
    total_filenames = 0
    files_processed = 0
    filename_counts = defaultdict(int)

    # Use glob to find all JSON files
    json_files = glob.glob(json_directory_pattern, recursive=True)

    # Filter out files in Velella_velella_top3 directory
    filtered_json_files = [f for f in json_files if 'Velella_velella_top3' not in f]

    print(f"Found {len(json_files)} JSON files total")
    print(f"Processing {len(filtered_json_files)} JSON files (skipping Velella_velella_top3 directory)...")

    for json_file in filtered_json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)

            # Count filenames in this JSON file
            if 'filenames' in data and isinstance(data['filenames'], list):
                file_count = len(data['filenames'])
                total_filenames += file_count
                filename_counts[json_file] = file_count

            files_processed += 1

            # Progress indicator for large datasets
            if files_processed % 1000 == 0:
                print(f"Processed {files_processed} files, total filenames so far: {total_filenames}")

        except (json.JSONDecodeError, KeyError, IOError) as e:
            print(f"Error processing {json_file}: {e}")
            continue

    print(f"\nSummary:")
    print(f"Total JSON files processed: {files_processed}")
    print(f"Total filenames found: {total_filenames}")
    print(f"Average filenames per JSON file: {total_filenames / files_processed if files_processed > 0 else 0:.2f}")

    return total_filenames, filename_counts


# Usage examples:
# For all JSON files in a directory
json_pattern = "/Volumes/DeepSea-AI/data/Planktivore/processed/vss_lm/**/*.json"

# For JSON files in subdirectories too (recursive)
# json_pattern = "/path/to/json/files/**/*.json"

total_count, file_counts = count_filenames_in_json_files(json_pattern)