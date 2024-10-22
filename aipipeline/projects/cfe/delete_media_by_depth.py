import tator
import os

kwargs = {}
project = 10  # cfe project in the database
TATOR_TOKEN = os.getenv("TATOR_TOKEN")

# Connect to Tator
api = tator.get_api(host='http://mantis.shore.mbari.org', token=TATOR_TOKEN)

# Search for media with a depth less than 50 m
attribute_media = ["$depth::50"]
kwargs["attribute_lt"] = attribute_media
medias = api.get_media_list(project=project, **kwargs)
print(f"Found {len(medias)} media.")

num_boxes = 0
for media in medias:
    print(f"Media {media.id}: {media.name}")
    # Get the number of boxes in this media
    boxes = api.get_localization_list(project=project, media_id=[media.id])
    num_boxes += len(boxes)
    # Delete the media
    # response = api.delete_media(id=media.id)
    # print(f"  Deleted media {media.id}. {response}")


print(f"Deleted {len(medias)} media with a total of {num_boxes} boxes.")