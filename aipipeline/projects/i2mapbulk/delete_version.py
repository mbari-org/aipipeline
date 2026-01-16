import tator
import os

kwargs = {}
project_id = 1  # i2mapbulk project in the database (i2map.shore.mbari.org)
media_type = 2  # video type id in the database
box_type = 5  # Box type id in the database
version_id = 13

# Connect to Tator
token = os.getenv("TATOR_TOKEN")
api = tator.get_api(host='http://i2map.shore.mbari.org', token=token)

# Search for all video and localizations in the project
attribute_video = [f"$type::{media_type}"]
attribute_version = [f"$version::{version_id}"]
kwargs["related_attribute"] = attribute_video
kwargs["attribute"] = attribute_version
localizations = api.get_localization_list(project=project_id, **kwargs)
print(f"Found {len(localizations)} in version {version_id}")

num_deleted = 0
for loc in localizations:
    print(f"Deleting localization {loc.id}")
    response = api.delete_localization(id=loc.id)
    print(response)
    num_deleted += 1

print(f"Deleted {num_deleted} localizations")

# (optionally) Delete the version itself
# api.delete_version(version_id)