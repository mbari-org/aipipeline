import tator
import os


# All medias a simple text file with full path to medias
all_media = "delme"

# Read all lines from the file
all_medias = open(all_media, "r").readlines()

# Get the name, e.g. from /mnt/DeepSea-AI/data/M3/images/a0cdc872-8240-4abd-95a2-13988d35dde3.png
# a0cdc872-8240-4abd-95a2-13988d35dde3.png
medias_to_load = [os.path.basename(line.strip()) for line in all_medias]

# To remove - one line per media name
to_remove = "medias.txt"
loaded_medias = open(to_remove, "w").readlines()

# Make a new list of those medias_to_load not in loaded_medias
to_load = list(set(medias_to_load) - set(loaded_medias))

print(f"Found {len(loaded_medias)} medias already loaded.")
print(f"Found {len(to_remove)} medias to remove.")
print(f"Found {len(to_load)} medias to load.")

kwargs = {}
project = 3  # 901103-biodiversity project in the database (mantis.shore.mbari.org)
# Connect to Tator
token = os.getenv("TATOR_TOKEN")
api = tator.get_api(host='http://mantis.shore.mbari.org', token=token)

# Search for all video and localizations in the project
# attribute_image = ["$type::5"] # 49 is the image type id
kwargs["type"] = 5
medias = api.get_media_list(project=project, **kwargs)
print(f"Found {len(medias)} in version 5")

# Save to a csv file
with open("medias.txt", "w") as f:
    f.write("id,name\n")
    for media in medias:
        f.write(f"{media.name}\n")