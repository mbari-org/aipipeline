from pathlib import Path
import pandas as pd

this_dir =  Path(__file__).resolve().parent
data_dir = this_dir
roi_parquet_files = data_dir.glob("*_below_euphotic.parquet")

# Create a .txt file with all the file paths
with open(data_dir / "below_euphotic_files.txt", "w") as f:
    for pq_file in roi_parquet_files:
        print(f"Processing {pq_file}")
        df = pd.read_parquet(pq_file)
        # Filter out rows where 'file' column is NaN
        df = df[df['filename'].notna()]
        # Extract the 'file' column and convert to a list
        file_list = df['filename'].tolist()
        # Extract the month and year from the directory structure
        # Assuming format is like 'April_2024_Ahi_lowmag_level2_below_euphotic.parquet
        str_split = pq_file.name.split("_")
        season = str_split[0]
        year = str_split[1]
        for file_path in file_list:
            f.write(f"/mnt/DeepSea-AI/data/Planktivore/raw/{year}_{season}-Ahi-Planktivore/low_mag_cam/{file_path}\n")
        print(f"Wrote {len(file_list)} entries from {pq_file} to below_euphotic_files.txt")