# test_stage1.py  — run from D:\Project\Podcast\
import sys
sys.path.insert(0, ".")

from src.preprocessing.video_loader   import load_video
from src.preprocessing.audio_extractor import extract_audio
from src.analysis.text.transcription  import transcribe_audio
from src.preprocessing.segmenter      import merge_segments, save_segments

# ── Change this to your sample video path or a YouTube URL ──
SOURCE = "https://youtube.com/shorts/baLpuhjXbiI?si=dHPlacNq7d5d4dIG"

video    = load_video(SOURCE)
audio    = extract_audio(video)
raw      = transcribe_audio(audio, model_size="base")
segments = merge_segments(raw)
save_segments(segments)

print(f"\n✅ Done!  {len(segments)} segments ready.")
print("First segment:", segments[0])