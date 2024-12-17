import tator
import pandas as pd

kwargs = {}
project = 3  # 901103-biodiversity project in the database (mantis.shore.mbari.org)
# Connect to Tator
token = "ae84628927851c1a545c375ea8e4c3da2a022400"
api = tator.get_api(host='http://mantis.shore.mbari.org', token=token)

# Search for all video and localizations in the project
attribute_video = ["$type::49"] # 49 is the video type id
attribute_version = ["$version::33"] # 33 is the version id for megadet-vits-track version
kwargs["related_attribute"] = attribute_video
kwargs["attribute"] = attribute_version
localizations = api.get_localization_list(project=project, **kwargs)
print(f"Found {len(localizations)} in version megadet-vits-track")

# Load the localizations into a pandas dataframe
df = pd.DataFrame([loc.attributes for loc in localizations])

# Get the top 20 labels and print the average depth
top_20 = df['Label'].value_counts().head(20)
print("Top 20 labels:")
print("Label, Localizations, Average Depth")
for s in top_20.index:
    print(f"{s}\t{top_20[s]}\t{df[df['Label'] == s]['depth'].mean():.2f}")

