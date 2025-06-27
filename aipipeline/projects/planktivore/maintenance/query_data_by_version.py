import pandas as pd
import tator
import os

project_id = 12  # planktivore project in the database
version_id = 61  # Version ID to query localizations for
box_loc_type = 17  # Box type ID for planktivore localizations (e.g., 17 for bounding boxes)

# Connect to Tator
token = os.getenv("TATOR_TOKEN")
api = tator.get_api(host='https://mantis.shore.mbari.org', token=token)

# Get the localization count for the specified version
count = api.get_localization_count(project=project_id, type=box_loc_type, version=[f"{version_id}"])
print(f"Found: {count} localizations for version {version_id}")

if count == 0:
    print(f"No localizations found for version {version_id}. Exiting.")
    exit(0)

# If there are localizations, retrieve them and put them into a panda DataFrame
df = pd.DataFrame()
if count > 0:
    kwargs = {}
    kwargs["version"] = [f"{version_id}"]

    # Retrieve localizations in batches of 2000
    batch_size = 2000
    if count < batch_size:
        batch_size = count

    kwargs["start"] = 0
    kwargs["stop"] = batch_size

    for i in range(0, count, batch_size):
        kwargs["start"] = i
        kwargs["stop"] = min(i + batch_size, count)

        # Get the localizations for the current batch
        print(f"Retrieving localizations for version {version_id}, batch {i // batch_size + 1}")
        localizations = api.get_localization_list(project=project_id, type=box_loc_type, **kwargs)

        # Append each localization to the DataFrame
        for loc in localizations:
            loc_dict = loc.to_dict()
            loc_dict['version'] = version_id
            df_loc = pd.DataFrame(loc_dict['attributes'], index=[0])
            df = pd.concat([df, df_loc], ignore_index=True)

    print(f"Total localizations retrieved: {len(df)}")
    print(df.head())

    output_file = f"localizations_version_{version_id}.csv"
    df.to_csv(output_file, index=False)
    print(f"Localizations saved to {output_file}")

    # Get the unique cluster names from the DataFrame
    unique_clusters = df['cluster'].unique()

    # Summarize totals in each cluster, sorted by count
    cluster_group = df.groupby('cluster').size().reset_index(name='count')
    cluster_group = cluster_group.sort_values(by='count', ascending=False)
    print("Cluster summary:")
    print(cluster_group)
    # Save the cluster summary to a CSV file
    cluster_summary_file = f"cluster_summary_version_{version_id}.csv"
    cluster_group.to_csv(cluster_summary_file, index=False)

