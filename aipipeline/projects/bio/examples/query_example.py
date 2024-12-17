import tator
import os

kwargs = {}
project = 3  # 901103-biodiversity project in the database (mantis.shore.mbari.org)
# Connect to Tator
token = os.getenv("TATOR_TOKEN")
api = tator.get_api(host='http://mantis.shore.mbari.org', token=token)

# Search for all video and localizations in the project
attribute_video = ["$type::49"] # 49 is the video type id
attribute_version = ["$version::26"] # 26 is the version id for the ctenophora-sp-a-yv5-vss version
kwargs["related_attribute"] = attribute_video
kwargs["attribute"] = attribute_version
localizations = api.get_localization_list(project=project, **kwargs)
print(f"Found {len(localizations)} possible Ctenophora sp. A")

# Save to a tsv file
with open("../data/localizations.tsv", "w") as f:
    f.write("database_id\tdive\tiso_datetime\tdepth\tlatitude\tlongitude\ttemperature\toxygen\tx\ty\twidth\theight\tscore\n")

    for loc in localizations:
        f.write(f"{loc.id}"
                f"\t{loc.attributes['dive']}"
                f"\t{loc.attributes['iso_datetime']}"
                f"\t{loc.attributes['depth']}"
                f"\t{loc.attributes['latitude']}"
                f"\t{loc.attributes['longitude']}"
                f"\t{loc.attributes['temperature']}"
                f"\t{loc.attributes['oxygen']}"
                f"\t{loc.x}"
                f"\t{loc.y}"
                f"\t{loc.width}"
                f"\t{loc.height}"
                f"\t{loc.attributes['score']}\n")