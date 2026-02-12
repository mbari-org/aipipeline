#!/usr/bin/env python3
import os
import argparse
import logging
from pathlib import Path
from cleanvision import Imagelab

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def remove_duplicates(input_path: Path, output_log: Path, dry_run: bool = False):
    """
    Finds and removes duplicate images using cleanvision.
    Keeps one from each set of duplicates and logs removed paths.
    """
    if not input_path.is_dir():
        logger.error(f"{input_path} is not a directory.")
        return

    logger.info(f"Scanning for duplicates in: {input_path}")
    
    # Initialize Imagelab
    # data_path will recursively find images in the directory
    imagelab = Imagelab(data_path=str(input_path))
    
    # Find duplicates
    imagelab.find_issues(issue_types={"near_duplicates": {}, "exact_duplicates": {}})
    
    removed_paths = set()
    
    for issue_type in ["near_duplicates", "exact_duplicates"]:
        if issue_type in imagelab.info and imagelab.info[issue_type]["sets"]:
            dup_sets = imagelab.info[issue_type]["sets"]
            
            for dup_set in dup_sets:
                if len(dup_set) <= 1:
                    continue
                
                # Keep one image from the set, mark others for removal.
                # Sorting ensures deterministic behavior.
                sorted_paths = sorted(dup_set)
                keep_path = sorted_paths[0]
                to_remove = sorted_paths[1:]
                
                logger.info(f"Issue type {issue_type} - Keeping: {keep_path}")
                for path in to_remove:
                    removed_paths.add(path)
                    logger.info(f"Marked for removal: {path}")
    
    if not removed_paths:
        logger.info("No duplicates found.")

    # Convert to sorted list for consistent log file output
    sorted_removed_paths = sorted(list(removed_paths))

    # Save removed paths to .txt file
    try:
        with open(output_log, "w") as f:
            for path in sorted_removed_paths:
                f.write(f"{path}\n")
        logger.info(f"Saved {len(sorted_removed_paths)} removed paths to {output_log}")
    except Exception as e:
        logger.error(f"Failed to write log file {output_log}: {e}")

    # Perform actual removal
    if sorted_removed_paths:
        if not dry_run:
            count = 0
            for path in sorted_removed_paths:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                        count += 1
                    else:
                        logger.warning(f"File not found for removal: {path}")
                except Exception as e:
                    logger.error(f"Error removing {path}: {e}")
            logger.info(f"Successfully removed {count} files from disk.")
        else:
            logger.info(f"Dry run enabled. Would have removed {len(sorted_removed_paths)} files.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remove duplicate images using cleanvision.")
    parser.add_argument("input_path", type=str, help="Directory containing images to check.")
    parser.add_argument("output_log", type=str, help="File to save the paths of removed duplicates.")
    parser.add_argument("--dry-run", action="store_true", help="Only log duplicates without deleting them.")
    
    args = parser.parse_args()
    
    remove_duplicates(Path(args.input_path), Path(args.output_log), args.dry_run)
