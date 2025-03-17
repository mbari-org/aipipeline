import json
import argparse
from collections import defaultdict
from pathlib import Path

# Parse arguments
parser = argparse.ArgumentParser(description="Calculate file counts in subdirectories.")
parser.add_argument("--input_dir", type=Path, help="Base directory to process")
args = parser.parse_args()

# Dictionary to store totals
stats = defaultdict(int)

# Traverse the base directory
for subdir in args.input_dir.iterdir():
    if subdir.is_dir():  # Only process directories
        stats[subdir.name] = sum(1 for file in subdir.iterdir() if file.is_file())

# Save to stats.json
stats_json = {"total_labels": stats}
output_file = args.input_dir / "stats.json"

with output_file.open("w") as f:
    json.dump(stats_json, f, indent=4)

print(f"Stats saved to {output_file}")
