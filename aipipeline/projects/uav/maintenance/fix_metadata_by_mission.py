# Utility script to update metadata values in the database for trinity media from image EXIF data
import os
from pathlib import Path
import piexif  # type: ignore

import logging
import tator

logging.basicConfig(level=logging.INFO)
fh = logging.FileHandler("fix_metadata_by_mission.log")
fh.setLevel(logging.INFO)
logging.getLogger().addHandler(fh)

from mbari_aidata.plugins.extractors.tap_sony_media import extract_media

kwargs = {}
project = 4  # uav project in the database
mission = 'trinity-2_20241220T190455_NewBrighton' # Mission name to update
section = "2024/12/NewBrighton" # Section to update media to

# Connect to Tator
api = tator.get_api(host='https://mantis.shore.mbari.org', token=os.environ['TATOR_TOKEN'])

# Get all media in the project with the mission
medias = api.get_media_list(project=project, attribute_contains=[f"$name::{mission}"])

# Find all media in the mission directory and extract the metadata
media_mdata_df = extract_media(Path(f"/Volumes/UAV/Level-1/trinity-2_20241220T190455_NewBrighton/"))

num_updated = 0

# Create the section if it doesn't exist
if not api.get_section_list(project=project, name=section):
    section_create = tator.models.SectionCreate(name=section)
    api.create_section(project=project, section_create=section_create)
    logging.info(f"Created section {section}")

for row, mdata in media_mdata_df.iterrows():
    for m in medias:
        if Path(mdata.media_path).name == m.name:
            logging.info(f"Fixing {m.name}")
            # Update the media with the metadata from the image
            u = tator.models.MediaUpdate(attributes={
                "date": mdata.date.isoformat(),
                "latitude": mdata.latitude,
                "longitude": mdata.longitude,
                "altitude": mdata.altitude,
                "make": mdata.make,
                "model": mdata.model,
                "section": section,
            })
            response = api.update_media(id=m.id, media_update=u)
            logging.info(
                f"  Updated media {m.id} {mdata.media_path}  {response}")
            num_updated += 1

logging.info(f"Updated {num_updated} media in mission {mission}.")
