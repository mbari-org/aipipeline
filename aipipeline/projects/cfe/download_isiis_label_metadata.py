import tator
import os

kwargs = {}
project = 10  # 902111-CFE  project in the database (mantis.shore.mbari.org)
# Connect to Tator
token = os.getenv("TATOR_TOKEN")
api = tator.get_api(host='http://mantis.shore.mbari.org', token=token)

# Search for all verified media and localizations in the project
attribute_version = ["$version::10","verified::True"] # 10 is the version id for the Baseline
kwargs["attribute"] = attribute_version
localizations = api.get_localization_list(project=project, **kwargs)
print(f"Found {len(localizations)} verified labels")

# Get all the unique media ids
media_ids = set([loc.media for loc in localizations])
print(f"Found {len(media_ids)} unique media ids")

# Get all the media objects to get the depth, time, etc. in batches of 100
medias = []
for i in range(0, len(media_ids), 100):
    print(f"Fetching media {i} to {i+100}")
    m = api.get_media_list(project=project, media_id=list(media_ids)[i:i+100])
    print(f"Found {len(m)} media objects")
    medias.extend(m)
media_hash = {media.id: media for media in medias}

# Save to a tsv file
with open("isiis_labels.tsv", "w") as f:
    f.write("database_id\tiso_datetime\tdepth\tLabel\tx\ty\twidth\theight\tscore\n")

    for loc in localizations:
        # Get the media that is associated with the localization
        media = media_hash[loc.media]

        f.write(f"{loc.id}"
                f"\t{media.attributes['iso_datetime']}"
                f"\t{media.attributes['depth']}"
                f"\t{loc.attributes['Label']}"
                f"\t{loc.x}"
                f"\t{loc.y}"
                f"\t{loc.width}"
                f"\t{loc.height}"
                f"\t{loc.attributes['score']}\n")

print("Done")