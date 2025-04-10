#!/bin/bash

INPUT_DIR="/mnt/M3/master/i2MAP/2025/04"  # Change this to your target directory if needed

for file in "$INPUT_DIR"/*.mov; do
  # Check if file exists and is non-zero size
  if [[ -s "$file" ]]; then
    base_name="${file%.*}"
    file_name=$(basename "$base_name")
    output="/mnt/DeepSea-AI/data/i2MAP/2025/04/${file_name}.mp4"
    echo "Processing with GPU: $file → $output"

   ffmpeg -y -hwaccel cuda -i "$file" \
      -c:v h264_nvenc -preset slow -rc vbr -cq 19 -b:v 5M -maxrate 7M -bufsize 10M \
      -pix_fmt yuv420p \
      -c:a aac -b:a 320k \
      -movflags +faststart \
      "$output"
  else
    echo "Skipping empty file: $file"
  fi
done
