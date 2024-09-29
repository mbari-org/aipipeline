import tator
import re
import os

kwargs = {}
project = 10  # cfe project in the database
TATOR_TOKEN = os.getenv("TATOR_TOKEN")

# 'CFE_ISIIS-010-2024-01-26 10-14-07.102_0835_8.3m.png'
pattern = re.compile(
    r"CFE_(.*?)-(\d+)-(\d{4}-\d{2}-\d{2} \d{2}-\d{2}-\d{2}\.\d{3})_(\d{4})_(\d+\.\d+)m\.(png|jpg|jpeg|JPEG|PNG)")

# Connect to Tator
api = tator.get_api(host='http://mantis.shore.mbari.org', token=TATOR_TOKEN)

# Search for media with a depth letter m in the name
attribute_media = ["$name::m"]
kwargs["attribute_contains"] = attribute_media
medias = api.get_media_list(project=project, **kwargs)
print(f"Found {len(medias)} media.")

media_ids = []
media_depths = []
for media in medias:
    print(f"Media {media.id}: {media.name}")
    # Parse out the depth from the media name and update the media
    matches = re.findall(pattern, media.name)
    if matches:
        instrument, _, datetime_str, frame_num, depth, ext = matches[0]
        print(f"  Instrument: {instrument} Depth: {depth}m")
        media_ids.append(media.id)
        media_depths.append(float(depth))
        m = tator.models.MediaUpdate(attributes={"depth": float(depth)})
        response = api.update_media(id=media.id, media_update=m)
        print(f"  Updated media {media.id} with depth {depth}m. {response}")