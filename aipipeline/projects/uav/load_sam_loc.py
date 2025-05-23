# Utility to load the bounding box data from a CSV file and update the bounding box data in Tator
import os
from pathlib import Path
from aipipeline.db.utils import init_api_project
import pandas as pd

out_csv = Path("/Users/dcline/aidata/datasets/Baseline/crops/BirdOut") / "birdbox.csv"
host = "mantis.shore.mbari.org"
TATOR_TOKEN=os.environ["TATOR_TOKEN"]
project_name="901902-uavs"
api, project_id = init_api_project(host=host, token=TATOR_TOKEN, project=project_name)

df = pd.read_csv(out_csv)

image_width = 7952
image_height = 5304

# Iterate over the rows and fix the bounding box data
for i, row in df.iterrows():
    try:
        localization = api.get_localization(row["id"])
    except Exception as e:
        print(f"Error getting localization for {row['image']}: {e}")
        continue
    x = row["x"]/image_width + localization.x
    y = row["y"]/image_height + localization.y
    w = row["width"] / image_width
    h = row["height"] / image_height
    print(f"Updating {row['image']} to {x},{y},{w},{h}")
    update = {'width':  w, 'height': h, 'x': x, 'y': y}
    try:
        api.update_localization(row['id'], localization_update=update)
        print(f"Updated {row['image']}")
    except Exception as e:
        print(f"Error updating {row['image']}: {e}")
        continue