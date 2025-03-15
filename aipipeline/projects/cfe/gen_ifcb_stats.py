import os
import json
from collections import defaultdict
from pathlib import Path

# Define the base directory
base_dir = Path("/mnt/ML_SCRATCH/ifcb/raw/2014-square/crops")

# Dictionary to store totals
stats = defaultdict(int)

# Traverse the base directory
for subdir in base_dir.iterdir():
    if subdir.is_dir():  # Only process directories
        stats[subdir.name] = sum(1 for file in subdir.iterdir() if file.is_file())

# Save to stats.json
stats_json = {"total_labels": stats}
output_file = base_dir / "stats.json"

with output_file.open("w") as f:
    json.dump(stats_json, f, indent=4)

print(f"Stats saved to {output_file}")