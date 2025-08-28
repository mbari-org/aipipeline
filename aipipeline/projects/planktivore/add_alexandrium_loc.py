# Utility script to add velella localization to uploaded Tator media with the name containing "velella"
import os
import piexif  # type: ignore

import logging
import tator

logging.basicConfig(level=logging.INFO)
fh = logging.FileHandler("add_alexandrium_loc.log")
fh.setLevel(logging.INFO)
logging.getLogger().addHandler(fh)

project = 12  # 902004-Planktivore project in the database
section = "Alexandrium"
label = "alexandrium"
box_type = 17
version_id = 21 # Baseline

# Connect to Tator
api = tator.get_api(host='https://mantis.shore.mbari.org', token=os.environ['TATOR_TOKEN'])

# Get the section ID for Alexandrium
sections = api.get_section_list(project)
section_id = None
for sec in sections:
    if sec.name == section:
        section_id = sec.id
        break


# Get all the medias in the project with the section_name attribute set to label
medias = api.get_media_list(project=project, section=section_id)
print(f"Found {len(medias)} media in project {project} with section {section}.")
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
                "Label": label,
                "label_s": label,
                "score": 1.0,
                "score_s": 1.0,
            },
    )
    response = api.create_localization_list(project=project, body=[spec] )
    logging.info(f"Added {label} localization to media {media.id} {media.name} with response {response}")
    num_created += 1

logging.info(f"Created {num_created} {label} localizations in project {project}.")
