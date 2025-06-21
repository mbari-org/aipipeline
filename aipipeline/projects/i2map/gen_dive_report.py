# Utility to export csv with a report of a dive

import csv
import json
import requests

if __name__ == "__main__":

    # Fetch the data from the API
    url = "http://mantis.shore.mbari.org:8001/labels/detail/901103-biodiversity"  # Replace with the actual API endpoint
    json_data = {
        "version_name": "megart-mbari-i2map-vits-b-8-2025",
        "attribute": "depth"
    }

    response = requests.post(url, json=json_data)
    if response.status_code != 200:
        print(f"Error fetching data: {response.status_code}")
        print(response.text)
        exit(1)

    rows = []
    data = response.json()

    for label, depths in data["labels"].items():
        for depth, count in depths.items():
            rows.append([label, float(depth), count])

    # Write to CSV
    with open("label_depth_count.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Label", "Depth", "Count"])  # header
        writer.writerows(rows)
