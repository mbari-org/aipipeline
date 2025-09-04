import os
from tator.openapi import tator_openapi

project_id = 4  # UAV project in the database (drone.mbari.org)
image_type = 7  # Image type id in the database
box_type = 4  # Box type id in the database
section_id = 279  # Section id in the database
host = 'drone.mbari.org'

# Connect to Tator
token = os.getenv("TATOR_TOKEN")
config = tator_openapi.Configuration()
config.host = host
config.verify_ssl = False  # Disable SSL verification
media_ids = []
if token:
    config.api_key['Authorization'] = token
    config.api_key_prefix['Authorization'] = 'Token'

api = tator_openapi.TatorApi(tator_openapi.ApiClient(config))

print("Getting media count")
media_count = api.get_media_count(project=project_id, section=section_id)
print(f"Found {media_count} media in section {section_id}")

if media_count == 0:
    print(f"No media found")
    exit(0)
#
batch_size = min(5000, media_count)
unique_media_names = []

print(f"Searching through {media_count} medias in section {section_id} ")
ids = []
for i in range(0, media_count, batch_size):
    media = api.get_media_list(project=project_id, section=section_id, start=i, stop=i + batch_size)
    ids += [m.id for m in media]

    if len(media) == 0:
        break

# Bulk delete media
batch_size = 200
for i in range(0, len(ids), batch_size):
    deleted = api.delete_media_list(project=project_id, media_id=ids[i: i + batch_size])
    print(deleted)

print(f"Deleted {len(ids)} media")