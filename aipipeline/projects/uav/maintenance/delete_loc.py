import os

import tator
import os

kwargs = {}
project_id = 4  # project in the database
version_id = 25  # version in the database

# Connect to Tator
token = os.getenv("TATOR_TOKEN")
api = tator.get_api(host='http://mantis.shore.mbari.org', token=token)

# Search for media with name
attribute_media = ["$name::trinity-2_20240820T233850_NewBrighton"]
kwargs["attribute_contains"] = attribute_media
medias = api.get_media_list(project=project_id, **kwargs)
print(f"Found {len(medias)} media.")
kwargs["version"] = [version_id]
media_ids = [media.id for media in medias]
batch_size = 1

related_attr = [f"version::{version_id}"]

for i in range(0, len(media_ids), batch_size):
    print(f"Deleting localizations flagged for deletion for media index {i + batch_size} ...")
    response = api.delete_localization_list(
        project=project_id,
        media_id=media_ids[i: i + batch_size],
        related_attribute=related_attr
    )
    print(response)

print(f"Finished deleting localizations flagged for deletion in project {project_id}")