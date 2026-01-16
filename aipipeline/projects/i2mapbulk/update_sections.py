#!/usr/bin/env python
# This script updates the sections of all media in the i2map project
# This is lost in the migration to the new Tator instance
import os
import tator
from tator.openapi.tator_openapi import MediaBulkUpdate

project_id = 1  # i2map project in the database
media_by_section = {}
section_uuid_to_id = {}

# Connect to Tator
api = tator.get_api(host='http://i2map.shore.mbari.org', token=os.environ['TATOR_TOKEN'])

# Get media count
media_count = api.get_media_count(project=project_id)

# Get the mapping of sections to section ids
sections = api.get_section_list(project=project_id)
for section in sections:
    section_uuid_to_id[section.elemental_id] = section.id

batch_size = 100
for media_batch in range(0, media_count, batch_size):
    response = api.get_media_list(project=project_id, start=media_batch, stop=media_batch + batch_size)
    for media in response:
        if ".mp4" not in media.name:
            section = media.attributes['tator_user_sections']
            if section not in media_by_section:
                media_by_section[section] = []
            media_by_section[section].append(media.id)

for section, media_ids in media_by_section.items():
    print(f"Updating section {section} with {len(media_ids)} media")
    media_update = MediaBulkUpdate(attributes={"tator_user_sections": section})
    # Process in batches of 500
    for i in range(0, len(media_ids), 500):
        print(f"Updating media {i} to {i+500}")
        media_ids_batch = media_ids[i:i+500]
        api.update_media_list(project=project_id, media_id=media_ids_batch, media_bulk_update=media_update)
print("Done")