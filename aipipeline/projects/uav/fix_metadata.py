# Utility script to fix lat/lon/date values in the database for trinity media
# Replace missing lat/lon/date values with the values from images EXIF data
import re
from datetime import datetime
from pathlib import Path
import piexif  # type: ignore

import logging
import pytz
import tator
import pandas as pd

logging.basicConfig(level=logging.INFO)
fh = logging.FileHandler("fix_metadata.log")
fh.setLevel(logging.INFO)
logging.getLogger().addHandler(fh)

from mbari_aidata.plugins.extractors.tap_sony_media import extract_media

kwargs = {}
project = 4  # uav project in the database

# Connect to Tator
api = tator.get_api(host='http://mantis.shore.mbari.org', token='ae84628927851c1a545c375ea8e4c3da2a022400')

# Get all media in the project
medias = api.get_media_list(project=project)
# Only keep media that have trinity-1 in the name
medias = [x for x in medias if "trinity-2" in x.name]
logging.info(f"Found {len(medias)} media for trinity-2.")

# Sort the media by name
medias = sorted(medias, key=lambda x: x.name)

# Find all media in the /mnt/UAV/Level-1 directory
media_local = Path("/mnt/UAV/Level-1/")

# Get only directories that contain trinity-1 in the name
local_22 = [x for x in media_local.iterdir() if x.is_dir() and "trinity-2" in x.name]

def match_frame(image_path):
    # trinity-1_20220518T173530_DSC00166.JPG
    match1 = re.match(r"^(.+)_(\d{8}T\d{6})_(?P<frame>DSC\d+.JPG)", image_path)
    if match1:
        return match1.group("frame")
    # trinity-1_20220518T173530_NewBrighton_DSC00166.JPG
    match2 = re.match(r"^(.+)_(\d{8}T\d{6})_(.+)_(?P<frame>DSC\d+.JPG)", image_path)
    if match2:
        return match2.group("frame")
    # DSC00166.JPG
    match3 = re.match(r"^(.+)(?P<frame>DSC\d+.JPG)", image_path)
    if match3:
        return match3.group('frame')
    return None


def match_date(date_attr, time_attr, name):
    #2023-12-08T193612T193612
    # Match date in the following formats:
    # trinity-1_20220518T173530_DSC00166.JPG
    match1 = re.match(r"^(.+)_(?P<date>\d{8}T\d{6})_DSC\d+", name)
    if match1:
        dt = match1.group("date")
        return datetime.strptime(dt, "%Y%m%dT%H%M%S").replace(tzinfo=pytz.utc)

    # trinity-1_20220518T173530_NewBrighton_DSC00166.JPG
    match2 = re.match(r"^(.+)_(?P<date>\d{8}T\d{6})_(.+)_DSC\d+", name)
    if match2:
        dt = match2.group("date")
        return datetime.strptime(dt, "%Y%m%dT%H%M%S").replace(tzinfo=pytz.utc)

    # 20220518T173530
    match3 = re.match(r"^(?P<date>\d{8}T\d{6})", name)
    if match3:
        dt = match3.group("date")
        return datetime.strptime(dt, "%Y%m%dT%H%M%S").replace(tzinfo=pytz.utc)

    # 2023-12-08T193612T193612
    match4 = re.match(r"^(?P<date>\d{4}-\d{2}-\d{2}T\d{6}T\d{6})", name)
    if match4:
        dt = match4.group("date")
        return datetime.strptime(dt, "%Y-%m-%dT%H%M%S").replace(tzinfo=pytz.utc)

    if len(date_attr) > 0 and len(time_attr) > 0:
        str = date_attr + "T" + time_attr
        if len(date_attr) == 19:
            return datetime.strptime(date_attr, "%Y-%m-%dT%H:%M:%S")
        return datetime.strptime(str, "%Y:%m:%dT%H:%M:%S").replace(tzinfo=pytz.utc)

    # Date is not in the filename - it is in the exif data
    exif = piexif.load(name)
    if "Exif" in exif and piexif.ExifIFD.DateTimeOriginal in exif["Exif"]:
        date_time_str = exif["Exif"][piexif.ExifIFD.DateTimeOriginal].decode("utf-8")
        dt = datetime.strptime(date_time_str, "%Y:%m:%d %H:%M:%S")
        dt_utc = pytz.utc.localize(dt)
        return dt_utc

    exit(f"Could not match date in {name}")


df_media = pd.DataFrame()
df_media["track_id"] = [m.id for m in medias]
df_media["name"] = [m.name for m in medias]
df_media["date_attr"] = [m.attributes["date"] for m in medias]
df_media["time_attr"] = [m.attributes["time"] for m in medias]
df_media["date"] = df_media.apply(lambda row: match_date(row['date_attr'], row['time_attr'], row['name']), axis=1)
df_media["frame"] = df_media["name"].apply(lambda x: match_frame(x))
df_media["date_str"] = df_media["date"].apply(lambda x: x.strftime("%Y%m%dT%H%M%S"))

num_updated = 0
num_found = 0
for d in local_22:

    # Extract the media metadata from the local directory
    logging.info(f"Processing {d}")
    df_metadata = extract_media(d)
    logging.info(f"Found {len(df_metadata)} images in {d}")
    num_found += len(df_metadata)
    try:
        df_metadata["name"] = df_metadata["image_path"].apply(lambda x: Path(x).name)
        df_metadata["frame"] = df_metadata["image_path"].apply(lambda x: match_frame(x))
        df_metadata["date_str"] = df_metadata["date"].apply(lambda x: x.strftime("%Y%m%dT%H%M%S"))
    except Exception as e:
        logging.info(f"Error processing {d}: {e}")
        continue

    # Find a any df_metadata that date_str starts with 20240424
    # df_metadata = df_metadata[df_metadata["date_str"].str.startswith("20240424")]

    # Find the matching media in the database by frame
    match_df = pd.merge(df_media, df_metadata, on=["date_str", "frame"])

    if match_df.empty:
        logging.info(f"Could not find a match for {d}")
        continue

    if len(match_df) != len(df_metadata):
        logging.info(f"Found {len(match_df)} matches for {d} out of {len(df_metadata)} images")
        # # Try to match by filename only
        match_df = pd.merge(df_media, df_metadata, on=["name"])
        if len(match_df) != len(df_metadata):
            exit(f"Could not find a match for {d}")
        logging.info(f"Found {len(match_df)} matches for {d} out of {len(df_metadata)} images")

    for i, row in match_df.iterrows():
        # Update the media with the lat/lon values
        m = tator.models.MediaUpdate(attributes={
            "date": row.date_y,
            "latitude": row.latitude,
            "longitude": row.longitude,
            "altitude": row.altitude
        })
        response = api.update_media(id=row.id, media_update=m)
        logging.info(
            f"  Updated media {row.id} {row.image_path} with lat/lon {row.latitude}, {row.longitude}. {response}")
        num_updated += 1

logging.info(f"Updated {num_updated} media. Found {len(medias)} media in the database and {num_found} locally.")
