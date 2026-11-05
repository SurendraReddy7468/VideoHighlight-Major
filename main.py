"""
Podcast Video Highlight Generator
==================================
Usage:
    python main.py --input <path_or_url> --mode <shorts|highlights>

Examples:
    python main.py --input data/raw_videos/video_01.mp4 --mode shorts
    python main.py --input data/raw_videos/video_01.mp4 --mode highlights
    python main.py --input https://www.youtube.com/watch?v=XXX --mode shorts

Options:
    --input          Local video path or YouTube URL  (required)
    --mode           'shorts' for 30-60s vertical clip
                     'highlights' for 60-180s horizontal clip  (default: shorts)
    --type           'podcast' or 'normal'  (default: podcast)
    --whisper        Whisper model size: tiny/base/small/medium  (default: base)
    --output         Output filename without extension  (default: final_clip)
"""

import sys
import os
import argparse

# Make sure src/ is importable from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.pipeline import run_pipeline


def parse_args():
    parser = argparse.ArgumentParser(
        description="🎙️  AI Podcast Video Highlight Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Local video path or YouTube URL",
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["shorts", "highlights", "intro"],
        default="shorts",
        help="Output mode: 'shorts' (30-60s vertical) | 'highlights' (60-180s horizontal) | 'intro' (15-25s hook teaser)",
    )
    parser.add_argument(
        "--type", "-t",
        choices=["podcast", "normal"],
        default="podcast",
        dest="video_type",
        help="Video type — affects scoring weights (default: podcast)",
    )
    parser.add_argument(
        "--whisper", "-w",
        choices=["tiny", "base", "small", "medium", "large"],
        default="base",
        help="Whisper model size (default: base). Use 'small' for better accuracy.",
    )
    parser.add_argument(
        "--output", "-o",
        default="final_clip",
        help="Output filename without extension (default: final_clip)",
    )
    parser.add_argument(
        "--narrative",
        action="store_true",
        help="Cut one continuous sentence-aligned span (F1) instead of stitching pieces",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        final_path = run_pipeline(
            source=args.input,
            mode=args.mode,
            video_type=args.video_type,
            whisper_model=args.whisper,
            narrative=args.narrative,
            output_name=args.output,
        )
        print(f"✅ Success!  Open your clip: {final_path}")

    except FileNotFoundError as e:
        print(f"\n❌ File not found: {e}")
        print("   Check your --input path is correct.")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()