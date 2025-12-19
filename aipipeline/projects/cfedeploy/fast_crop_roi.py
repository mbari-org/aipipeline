import datetime
import os
import csv
import multiprocessing as mp
from datetime import datetime
import traceback
import sys
import cv2

INPUT_CSV = "/mnt/ML_SCRATCH/isiis/cfe_isiis_dino_v7-20250916/localizations.csv"
OUTPUT_DIR = "/mnt/ML_SCRATCH/isiis/cfe_isiis_dino_v7-20250916/crops"
MAX_WORKERS = max(1, os.cpu_count() - 1)  # Use all CPU cores minus 1
HEIGHT_PX = 2048
WIDTH_PX = 2048
RESCALE = 224  # Target size for rescaled crops

os.makedirs(OUTPUT_DIR, exist_ok=True)

def process_single_video(video_data, output_dir):
    """Process all crops for a single video file using OpenCV with sequential reading."""
    media_path, rows = video_data

    if not rows:
        return []

    total_crops = len(rows)
    successful = 0
    failed = 0
    skipped_existing = 0
    failure_reasons = {
        'empty_crop': 0,
        'write_failed': 0,
        'exception': 0,
        'beyond_video': 0,
        'video_ended_early': 0
    }

    try:
        # Group rows by frame for this video
        from collections import defaultdict
        frame_groups = defaultdict(list)

        for row in rows:
            frame = row.get('frame', '')
            frame_groups[frame].append(row)

        # Get sorted list of frame numbers we need
        frame_numbers = sorted([int(float(f)) for f in frame_groups.keys()])
        
        if not frame_numbers:
            print(f"[{os.path.basename(media_path)}] No valid frame numbers found")
            return {'video': media_path, 'successful': 0, 'failed': total_crops, 'total': total_crops}
        
        print(f"[{os.path.basename(media_path)}] Processing {total_crops} crops across {len(frame_numbers)} frames (frames {frame_numbers[0]}-{frame_numbers[-1]})")

        # Open video once with OpenCV
        cap = cv2.VideoCapture(media_path)
        
        if not cap.isOpened():
            print(f"[{os.path.basename(media_path)}] Failed to open video file")
            failure_reasons['exception'] = total_crops
            return {
                'video': media_path, 
                'successful': 0, 
                'failed': total_crops, 
                'total': total_crops,
                'skipped_existing': 0,
                'failure_reasons': failure_reasons
            }
        
        # Get video properties for diagnostics
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Check if requested frames are beyond video length
        if frame_numbers[-1] > total_frames:
            print(f"[{os.path.basename(media_path)}] WARNING: CSV requests frames up to {frame_numbers[-1]}, but video only has {total_frames} frames (FPS: {video_fps:.2f})")
            # Count crops that will be skipped
            frames_beyond = [f for f in frame_numbers if f > total_frames]
            crops_beyond = sum(len(frame_groups[str(f)]) for f in frames_beyond)
            
            # Filter to only frames that exist
            frame_numbers = [f for f in frame_numbers if f <= total_frames]
            
            if not frame_numbers:
                print(f"[{os.path.basename(media_path)}] All requested frames are beyond video length. Skipping {total_crops} crops.")
                failed = total_crops
                failure_reasons['beyond_video'] = total_crops
                cap.release()
                return {'video': media_path, 'successful': 0, 'failed': failed, 'total': total_crops, 'skipped_existing': 0, 'failure_reasons': failure_reasons}
            
            print(f"[{os.path.basename(media_path)}] Will skip {crops_beyond} crops from {len(frames_beyond)} frames beyond video length")
            failed += crops_beyond
            failure_reasons['beyond_video'] += crops_beyond

        # Pre-create all label directories to avoid overhead during processing
        label_dirs = set()
        for row in rows:
            label = row.get('Label') or row.get('label') or row.get('concept') or 'Unknown'
            safe_label = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in label)
            safe_label = safe_label.strip() or 'Unknown'
            label_dirs.add(safe_label)
        
        for safe_label in label_dirs:
            label_dir = os.path.join(output_dir, safe_label)
            os.makedirs(label_dir, exist_ok=True)

        # Read frames sequentially (more reliable than seeking)
        # Frame numbers in CSV appear to be 1-indexed, OpenCV frame counter is 0-indexed
        current_frame = 0
        frame_idx = 0  # Index into our frame_numbers list
        
        while frame_idx < len(frame_numbers):
            ret, frame_img = cap.read()
            
            if not ret or frame_img is None:
                # Failed to read more frames - video ended early
                remaining_frames = frame_numbers[frame_idx:]
                remaining_crops = sum(len(frame_groups[str(fn)]) for fn in remaining_frames)
                failed += remaining_crops
                failure_reasons['video_ended_early'] += remaining_crops
                print(f"[{os.path.basename(media_path)}] Video ended at frame {current_frame}. Could not process {remaining_crops} crops from frames {remaining_frames[0]}-{remaining_frames[-1]}")
                break
            
            current_frame += 1  # Now at frame 1, 2, 3, etc. (1-indexed to match CSV)
            
            # Check if this is a frame we need
            if current_frame == frame_numbers[frame_idx]:
                frame_str = str(frame_numbers[frame_idx])
                frame_rows = frame_groups[frame_str]
                
                # Process each crop in this frame
                for row in frame_rows:
                    try:
                        x = float(row['x'])
                        y = float(row['y'])
                        width = float(row['width'])
                        height = float(row['height'])
                        uuid = row['uuid']
                        label = row.get('Label') or row.get('label') or row.get('concept') or 'Unknown'
                        
                        # Sanitize label for filesystem
                        safe_label = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in label)
                        safe_label = safe_label.strip() or 'Unknown'

                        # Convert normalized coordinates to pixel coordinates
                        x1 = int(WIDTH_PX * x)
                        y1 = int(HEIGHT_PX * y)
                        x2 = int(WIDTH_PX * (x + width))
                        y2 = int(HEIGHT_PX * (y + height))

                        crop_w = x2 - x1
                        crop_h = y2 - y1

                        # Apply padding to make crop square
                        shorter_side = min(crop_h, crop_w)
                        longer_side = max(crop_h, crop_w)
                        delta = abs(longer_side - shorter_side)

                        padding = delta // 2
                        if crop_w == shorter_side:
                            x1 -= padding
                            x2 += padding
                        else:
                            y1 -= padding
                            y2 += padding

                        # Ensure crop area is within bounds
                        x1 = max(0, x1)
                        x2 = min(WIDTH_PX, x2)
                        y1 = max(0, y1)
                        y2 = min(HEIGHT_PX, y2)

                        # Create output path
                        label_dir = os.path.join(output_dir, safe_label)
                        output_path = os.path.join(label_dir, f"{uuid}.jpg")

                        # Skip if already exists
                        if os.path.exists(output_path):
                            successful += 1
                            skipped_existing += 1
                            continue

                        # Crop from frame (OpenCV uses [y1:y2, x1:x2] indexing)
                        crop = frame_img[y1:y2, x1:x2]
                        
                        if crop.size == 0:
                            failed += 1
                            failure_reasons['empty_crop'] += 1
                            continue

                        # Resize to target size
                        crop_resized = cv2.resize(crop, (RESCALE, RESCALE), interpolation=cv2.INTER_LINEAR)

                        # Save with high quality JPEG
                        success = cv2.imwrite(output_path, crop_resized, [cv2.IMWRITE_JPEG_QUALITY, 95])
                        
                        if success:
                            successful += 1
                        else:
                            failed += 1
                            failure_reasons['write_failed'] += 1
                            if os.path.exists(output_path):
                                os.remove(output_path)

                    except (ValueError, KeyError) as e:
                        failed += 1
                        failure_reasons['exception'] += 1
                        continue
                    except Exception as e:
                        failed += 1
                        failure_reasons['exception'] += 1
                        continue
                
                # Move to next frame we need
                frame_idx += 1

        cap.release()
        
        # Print summary with failure breakdown
        print(f"[{os.path.basename(media_path)}] Complete: {successful}/{total_crops} successful ({skipped_existing} already existed), {failed} failed")
        if failed > 0:
            print(f"[{os.path.basename(media_path)}] Failure breakdown: empty_crop={failure_reasons['empty_crop']}, "
                  f"write_failed={failure_reasons['write_failed']}, exception={failure_reasons['exception']}, "
                  f"beyond_video={failure_reasons['beyond_video']}, video_ended_early={failure_reasons['video_ended_early']}")
        
        return {
            'video': media_path, 
            'successful': successful, 
            'failed': failed, 
            'total': total_crops,
            'skipped_existing': skipped_existing,
            'failure_reasons': failure_reasons
        }

    except Exception as e:
        print(f"[{os.path.basename(media_path)}] Error: {e}")
        traceback.print_exc()
        return {
            'video': media_path, 
            'successful': successful, 
            'failed': failed, 
            'total': total_crops,
            'skipped_existing': skipped_existing,
            'failure_reasons': failure_reasons
        }


def worker_process(task_queue, result_queue, output_dir):
    """Worker process for multiprocessing - handles entire videos."""
    while True:
        try:
            video_data = task_queue.get()
            if video_data is None:  # Poison pill to stop worker
                break

            result = process_single_video(video_data, output_dir)
            result_queue.put(result)

        except Exception as e:
            print(f"Worker error: {e}")
            traceback.print_exc()
            result_queue.put({
                'video': 'ERROR', 
                'successful': 0, 
                'failed': 0, 
                'total': 0,
                'skipped_existing': 0,
                'failure_reasons': {}
            })

def process_csv_multiprocessing():
    """Main function to process CSV with multiprocessing - parallelized by video."""
    # Read CSV
    rows = []
    try:
        with open(INPUT_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except FileNotFoundError:
        print(f"Error: CSV file not found: {INPUT_CSV}")
        return
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    if not rows:
        print("No rows found in CSV")
        return
    
    # Check for duplicate UUIDs, missing UUIDs, and path issues
    print(f"\nChecking for duplicates and data quality in {len(rows)} rows...")
    uuid_set = set()
    duplicates = []
    missing_uuid = 0
    missing_path = 0
    invalid_path = 0
    not_found_path = 0
    
    for row in rows:
        uuid = row.get('uuid', '')
        if not uuid:
            missing_uuid += 1
        else:
            if uuid in uuid_set:
                duplicates.append(uuid)
            else:
                uuid_set.add(uuid)
        
        # Check path validity
        path = row.get('path', '')
        if not path:
            missing_path += 1
        elif path == "NOT_FOUND":
            not_found_path += 1
        elif not os.path.exists(path):
            invalid_path += 1
    
    print(f"\nData Quality Report:")
    print(f"  Total CSV rows: {len(rows)}")
    
    if missing_uuid > 0:
        print(f"  ⚠ Missing UUIDs: {missing_uuid}")
    else:
        print(f"  ✓ All rows have UUIDs")
    
    if duplicates:
        print(f"  ⚠ Duplicate UUIDs: {len(duplicates)}")
        print(f"    Unique UUIDs: {len(uuid_set)}")
        if len(duplicates) <= 10:
            print(f"    Example duplicates: {duplicates[:10]}")
    else:
        print(f"  ✓ No duplicate UUIDs - all {len(uuid_set)} are unique")
    
    # Path analysis
    total_path_issues = missing_path + not_found_path + invalid_path
    if total_path_issues > 0:
        print(f"  ⚠ Video path issues: {total_path_issues} rows")
        if missing_path > 0:
            print(f"    - Empty path column: {missing_path}")
        if not_found_path > 0:
            print(f"    - Path = 'NOT_FOUND': {not_found_path}")
        if invalid_path > 0:
            print(f"    - File doesn't exist: {invalid_path}")
        print(f"  → These {total_path_issues} rows will be SKIPPED")
    else:
        print(f"  ✓ All paths are valid")

    # Filter out rows with invalid paths before processing
    original_row_count = len(rows)
    valid_rows = []
    skipped_count = 0

    for row in rows:
        media_path = row.get('path', '')
        if not media_path or media_path == "NOT_FOUND":
            skipped_count += 1
            continue
        if not os.path.exists(media_path):
            skipped_count += 1
            continue
        valid_rows.append(row)

    if skipped_count > 0:
        print(f"\n⚠ Skipped {skipped_count} rows with invalid or missing media files")
        print(f"  Rows to process: {len(valid_rows)}/{original_row_count}")

    if not valid_rows:
        print("No valid rows to process after filtering")
        return

    # Group rows by video file (media_path)
    from collections import defaultdict
    video_groups = defaultdict(list)

    for row in valid_rows:
        media_path = row.get('path', '')
        video_groups[media_path].append(row)

    # Create list of (media_path, rows) tuples for each video
    video_tasks = [(media_path, rows) for media_path, rows in video_groups.items()]

    total_videos = len(video_tasks)
    total_crops = len(valid_rows)

    print(f"Processing {total_crops} crops from {total_videos} videos using {MAX_WORKERS} workers")
    print(f"Average crops per video: {total_crops / total_videos:.1f}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Method: OpenCV (cv2) - extracts frames once per video")
    print("-" * 60)

    # Create task and result queues
    task_queue = mp.Queue()
    result_queue = mp.Queue()

    # Start worker processes
    workers = []
    for i in range(MAX_WORKERS):
        worker = mp.Process(
            target=worker_process,
            args=(task_queue, result_queue, OUTPUT_DIR)
        )
        worker.start()
        workers.append(worker)
        print(f"Started worker {i + 1}/{MAX_WORKERS}")

    # Add video tasks to queue
    for video_task in video_tasks:
        task_queue.put(video_task)

    # Add poison pills to stop workers
    for _ in range(MAX_WORKERS):
        task_queue.put(None)

    # Monitor progress
    completed_videos = 0
    total_successful = 0
    total_failed = 0
    total_skipped_existing = 0
    aggregated_failures = {
        'empty_crop': 0,
        'write_failed': 0,
        'exception': 0,
        'beyond_video': 0,
        'video_ended_early': 0
    }
    video_results = []

    print(f"\nProcessing {total_videos} videos...")

    while completed_videos < total_videos:
        try:
            result = result_queue.get(timeout=1)
            completed_videos += 1
            total_successful += result['successful']
            total_failed += result['failed']
            total_skipped_existing += result.get('skipped_existing', 0)
            
            # Aggregate failure reasons
            for reason, count in result.get('failure_reasons', {}).items():
                aggregated_failures[reason] += count
            
            video_results.append(result)

            # Update progress
            progress = (completed_videos / total_videos) * 100
            print(f"Progress: {completed_videos}/{total_videos} videos ({progress:.1f}%) - "
                  f"Crops: {total_successful} successful ({total_skipped_existing} existing), {total_failed} failed")

        except:
            pass  # Timeout, continue checking

    # Wait for all workers to finish
    for worker in workers:
        worker.join()

    print("\n" + "=" * 60)
    print(f"Processing complete!")
    print(f"Total videos processed: {total_videos}")
    print(f"Total crops attempted: {total_crops}")
    print(f"Successful crops: {total_successful} ({total_skipped_existing} already existed)")
    print(f"Failed crops: {total_failed}")
    print(f"\nFailure Breakdown:")
    print(f"  Empty crops (after bounds check): {aggregated_failures['empty_crop']}")
    print(f"  Write failures: {aggregated_failures['write_failed']}")
    print(f"  Exceptions (parsing/processing): {aggregated_failures['exception']}")
    print(f"  Frames beyond video length: {aggregated_failures['beyond_video']}")
    print(f"  Video ended early: {aggregated_failures['video_ended_early']}")
    
    # Show correlation with CSV rows
    print(f"\n📊 Full Accounting:")
    print(f"  CSV rows read: {original_row_count}")
    print(f"  Rows filtered (invalid paths): {original_row_count - total_crops}")
    print(f"  Rows attempted for processing: {total_crops}")
    print(f"  └─ Successful: {total_successful}")
    print(f"     └─ New files created: {total_successful - total_skipped_existing}")
    print(f"     └─ Already existed: {total_skipped_existing}")
    print(f"  └─ Failed: {total_failed}")

    # Check for duplicates in results
    all_uuids = []
    for row in valid_rows:
        uuid = row.get('uuid', '')
        if uuid:
            all_uuids.append(uuid)
    
    unique_uuids = len(set(all_uuids))
    duplicate_count = len(all_uuids) - unique_uuids
    
    # Calculate how many rows were filtered
    rows_filtered = original_row_count - len(valid_rows)
    
    # Generate summary file
    summary_path = os.path.join(OUTPUT_DIR, "processing_summary.txt")
    with open(summary_path, 'w') as f:
        f.write(f"Processing Summary - {datetime.now()}\n")
        f.write("=" * 60 + "\n")
        f.write(f"Input CSV: {INPUT_CSV}\n")
        f.write(f"Output Directory: {OUTPUT_DIR}\n")
        f.write(f"Method: OpenCV (cv2)\n")
        f.write(f"Workers used: {MAX_WORKERS}\n")
        f.write(f"Target crop size: {RESCALE}x{RESCALE}px\n\n")
        
        f.write("CSV Data Quality:\n")
        f.write(f"  Total rows in CSV: {original_row_count}\n")
        f.write(f"  Rows with valid paths: {len(valid_rows)}\n")
        if rows_filtered > 0:
            f.write(f"  Rows filtered (invalid/missing paths): {rows_filtered}\n")
        
        if duplicate_count > 0:
            f.write(f"\nDuplicate Detection:\n")
            f.write(f"  Rows with valid paths: {len(all_uuids)}\n")
            f.write(f"  Unique UUIDs: {unique_uuids}\n")
            f.write(f"  Duplicate entries: {duplicate_count}\n")
        f.write("\n")

        f.write("Overall Statistics:\n")
        f.write(f"  Total videos: {total_videos}\n")
        f.write(f"  Total crops attempted: {total_crops}\n")
        f.write(f"  Avg crops per video: {total_crops / total_videos:.1f}\n")
        f.write(f"  Successful crops: {total_successful}\n")
        f.write(f"  Already existed (skipped): {total_skipped_existing}\n")
        f.write(f"  New crops created: {total_successful - total_skipped_existing}\n")
        f.write(f"  Failed crops: {total_failed}\n")
        f.write(f"  Success rate: {(total_successful / total_crops * 100 if total_crops > 0 else 0):.1f}%\n\n")
        
        f.write("Failure Breakdown:\n")
        f.write(f"  Empty crops (after bounds check): {aggregated_failures['empty_crop']}\n")
        f.write(f"  Write failures: {aggregated_failures['write_failed']}\n")
        f.write(f"  Exceptions (parsing/processing): {aggregated_failures['exception']}\n")
        f.write(f"  Frames beyond video length: {aggregated_failures['beyond_video']}\n")
        f.write(f"  Video ended early: {aggregated_failures['video_ended_early']}\n\n")

        f.write("Per-Video Results:\n")
        f.write("-" * 60 + "\n")
        for result in sorted(video_results, key=lambda x: x.get('failed', 0), reverse=True):
            video_name = os.path.basename(result['video'])
            f.write(f"{video_name}:\n")
            f.write(f"  Total: {result['total']}, Success: {result['successful']}, Failed: {result['failed']}\n")
            
            # Show failure breakdown if there were failures
            if result.get('failed', 0) > 0:
                reasons = result.get('failure_reasons', {})
                if any(reasons.values()):
                    f.write(f"  Failures: empty={reasons.get('empty_crop', 0)}, "
                           f"write={reasons.get('write_failed', 0)}, "
                           f"exception={reasons.get('exception', 0)}, "
                           f"beyond_video={reasons.get('beyond_video', 0)}, "
                           f"ended_early={reasons.get('video_ended_early', 0)}\n")

    print(f"Summary saved to: {summary_path}")


if __name__ == "__main__":
    print("=" * 60)
    print("Media Cropping Script (OpenCV-accelerated)")
    print("=" * 60)
    print("\nConfiguration:")
    print(f"  Input CSV: {INPUT_CSV}")
    print(f"  Output Directory: {OUTPUT_DIR}")
    print(f"  CPU Workers: {MAX_WORKERS}")
    print(f"  Target crop size: {RESCALE}x{RESCALE}px")
    print("=" * 60)

    # Test OpenCV availability
    try:
        cv2_version = cv2.__version__
        print(f"✓ OpenCV found (version {cv2_version})")
    except Exception as e:
        print(f"ERROR: OpenCV not available")
        print("Please install: pip install opencv-python")
        sys.exit(1)

    # Check input CSV
    if not os.path.exists(INPUT_CSV):
        print(f"ERROR: Input CSV not found: {INPUT_CSV}")
        print("Please run the previous script first or update INPUT_CSV")
        sys.exit(1)

    print(f"✓ Input CSV found: {INPUT_CSV}")
    print("\nStarting processing with OpenCV...")
    process_csv_multiprocessing()