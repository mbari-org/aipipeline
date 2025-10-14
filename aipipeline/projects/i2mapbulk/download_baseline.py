import tator
import os
import pandas as pd

project_id = 1  # i2map project in the database (i2map.shore.mbari.org)
version_id = 1  # Version ID to download localizations for
box_type = 5  # Box type ID for i2map localizations (e.g., 18 for bounding boxes)
image_type = 3  # Media type ID for images (e.g., 4 for images)
# Connect to Tator
token = os.getenv("TATOR_TOKEN")
api = tator.get_api(host='http://i2map.shore.mbari.org', token=token)

count = api.get_localization_count(project=project_id, type=box_type, version=[f"{version_id}"])

print(f"Found: {count} localizations for version {version_id}")
locs_list = []
if count > 0:
    # Download in batches
    batch_size = 1000
    start = 0
    stop = batch_size
    while count > 0:
        locs = api.get_localization_list(project=project_id, type=box_type, version=[version_id], start=start, stop=stop)
        if locs:
            locs_list.extend([loc.to_dict() for loc in locs])
        print(f"Downloaded {len(locs) if locs is not None else 0} localizations in current batch.")
        start = stop
        stop += batch_size
        count -= len(locs)

df = pd.DataFrame.from_records(locs_list) if locs_list else pd.DataFrame()

media_count = api.get_media_count(project=project_id, type=image_type)
medias_list = []
if media_count > 0:
    # Download in batches
    batch_size = 1000
    start = 0
    stop = batch_size
    while media_count > 0:
        medias = api.get_media_list(project=project_id, type=image_type, start=start, stop=stop)
        if medias:
            medias_list.extend([media.to_dict() for media in medias])
        print(f"Downloaded {len(medias) if medias is not None else 0} media in current batch.")
        start = stop
        stop += batch_size
        media_count -= len(medias)

media_df = pd.DataFrame.from_records(medias_list) if medias_list else pd.DataFrame()

# Merge the media names into the localization dataframe on media_id as needed for image_path in SDCAT format
if not df.empty and not media_df.empty:
    df = df.merge(media_df[['id', 'name']], left_on='media', right_on='id', suffixes=('', '_media'))
    df = df.rename(columns={'name': 'image_path'})
    df = df.drop(columns=['id_media'])

# Save to CSV
df.to_csv(f"tator_i2mapbulk_baseline.csv", index=False)
