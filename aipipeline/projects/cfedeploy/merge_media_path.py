import csv
from pathlib import Path

INPUT_CSV = "/mnt/ML_SCRATCH/isiis/cfe_isiis_dino_v7-20250916/localizations_aidata.csv"
MEDIA_BASE_DIR = "/mnt/CFElab//Data_archive/Images/ISIIS/COOK/VideosMP4_v2/20240206_RachelCarson/"
OUTPUT_CSV = "/mnt/ML_SCRATCH/isiis/cfe_isiis_dino_v7-20250916/localizations.csv"


def main():
    # Read all media files in base directory first
    media_files = {}  # exact filename
    media_files_basename = {}  # basename without extension
    media_files_lower = {}  # case-insensitive lookup
    base_path = Path(MEDIA_BASE_DIR)

    print(f"Scanning media files in: {MEDIA_BASE_DIR}")
    for media_file in base_path.rglob('*.mp4'):
        if media_file.is_file():
            full_name = media_file.name
            basename = media_file.stem  # filename without extension
            full_path = str(media_file.absolute())
            
            # Store with different keys for flexible matching
            media_files[full_name] = full_path
            media_files_basename[basename] = full_path
            media_files_lower[full_name.lower()] = full_path
            media_files_lower[basename.lower()] = full_path

    print(f"Found {len(media_files)} media files")

    # Process CSV
    with open(INPUT_CSV, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        rows = list(reader)

        # Add path column to fieldnames
        fieldnames = reader.fieldnames
        if 'media' in fieldnames:
            # Insert 'path' right after 'media'
            media_idx = fieldnames.index('media')
            new_fieldnames = (fieldnames[:media_idx + 1] +
                              ['path'] +
                              fieldnames[media_idx + 1:])
        else:
            new_fieldnames = ['path'] + fieldnames

        # Track unique media names and match statistics
        unique_media_names = set()
        match_types = {'exact': 0, 'basename': 0, 'case_insensitive': 0, 'not_found': 0}

        # Add paths to each row
        for row in rows:
            media_name = row['media']
            unique_media_names.add(media_name)
            matched = False
            
            # Try exact match first (fastest)
            if media_name in media_files:
                row['path'] = media_files[media_name]
                match_types['exact'] += 1
                matched = True
            
            # Try basename match (without extension)
            elif media_name in media_files_basename:
                row['path'] = media_files_basename[media_name]
                match_types['basename'] += 1
                matched = True
            
            # Try basename of media_name (if it has extension)
            if not matched:
                media_basename = Path(media_name).stem
                if media_basename in media_files_basename:
                    row['path'] = media_files_basename[media_basename]
                    match_types['basename'] += 1
                    matched = True
            
            # Try case-insensitive match
            if not matched:
                if media_name.lower() in media_files_lower:
                    row['path'] = media_files_lower[media_name.lower()]
                    match_types['case_insensitive'] += 1
                    matched = True
            
            # Mark as not found
            if not matched:
                row['path'] = "NOT_FOUND"
                match_types['not_found'] += 1

    # Write output
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=new_fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nProcessed {len(rows)} rows from {INPUT_CSV}")
    print(f"Output saved to: {OUTPUT_CSV}")

    # Show detailed statistics
    found_count = sum(1 for row in rows if row['path'] != "NOT_FOUND")
    print(f"\n📊 Matching Statistics:")
    print(f"  Total CSV rows: {len(rows)}")
    print(f"  Unique media names in CSV: {len(unique_media_names)}")
    print(f"  Media files found on disk: {len(media_files)}")
    print(f"\n  Match Results:")
    print(f"    Exact matches: {match_types['exact']}")
    print(f"    Basename matches: {match_types['basename']}")
    print(f"    Case-insensitive matches: {match_types['case_insensitive']}")
    print(f"    Not found: {match_types['not_found']}")
    print(f"\n  Success rate: {found_count}/{len(rows)} ({100*found_count/len(rows):.1f}%)")
    
    # Show examples of unmatched names
    if match_types['not_found'] > 0:
        unmatched_examples = []
        for row in rows:
            if row['path'] == "NOT_FOUND":
                unmatched_examples.append(row['media'])
                if len(unmatched_examples) >= 10:
                    break
        
        print(f"\n⚠ Examples of unmatched media names:")
        for example in unmatched_examples:
            print(f"    {example}")
        
        # Show available files for comparison
        print(f"\n📁 Sample of available files on disk:")
        for i, filename in enumerate(sorted(media_files.keys())[:10]):
            print(f"    {filename}")
        
        # Save unmatched names to a file for analysis
        unmatched_file = OUTPUT_CSV.replace('.csv', '_unmatched_media.txt')
        unmatched_media = sorted(set(row['media'] for row in rows if row['path'] == "NOT_FOUND"))
        with open(unmatched_file, 'w') as f:
            f.write(f"Unmatched media names ({len(unmatched_media)} unique):\n")
            f.write("=" * 60 + "\n")
            for name in unmatched_media:
                f.write(f"{name}\n")
        print(f"\n💾 Full list of unmatched media names saved to: {unmatched_file}")


if __name__ == "__main__":
    print(f"Current input CSV: {INPUT_CSV}")
    print(f"Current media directory: {MEDIA_BASE_DIR}")
    main()