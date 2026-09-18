# test_stage3.py
import sys, json
sys.path.insert(0, ".")

from src.preprocessing.segmenter      import merge_segments
from src.scoring.highlight_score       import score_segments, save_scores
from src.editing.clip_generator        import generate_clip
from src.editing.format_converter      import convert_to_vertical

from pathlib import Path

video_files = list(Path("data/raw_videos").glob("*.mp4"))
audio_files = list(Path("data/audio").glob("*.wav"))

if not video_files or not audio_files:
    raise FileNotFoundError("Missing video or audio file — run test_stage1.py first.")

VIDEO_PATH = str(video_files[0])
AUDIO_PATH = str(audio_files[0])
MODE       = "shorts"   # change to "highlights" for long clip

# Load segments
with open("data/segments/segments.json", "r") as f:
    segments = json.load(f)

# Score
scored = score_segments(segments, AUDIO_PATH, VIDEO_PATH, mode="podcast")
save_scores(scored)

# Generate clip
raw_clip, selected_segments = generate_clip(VIDEO_PATH, scored, mode=MODE, output_name="raw_clip")

# Convert format
final = convert_to_vertical(raw_clip, "data/outputs/shorts/final_short.mp4")

print(f"\n🎉 FINAL OUTPUT: {final}")