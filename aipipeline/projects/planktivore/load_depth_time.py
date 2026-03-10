# Utility script to fix lat/lon/date values in the database for trinity media
# Replace missing lat/lon/date values with the values from images EXIF data
import os
from pathlib import Path
import pyarrow.parquet as pq
import logging
import tator
import pandas as pd
import sys

logging.basicConfig(level=logging.INFO)
fh = logging.FileHandler("../load_depth_time.log")
fh.setLevel(logging.INFO)
logging.getLogger().addHandler(fh)
 
def load_depth_to_media(parquet_path: Path) -> None:
    project = 12  # planktivore project in the database

    # Get all the parquet files in the parquet_path
    # Only search 1 level deep
    print(f"Searching for parquet files in {parquet_path}...")
    parquet_files = []
    for d in parquet_path.iterdir():
        if d.is_dir():
            print(f"Searching {d.name}...")
            parquet_path = d
            files = list(d.glob("*.parquet"))
            parquet_files.extend(files)

    if len(parquet_files) == 0:
        print(f"No parquet files found in {parquet_path}")
        return 

    # Connect to Tator
    print("Connecting to Tator...")
    api = tator.get_api(host='https://mantis.shore.mbari.org', token=os.environ['TATOR_TOKEN'])

    # Get all media in the project
    print(f"Getting media in project {project}...")
    medias = api.get_media_list(project=project, section=273)
    if len(medias) == 0:
        print(f"No media found in project {project}")
        return

    # Convert media to dataframe. Medias is a list of dictionaries
    import pdb; pdb.set_trace()
    # medias_df = pd.DataFrame(medias.tolist())
    # medias_df['time'] = pd.to_datetime(medias_df['iso_datetime'])
    # medias_df = medias_df.set_index('time')
    medias_df = pd.DataFrame({
        "id": [m.id for m in medias],
        "iso_datetime": [
            m.attributes.get("iso_datetime") if m.attributes else None
            for m in medias
        ],
    })

    dfs = [
        pq.read_table(
            f, columns=["time", "depth"]
        ).to_pandas()
        for f in parquet_files
    ]

    depth_df = (
        pd.concat(dfs, ignore_index=True)
        .drop_duplicates("time")
        .set_index("time")
    )

    medias_df = medias_df.set_index("time")
    medias_df = medias_df.join(depth_df, how="left").reset_index()

    # # Update the media with the depth and time
    # for index, row in df_parquet.iterrows():
    #     media_id = row['id']
    #     depth = row['depth']
    #     # m = tator.models.MediaUpdate(attributes={"depth": depth)
    #     # response = api.update_media(id=media_id, media_update=m)
    #     print(f"Updated media {media_id} with depth {depth}")

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python load_depth_time.py <parquet_path>")
        print("Example: python load_depth_time.py /mnt/DeepSea-AI/data/Planktivore/raw/2025")
        return

    try:
        parquet_path = Path(sys.argv[1])
    except ValueError:
        print(f"Parquet path must be a valid path, got: {sys.argv[1]!r}")
        return

    load_depth_to_media(parquet_path=parquet_path)

if __name__ == "__main__":
    main()
