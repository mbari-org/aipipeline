import tator
import os

project_id = 12  # planktivore project in the database (mantis.shore.mbari.org)
version_id = 61  # Version ID to delete localizations for

# Connect to Tator
token = os.getenv("TATOR_TOKEN")
api = tator.get_api(host='https://mantis.shore.mbari.org', token=token)


count = api.get_localization_count(project=project_id, type=17, version=[f"{version_id}"])

print(f"Found: {count} localizations for version {version_id}")
if count > 0:

    # Delete in batches
    batch_size = 200
    while count > 0:
        deleted = api.delete_localization_list(project=project_id, version=[version_id], start=0, stop=batch_size)
        print(f"Deleted {deleted if deleted is not None else 0} localizations in current batch.")
        count = api.get_localization_count(project=project_id, type=17, version=[f"{version_id}"])
        if count == 0:
            print(f"All localizations for version {version_id} have been deleted.")
            break


