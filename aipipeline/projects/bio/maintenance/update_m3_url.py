import os

import tator

project_id = 3  # biodiversity project in the database

# Connect to Tator
api = tator.get_api(host='http://mantis.shore.mbari.org', token=os.environ['TATOR_TOKEN'])

# Get media count from source section
media_count = api.get_media_count(project=project_id)

batch_size = 100

for media_batch in range(0, media_count, batch_size):
    response = api.get_media_list(project=project_id, start=media_batch, stop=media_batch + batch_size)
    for media in response:
        if '.mp4' not in media.name:
            continue
        media_files = media
        try:
            if media_files is None or media_files.media_files.streaming is None:
                continue
            media_url = media_files.media_files.streaming[0].path
            if media_url.startswith("http://m3.shore.mbari.org/") or media_url.startswith("https://m3.shore.mbari.org/"):
                print(f"Replacing {media_url} with")
                media_url = media_url.replace('http://m3.shore.mbari.org/videos/M3/', 'http://mantis.shore.mbari.org/M3/')
                media_url = media_url.replace('https://m3.shore.mbari.org/videos/M3/', 'http://mantis.shore.mbari.org/M3/')
                media_files.media_files.streaming[0].path = media_url
                media_files.media_files.streaming[0].bit_rate = 22000
                u = tator.models.MediaUpdate(media_files={"streaming": media_files.media_files.streaming})
                api.update_media(media.id, media_update=u)
        except Exception as e:
            print(f"Error updating media {media.id}: {e}")
print("Done")