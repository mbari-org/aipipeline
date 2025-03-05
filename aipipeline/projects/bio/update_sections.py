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
        if ".mp4" not in media.name:
            section = media.attributes['tator_user_sections']
            print(f"Add {media.name} to section {section} ")
            media_update = tator.models.MediaUpdate(attributes={"tator_user_sections": section})
            api.update_media(media.id, media_update)
print("Done")