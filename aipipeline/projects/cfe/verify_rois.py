import os
import tator

# Connect to Tator
api = tator.get_api(host='http://mantis.shore.mbari.org', token=os.environ['TATOR_TOKEN'])

project_id = 10  # cfe project in the database
batch_size = 200
box_type = 14
attribute_filter = ["Label::bloom","verified::False"]
num_locs = api.get_localization_count(project=project_id, type=14, attribute=attribute_filter)
print(f"Found {num_locs} localizations to verify")

for i in range(0, num_locs, batch_size):
    print(f"Verifying localizations {i} to {i + batch_size}")
    localizations = api.get_localization_list(project=project_id, type=box_type, attribute=attribute_filter, start=i, stop=i+batch_size)
    # Bulk update boxes by IDs, set verified to True
    params = {"type": box_type}
    id_bulk_patch = {
        "attributes": {"verified": "True"},
        "ids": [l.id for l in localizations],
        "in_place": 1,
    }
    response = api.update_localization_list(project=project_id, **params, localization_bulk_update=id_bulk_patch)
    print(response)