# aipipeline, Apache-2.0 license
# Filename: projects/bio/core/args.py
# Description: Argument parser for bio projects

import argparse
from pathlib import Path
from textwrap import dedent

DEFAULT_CONFIG_YAML = Path(__file__).resolve().parent / "config" / "config.yml"
DEFAULT_VIDEO = Path(__file__).resolve().parent / "data" / "V4361_20211006T163256Z_h265_1min.mp4"

def parse_args():
    parser = argparse.ArgumentParser(
        description=dedent("""\
        Run strided video track pipeline with REDIS queue based load.

        Example: 
        python3 predict.py /path/to/video.mp4
        """),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--config", default=DEFAULT_CONFIG_YAML, required=False, help=f"Configuration files. Default: {DEFAULT_CONFIG_YAML}", type=str)
    parser.add_argument("--video", help="Video file", required=False, type=str, default=DEFAULT_VIDEO)
    parser.add_argument("--max-seconds", help="Maximum number of seconds to process.", required=False, type=int)
    parser.add_argument("--min-frames", help="Minimum number of frames a track must have.", required=False, type=int, default=5)
    parser.add_argument("--min-score-track", help="Minimum score for a track to be valid.", required=False, type=float, default=0.1)
    parser.add_argument("--min-score-det", help="Minimum score for a detection to be valid.", required=False, type=float, default=0.1)
    parser.add_argument("--max-frames-tracked", help="Maximum number of frames a track can have before closing it.", required=False, type=int, default=300)
    parser.add_argument("--version", help="Version name", required=False, type=str)
    parser.add_argument("--gpu-id", help="GPU ID to use for inference.", required=False, type=int, default=0)
    parser.add_argument("--vits-model", help="ViTS vits_model location", required=False, type=str, default="/mnt/DeepSea-AI/models/m3midwater-vit-b-16/")
    parser.add_argument("--skip-load", help="Skip loading the video reference into Tator.", action="store_true")
    parser.add_argument("--imshow", help="Display the video as images with track results", action="store_true")
    parser.add_argument("--stride", help="Frame stride, e.g. 10 run every 10th frame", default=3, type=int)
    parser.add_argument("--class_name", help="Class name to target inference.", default="Ctenophora sp. A", type=str)
    parser.add_argument( "--endpoint-url", help="URL of the inference endpoint.", required=False, type=str,)
    parser.add_argument("--det-model",help="Object detection model path.",required=False, type=str,)
    parser.add_argument("--batch-size", help="Batch size", default=1, type=int)
    parser.add_argument("--min-depth", help="Minimum depth for detections. Any video shallower than this at the beginning of the video will be skipped", default=0, type=int)
    parser.add_argument("--flush", help="Flush the REDIS database.", action="store_true")
    parser.add_argument('--allowed-classes',type=str,nargs='+',help='List of allowed classes.')
    parser.add_argument('--class-remap',type=str,help='Dictionary of class remapping, formatted as a string.')
    parser.add_argument('--create-video', help="Create video with tracked results.", action="store_true")
    return parser.parse_args()
