import os

import tator
import os

kwargs = {}
project = 1  # project in the database

# Connect to Tator
token = os.getenv("TATOR_TOKEN")
api = tator.get_api(host='http://i2map.shore.mbari.org', token=token)

# Search for media with a depth less than 50 m
attribute_media = ["$depth::300"]
kwargs["attribute_contains"] = attribute_media
medias = api.get_media_list(project=project, **kwargs)
print(f"Found {len(medias)} media.")

num_boxes = 0
for media in medias:
    print(f"Media {media.id}: {media.name}")
    # Get the number of boxes in this media
    boxes = api.get_localization_list(project=project, media_id=[media.id])
    print(f"  Found {len(boxes)} boxes.")
    # Remove any boxes that are close to the edge of the image
    threshold = 0.01  # 1% threshold
    for box in boxes:
        x = box.x
        y = box.y
        xx = box.x + box.width
        yy = box.y + box.height
        if (0 <= x <= threshold or 1 - threshold <= x <= 1) or \
            (0 <= y <= threshold or 1 - threshold <= y <= 1) or \
            (0 <= xx <= threshold or 1 - threshold <= xx <= 1) or \
            (0 <= yy <= threshold or 1 - threshold <= yy <= 1):
                print(f"  Found edge box {box.id}.")
                # Delete the box
                response = api.delete_localization(id=box.id)
                print(f"  Deleted box {box.id}. {response}")
                num_boxes -= 1


print(f"Deleted {num_boxes} boxes.")