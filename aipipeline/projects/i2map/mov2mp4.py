# aipipeline, Apache-2.0 license
# Filename: projects/i2map/mov2mp4.py
# Description: Utility to recursively transcode MOV files to fast start MP4 with keyframes compatible with Tator. Retains directory structure.
import subprocess
from pathlib import Path
import argparse


def transcode_file(input_file: Path, output_file: Path, gop: int, codec: str = "hevc"):
    """Run ffmpeg to transcode with selectable codec."""
    output_file.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg", "-y", "-hwaccel", "cuda", "-i", str(input_file),
        "-g", str(gop), "-keyint_min", str(gop), "-sc_threshold", "0",
        "-c:v", "h264",
        "-an",  # Remove audio
        "-preset", "slow",  # Slower preset = better quality
        "-avoid_negative_ts", "make_zero",
        "-movflags", "faststart+frag_keyframe+empty_moov+default_base_moof",
        str(output_file)
    ]
    subprocess.run(command, check=True)

def main():
    parser = argparse.ArgumentParser(description="Recursively transcode AVI files to fast start MP4 with keyframes compatible with Tator. Retains directory structure.")
    parser.add_argument("--input", required=True, help="Input directory to search for MP4 files")
    parser.add_argument("--output", required=True, help="Output directory to store transcoded MP4s")
    parser.add_argument("--gop", type=int, default=120, help="GOP size (default: 120)")

    args = parser.parse_args()
    input_dir = Path(args.input).resolve()
    output_dir = Path(args.output).resolve()
    gop = args.gop

    for input_file in input_dir.rglob("*.mov"):
        if input_file.stat().st_size == 0:
            print(f"Skipping empty file: {input_file}")
            continue
        relative_path = input_file.relative_to(input_dir)
        output_file = output_dir / relative_path
        output_file = output_file.with_suffix(".mp4")
        transcode_file(input_file, output_file, gop)

if __name__ == "__main__":
    main()
