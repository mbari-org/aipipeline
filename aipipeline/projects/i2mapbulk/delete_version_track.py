import tator
import os

project_id = 1  # i2mapbulk project in the database (i2map.shore.mbari.org)
media_type = 2  # video type id in the database
box_type = 5  # Box type id in the database
version_id = 13
track_type = 1 # State type for tracks

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

# Delete all the states in this version
state_count = api.get_state_count(project=project_id, version=[f"{version_id}"])
print(f"Found: {state_count} states for version {version_id}")
if state_count > 0:
    # Delete in batches
    batch_size = 1000
    while state_count > 0:
        deleted_states = api.delete_state_list(project=project_id, version=[version_id], start=0, stop=batch_size)
        print(f"Deleted {deleted_states if deleted_states is not None else 0} states in current batch.")
        state_count = api.get_state_count(project=project_id, version=[f"{version_id}"])
        if state_count == 0:
            print(f"All states for version {version_id} have been deleted.")
            break


state_count = api.get_state_count(project=project_id, type=track_type)
print(f"Found: {state_count} states for track type {track_type}")
if state_count > 0:
    # Delete in batches
    batch_size = 1000
    while state_count > 0:
        deleted_states = api.delete_state_list(project=project_id, type=track_type, start=0, stop=batch_size)
        print(f"Deleted {deleted_states if deleted_states is not None else 0} states in current batch.")
        state_count = api.get_state_count(project=project_id, type=track_type)
        if state_count == 0:
            print(f"All states for version {version_id} have been deleted.")
            break


# Delete the version itself
# api.delete_version(id=version_id)