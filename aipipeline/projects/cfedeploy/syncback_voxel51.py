import tator
import os
from pandas import read_csv


token = os.getenv("TATOR_TOKEN")
api = tator.get_api(host='https://mantis.shore.mbari.org', token=token)


raw_data="aipipeline/projects/cfedeploy/data/rc_2024_02_cfe_isiis_dino_v7-20250916.csv"
voxel_data="/mnt/CFElab/Data_analysis/ISIIS/Voxel51/ood_remap_risk.csv"

df_raw = read_csv(raw_data)
df_voxel = read_csv(voxel_data)

print(f"Found {len(df_raw)} raw localizations")
print(f"Found {len(df_voxel)} voxel51 localizations")

# Rename elemental_id to uuid and merge the two dataframes on uuid
df_raw = df_raw.rename(columns={'elemental_id': 'uuid'})
df_voxel = df_voxel.merge(df_raw, on='uuid', how='left')

print(f"Found {len(df_voxel)} merged localizations")
print(df_voxel.head())

# Drop any unmatched row where label_y is null
df_voxel = df_voxel.dropna(subset=['label_y'])

# Find where the ground_truth.label does not match label
to_update = df_voxel[df_voxel['ground_truth.label'] != df_voxel['label_y']]
print(f"Found {len(to_update)} localizations to update")

for index, row in df_voxel.iterrows():
    params = {
        "attributes": {"Label": row['ground_truth.label'], "anomaly_score": float(row["risk_score_0.3"]), "verified": True}
    }
    print(f"Updating localization {row['uuid']} with {params}")
    loc=api.get_localization_list(version=[67], elemental_id=row['uuid'], project=14)
    if len(loc) != 1:
        print(f"ERROR: Cannot find localization for {row['uuid']}")
        continue
    print(f'Updating {loc[0].id} with elemental_id {row["uuid"]} to {row["ground_truth.label"]}')
    api.update_localization(loc[0].id, localization_update=params)