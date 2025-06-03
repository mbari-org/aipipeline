# Utility script to add velella localization to uploaded Tator media with the name containing "velella"
import os
import piexif  # type: ignore

import logging
import tator

logging.basicConfig(level=logging.INFO)
fh = logging.FileHandler("add_velella_loc.log")
fh.setLevel(logging.INFO)
logging.getLogger().addHandler(fh)

project = 12  # 902004-Planktivore project in the database
section = "Velella-high-mag2"
box_type = 17
version_id=21 # Baseline

# Connect to Tator
api = tator.get_api(host='https://mantis.shore.mbari.org', token=os.environ['TATOR_TOKEN'])

# Get all media in the project with the media_name attribute set to trinity-2
medias = api.get_media_list(project=project, attribute_contains=["$name::velella"])

print(f"Found {len(medias)} media in project {project} with velella in the image name.")

num_created = 0
for media in medias:
    spec = tator.models.LocalizationSpec(
        type=box_type,
        media_id=media.id,
        version=version_id,
        x=0.0,
        y=0.0,
        width=1.0,
        height=1.0,
        frame=0,
        attributes={
                "Label": "Velella_velella",
                "label_s": "Velella_velella",
                "score": 1.0,
                "score_s": 1.0,
            },
    )
    response = api.create_localization_list(project=project, body=[spec] )
    logging.info(f"Added velella localization to media {media.id} {media.name} with response {response}")
    num_created += 1

logging.info(f"Created {num_created} velella localizations in project {project}.")
