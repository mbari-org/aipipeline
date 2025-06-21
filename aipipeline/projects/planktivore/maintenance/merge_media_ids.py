# This script add the Tator media IDs to the cluster detections CSV file for the Planktivore project.
import os
import pandas as pd

pd_media = pd.read_csv('/Users/dcline/Dropbox/data/planktivore/tator_data_ptvr_unverified_high_mag_2025_06_01.csv')
pd_clusters = pd.read_csv('/Volumes/DeepSea-AI/data/Planktivore/cluster_iter1/cluster/_mnt_DeepSea-AI_models_Planktivore_mbari-ptvr-vits-b8-20250513_20250526_130025_cluster_detections.csv')

# Create a new column in pd_media with the filename without the full path
pd_clusters['$name'] = pd_clusters['image_path'].apply(lambda x: os.path.basename(x))

# Merge the two dataframes on the $name column
merged_df = pd.merge(pd_media, pd_clusters, on='$name', how='inner')

# Drop the image_path_x column
merged_df = merged_df.drop(columns=['image_path'])

# rename the $id column to id as required by aidata
merged_df = merged_df.rename(columns={'$id': 'id'})

# Save the merged dataframe to a new CSV file
output_path = '/Volumes/DeepSea-AI/data/Planktivore/cluster_iter1/cluster/_mnt_DeepSea-AI_models_Planktivore_mbari-ptvr-vits-b8-20250513_20250526_130025_cluster_detections_with_id.csv'
merged_df.to_csv(output_path, index=False)
