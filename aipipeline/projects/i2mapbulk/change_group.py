import tator

kwargs = {}
project = 1  # project in the database
box_type = 5  # box type in the database

# Connect to Tator
api = tator.get_api(host='http://i2map.shore.mbari.org', token='20551a9e486809901675a33774e5bac6e61d3d03')

# Bulk change all boxes with attribute GROUP=MERGE_CLASSIFY to GROUP=NMS
attribute_localization = ["$group::MERGE_CLASSIFY"]

kwargs["attribute_contains"] = attribute_localization

localizations = api.get_localization_list(project=project, **kwargs)
print(f"Found {len(localizations)} localizations.")

# Bulk change all boxes with attribute GROUP=MERGE_CLASSIFY to GROUP=NMS
chunk_size = min(200, len(localizations))

# Bulk update boxes by IDs, set verified to True
params = {"type": box_type}
id_bulk_patch = {
    "attributes": {"group": "NMS"},
    "ids": [l.id for l in localizations],
    "in_place": 1,
}
response = api.update_localization_list(project=project, **params, localization_bulk_update=id_bulk_patch)