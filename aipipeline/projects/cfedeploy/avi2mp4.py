import os
import subprocess
from pathlib import Path
import argparse

def transcode_file(input_file: Path, output_file: Path, gop: int):
    """Run ffmpeg to transcode the video."""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    print(f"Transcoding: {input_file} → {output_file}")
    command = [
        "ffmpeg", "-y", "-i", str(input_file),
        "-g", str(gop), "-keyint_min", str(gop), "-sc_threshold", "0",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-movflags", "faststart+frag_keyframe+empty_moov+default_base_moof",
        str(output_file)
    ]
    subprocess.run(command, check=True)

def main():
    parser = argparse.ArgumentParser(description="Recursively transcode AVI files to fast start MP4 with keyframes compatible with Tator. Retains directory structure.")
    parser.add_argument("--input", required=True, help="Input directory to search for MP4 files")
    parser.add_argument("--output", required=True, help="Output directory to store transcoded MP4s")
    parser.add_argument("--gop", type=int, default=30, help="GOP size (default: 30)")

    args = parser.parse_args()
    input_dir = Path(args.input).resolve()
    output_dir = Path(args.output).resolve()
    gop = args.gop

    for input_file in input_dir.rglob("*.avi"):
        if input_file.stat().st_size == 0:
            print(f"Skipping empty file: {input_file}")
            continue
        relative_path = input_file.relative_to(input_dir)
        output_file = output_dir / relative_path
        output_file = output_file.with_suffix(".mp4")
        transcode_file(input_file, output_file, gop)

if __name__ == "__main__":
    main()
