import tator
import os

kwargs = {}
project = 3  # 901103-biodiversity project in the database (mantis.shore.mbari.org)
# Connect to Tator
token = os.getenv("TATOR_TOKEN")
api = tator.get_api(host='http://mantis.shore.mbari.org', token=token)

# Search for all video and localizations in the project
attribute_video = ["$type::5"] # 49 is the video type id
attribute_version = ["$version::75"] # 29 is the version id for the ctenophora-sp-a-yv5-vss-all version
kwargs["related_attribute"] = attribute_video
kwargs["attribute"] = attribute_version
localizations = api.get_localization_list(project=project, **kwargs)
print(f"Found {len(localizations)} in version ctenophora-sp-a-yv5-vss-all")

num_deleted = 0
for loc in localizations:
    print(f"Deleting localization {loc.id}")
    response = api.delete_localization(id=loc.id)
    print(response)
    num_deleted += 1

print(f"Deleted {num_deleted} localizations")

# (optionally) Delete the version itself
api.delete_version(75)