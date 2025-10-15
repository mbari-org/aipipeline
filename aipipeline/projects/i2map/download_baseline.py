import tator
import os
import pandas as pd
import argparse
import logging

def main():
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Download baseline localizations from Tator")
    parser.add_argument("--project_id", type=int, required=True, help="Project ID in Tator")
    parser.add_argument("--box_type", type=int, required=True, help="Box type ID for localizations")
    parser.add_argument("--image_type", type=int, required=True, help="Image type ID for media")
    parser.add_argument("--output_csv", type=str, default="tator_i2mapbulk_baseline.csv", help="Output CSV file name")
    args = parser.parse_args()

    project_id = args.project_id  # i2map project in the database (i2map.shore.mbari.org)
    version_id = 3  # Version ID to download localizations
    box_type = args.box_type  # Box type ID for i2map localizations (e.g., 18 for bounding boxes)
    image_type = args.image_type  # Media type ID for images (e.g., 4 for images)
    output_csv = args.output_csv  # Output CSV file name
    # Connect to Tator
    token = os.getenv("TATOR_TOKEN")
    api = tator.get_api(host='https://mantis.shore.mbari.org', token=token)
    kwargs = {
        "version": [f"{version_id}"],
        "attribute": ["generator::vars-labelbot", "group::NMS"],
    }

    count = api.get_localization_count(project=project_id, type=box_type, **kwargs)

    logger.info(f"Found: {count} localizations for version {version_id}")
    locs_list = []
    if count > 0:
        # Download in batches
        batch_size = 1000
        start = 0
        stop = batch_size
        while count > 0:
            locs = api.get_localization_list(project=project_id, type=box_type, start=start, stop=stop, **kwargs)
            if locs:
                locs_list.extend([loc.to_dict() for loc in locs])
            logger.info(f"Downloaded {len(locs) if locs is not None else 0} localizations in current batch.")
            start = stop
            stop += batch_size
            count -= len(locs)
    else:
        logger.info("No localizations found.")
        return

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
            logger.info(f"Downloaded {len(medias) if medias is not None else 0} media in current batch.")
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
    df.to_csv(output_csv, index=False)
    logger.info(f"Saved {len(df)} localizations to {output_csv}")

if __name__ == "__main__":
    main()
