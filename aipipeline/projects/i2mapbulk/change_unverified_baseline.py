import os
import tator

kwargs = {}
project = 1  # project in the database
box_type = 5  # box type in the database
version = 1

# Connect to Tator
token = os.getenv("TATOR_TOKEN")
api = tator.get_api(host='http://i2map.shore.mbari.org', token=token)

# Bulk change all boxes with attribute verified=False to Label=Unknown, score=0.0

kwargs["attribute"] = ["verified::False"]
kwargs["version"] = [f"{version}"]

count = api.get_localization_count(project=project, type=box_type, **kwargs)
print(f"Found {count} localizations to update.")
if count == 0:
    exit(0)

# Run in chunks of 500
for start in range(0, count, 500):
    stop = min(start + 500, count)
    print(f"Processing localizations {start} to {stop}")
    kwargs["start"] = start
    kwargs["stop"] = stop
     # Get the localizations to update
    localizations = api.get_localization_list(project=project, **kwargs)
    print(f"Found {len(localizations)} localizations.")

    # Bulk update boxes by IDs, set verified to True
    params = {"type": box_type}
    id_bulk_patch = {
        "attributes": {"score": 0.0},
        "label": "Unknown",
        "ids": [l.id for l in localizations],
        "in_place": 1,
    }
    response = api.update_localization_list(project=project, **params, localization_bulk_update=id_bulk_patch)
    print(f"Updated {len(localizations)} localizations.")
    uuids = [ l.elemental_id for l in localizations ]
    print(f"Updated UUIDs: {uuids}")
print("Done.")