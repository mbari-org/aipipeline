import tator
import os

project_id = 12  # planktivore project in the database (mantis.shore.mbari.org)
image_type = 55  # Image type id in the database
box_type = 17  # Box type id in the database
# Connect to Tator
token = os.getenv("TATOR_TOKEN")
api = tator.get_api(host='http://mantis.shore.mbari.org', token=token)
media_ids = []

media_count = api.get_media_count(project=project_id, type=image_type)

if media_count == 0:
    print(f"No media found")
    exit(0)

batch_size = min(5000, media_count)
unique_media_names = []

print(f"Searching through {media_count} medias ")
ids = []
for i in range(0, media_count, batch_size):
    media = api.get_media_list(project=project_id, start=i, stop=i + batch_size)
    ids += [m.id for m in media]

    if len(media) == 0:
        break

# Bulk delete media
batch_size = 200
for i in range(0, len(ids), batch_size):
    deleted = api.delete_media_list(project=project_id, media_id=ids[i: i + batch_size])
    print(deleted)

print(f"Deleted {len(ids)} media")