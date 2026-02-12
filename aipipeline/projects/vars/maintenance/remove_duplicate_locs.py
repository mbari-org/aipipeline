#!/usr/bin/env python3
import os
import argparse
import logging
import csv
from pathlib import Path
import tator

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def remove_duplicate_locs(csv_path: Path, project_id: int, host: str, token: str, dry_run: bool = False):
    """
    Reads a CSV file, finds duplicate localizations based on media ID and coordinates,
    and removes all duplicates except the first one from Tator.
    """
    if not csv_path.is_file():
        logger.error(f"{csv_path} is not a file.")
        return

    logger.info(f"Reading CSV file: {csv_path}")

    # Track seen localizations to find duplicates
    # Key: (media_id, x, y, width, height)
    seen = {}
    uuids_to_remove = []

    try:
        with open(csv_path, mode='r', newline='') as csvfile:
            csvfile.seek(0)
            reader = csv.DictReader(csvfile)
            
            # Map the columns as per the new header
            # (media) $id, $elemental_id, $x_pixels, $y_pixels, $width_pixels, $height_pixels
            col_media_id = '(media) $id'
            col_uuid = '$elemental_id'
            col_x = '$x_pixels'
            col_y = '$y_pixels'
            col_w = '$width_pixels'
            col_h = '$height_pixels'

            for row in reader:
                media_id = row.get(col_media_id, '').strip()
                elemental_id = row.get(col_uuid, '').strip()
                x = row.get(col_x, '').strip()
                y = row.get(col_y, '').strip()
                w = row.get(col_w, '').strip()
                h = row.get(col_h, '').strip()

                if not all([media_id, elemental_id, x, y, w, h]):
                    continue

                key = (media_id, x, y, w, h)

                if key in seen:
                    uuids_to_remove.append(elemental_id)
                else:
                    seen[key] = elemental_id
    except Exception as e:
        logger.error(f"Failed to read CSV file: {e}")
        return

    logger.info(f"Found {len(uuids_to_remove)} duplicate UUIDs to remove.")

    if not uuids_to_remove:
        logger.info("No duplicates found.")
        return

    if dry_run:
        logger.info(f"Dry run: would remove {len(uuids_to_remove)} localizations from project {project_id}.")
        for uuid in uuids_to_remove[:10]:
            logger.info(f"  Would remove UUID: {uuid}")
        if len(uuids_to_remove) > 10:
            logger.info(f"  ... and {len(uuids_to_remove) - 10} more.")
        return

    # Connect to Tator
    try:
        api = tator.get_api(host=host, token=token)
        logger.info(f"Connected to Tator at {host}")
    except Exception as e:
        logger.error(f"Failed to connect to Tator: {e}")
        return

    for uuid in uuids_to_remove:

        try:
            print(f"Removing localization with UUID: {uuid}")
            response = api.delete_localization_list(project=project_id, elemental_id=uuid)
            logger.info(f"Tator response: {response.message}")
        except Exception as e:
            logger.error(f"Error deleting {uuid}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remove duplicate localizations from Tator based on a CSV file.")
    parser.add_argument("csv_path", type=str, help="CSV file containing localization data.")
    parser.add_argument("--project-id", type=int, default=15, help="Tator project ID (default: 15).")
    parser.add_argument("--host", type=str, default='http://mantis.shore.mbari.org', help="Tator host (default: http://mantis.shore.mbari.org).")
    parser.add_argument("--dry-run", action="store_true", help="Only scan and log UUIDs without deleting.")
    
    args = parser.parse_args()
    
    token = os.getenv("TATOR_TOKEN")
    if not token:
        logger.error("TATOR_TOKEN environment variable not set.")
        exit(1)
        
    remove_duplicate_locs(Path(args.csv_path), args.project_id, args.host, token, args.dry_run)
