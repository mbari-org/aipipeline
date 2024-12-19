import tator
import os

project_id = 1  # i2map project in the database (i2map.shore.mbari.org)
image_type = 3  # Image type id in the database
box_type = 5  # Box type id in the database
# Connect to Tator
token = os.getenv("TATOR_TOKEN")
api = tator.get_api(host='http://i2map.shore.mbari.org', token=token)
media_ids = []

media_count = api.get_media_count(project=project_id, type=image_type)

if media_count == 0:
    print(f"No media found")
    exit(0)

batch_size = min(5000, media_count)
kwargs = {}
kwargs["attribute"] = ["depth::300"]
print(f"Searching through {media_count} medias with {kwargs}")
for i in range(0, media_count, batch_size):
    media = api.get_media_list(project=project_id, start=i, stop=i + batch_size, **kwargs)
    print(f"Found {len(media)} media with depth 300")
    if len(media) == 0:
        break
    media_ids.extend([m.id for m in media])

print(f"Found {len(media_ids)} media with depth 300")

# Delete localizations in batches of 100
batch_size = 500
for i in range(0, len(media_ids), batch_size):
    deleted = api.delete_localization_list(
        project=project_id,
        media_id=media_ids[i: i + batch_size],
        type=box_type,
        **kwargs
    )
    print(deleted)