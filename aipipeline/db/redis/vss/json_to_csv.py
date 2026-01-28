import json
import csv
from pathlib import Path
from typing import Any, Dict, List


def flatten_json(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Flatten the nested JSON structure into rows suitable for CSV.

    Each row will contain:
    - file_path: the original file path
    - prediction_1, prediction_2, prediction_3: the three predictions
    - score_1, score_2, score_3: the three scores
    - id_1, id_2, id_3: the three IDs
    """
    flattened_rows = []

    # Support both "filenames" (VSS output) and "file_paths" (legacy)
    file_paths = data.get("filenames") or data.get("file_paths", [])
    predictions = data.get("predictions", [])
    scores = data.get("scores", [])
    ids = data.get("ids", [])

    for i in range(len(file_paths)):
        row = {
            "file_path": file_paths[i],
            "prediction_1": predictions[i][0] if i < len(predictions) and len(predictions[i]) > 0 else "",
            "prediction_2": predictions[i][1] if i < len(predictions) and len(predictions[i]) > 1 else "",
            "prediction_3": predictions[i][2] if i < len(predictions) and len(predictions[i]) > 2 else "",
            "score_1": scores[i][0] if i < len(scores) and len(scores[i]) > 0 else "",
            "score_2": scores[i][1] if i < len(scores) and len(scores[i]) > 1 else "",
            "score_3": scores[i][2] if i < len(scores) and len(scores[i]) > 2 else "",
            "id_1": ids[i][0] if i < len(ids) and len(ids[i]) > 0 else "",
            "id_2": ids[i][1] if i < len(ids) and len(ids[i]) > 1 else "",
            "id_3": ids[i][2] if i < len(ids) and len(ids[i]) > 2 else "",
        }
        flattened_rows.append(row)

    return flattened_rows


def process_directory(root_dir: str, output_csv: str) -> None:
    """Recursively walk through directory and merge all .json files into a single .csv file.

    Args:
        root_dir: Root directory to start the search
        output_csv: Path to the output CSV file
    """
    root_path = Path(root_dir)

    if not root_path.exists():
        print(f"Error: Directory {root_dir} does not exist")
        return

    json_files = list(root_path.rglob("*.json"))

    if not json_files:
        print(f"No JSON files found in {root_dir}")
        return

    print(f"Found {len(json_files)} JSON file(s)")

    all_rows = []

    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)

            flattened_data = flatten_json(data)
            all_rows.extend(flattened_data)
            print(f"Processed {json_file}: {len(flattened_data)} rows")
        except Exception as e:
            print(f"Error processing {json_file}: {e}")

    if not all_rows:
        print("No data to write")
        return

    fieldnames = list(all_rows[0].keys())

    with open(output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Merged {len(all_rows)} rows into {output_csv}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python json_to_csv.py <directory_path> <output_csv>")
        sys.exit(1)

    directory = sys.argv[1]
    output_file = sys.argv[2]
    process_directory(directory, output_file)