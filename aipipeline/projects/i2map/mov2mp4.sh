#!/bin/bash

INPUT_DIR="/mnt/M3/master/i2MAP/2025/04/20250402/"
OUTPUT_DIR="/mnt/DeepSea-AI/data/i2MAP/2025/04/20250402"

for file in "$INPUT_DIR"/*.mov; do
  # Check if file exists and is non-zero size
  if [[ -s "$file" ]]; then
    base_name="${file%.*}"
    file_name=$(basename "$base_name")
    output="${OUTPUT_DIR}/${file_name}.mp4"
    echo "Processing with GPU: $file → $output"

   ffmpeg -y -hwaccel cuda -i "$file" \
      -g 120 -keyint_min 120 -sc_threshold 0 \
      -c:v h264_nvenc -preset slow -rc vbr -cq 19 -b:v 5M -maxrate 7M -bufsize 10M \
      -pix_fmt yuv420p \
      -c:a aac -b:a 320k \
      -movflags +faststart+frag_keyframe+empty_moov+default_base_moof \
      "$output"
  else
    echo "Skipping empty file: $file"
  fi
done