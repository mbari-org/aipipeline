import tator
import os

project_id = 1  # i2map project in the database (i2map.shore.mbari.org)
version_id = 12  # Version ID to delete localizations for
box_type = 5  # Box type ID for localizations
# Connect to Tator
token = os.getenv("TATOR_TOKEN")
api = tator.get_api(host='http://i2map.shore.mbari.org', token=token)

count = api.get_localization_count(project=project_id, type=box_type, version=[f"{version_id}"])

print(f"Found: {count} localizations for version {version_id}")
if count > 0:

    # Delete in batches
    batch_size = 1000
    while count > 0:
        deleted = api.delete_localization_list(project=project_id, version=[version_id], start=0, stop=batch_size)
        print(f"Deleted {deleted if deleted is not None else 0} localizations in current batch.")
        count = api.get_localization_count(project=project_id, type=box_type, version=[f"{version_id}"])
        if count == 0:
            print(f"All localizations for version {version_id} have been deleted.")
            break
