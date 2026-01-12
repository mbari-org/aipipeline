import tator
import os
import tator.openapi.tator_openapi.models as models

project_id = 14  # cfe project in the database (mantis.shore.mbari.org)
section_id = 274  # Section ID update localizations for
box_type = 18  # Box type ID

# Connect to Tator
token = os.getenv("TATOR_TOKEN")
api = tator.get_api(host='https://mantis.shore.mbari.org', token=token)

count = api.get_localization_count(project=project_id, type=box_type, section=section_id)

print(f"Found: {count} localizations for version {section_id}")
if count > 0:
    batch_size = 1000
    start = 0
    stop = batch_size

    while count > 0:
        # Fetch localizations in batches
        localizations = api.get_localization_list(project=project_id, type=box_type, section=section_id, start=start, stop=stop)

        # Subtract 1 from the frame number for each localization
        print(f"Updating {len(localizations)} localizations... {start}-{stop}")
        for loc in localizations:
            update = models.LocalizationUpdate(frame=loc.frame-1)
            api.update_localization(id=loc.id, localization_update=update)
            count -= 1

        start += batch_size
        stop = start + batch_size

print("Done!")