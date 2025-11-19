import tator
import os

project_id = 3  # i2map project in the database (mantis.shore.mbari.org)
section_id = 282  # Section ID delete localizations for
box_type = 3  # Box type ID for localizations

# Connect to Tator
token = os.getenv("TATOR_TOKEN")
api = tator.get_api(host='https://mantis.shore.mbari.org', token=token)

count = api.get_localization_count(project=project_id, type=box_type, section=section_id)

print(f"Found: {count} localizations for version {section_id}")
if count > 0:

    batch_size = 100
    while count > 0:
        deleted = api.delete_localization_list(project=project_id, section=section_id, start=0, stop=batch_size)
        print(f"Deleted {deleted if deleted is not None else 0} localizations in current batch.")
        count = api.get_localization_count(project=project_id, type=box_type, section=section_id)
        if count == 0:
            print(f"All localizations for section {section_id} have been deleted.")
            break