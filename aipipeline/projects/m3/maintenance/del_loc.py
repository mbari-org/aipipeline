import os

import tator
import os

kwargs = {}
project_id = 15  # project in the database
version_id = 76  # version in the database

# Connect to Tator
token = os.getenv("TATOR_TOKEN")
api = tator.get_api(host='http://mantis.shore.mbari.org', token=token)

# Get all localizations
kwargs["type"] = 20
count = api.get_localization_count(project=project_id, **kwargs)
print(f"Found {count} localizations in project {project_id}")

for i in range(0, count, 1000):
    print(f"Deleting localizations {i} to {i + 1000}")
    response = api.delete_localization_list(project=project_id, start=i, stop=i + 1000)
    print(response)