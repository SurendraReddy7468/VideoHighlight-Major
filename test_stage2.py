# test_stage2.py
import sys, json
sys.path.insert(0, ".")

from src.analysis.audio.energy    import compute_energy
from src.analysis.audio.pitch     import compute_pitch_variation
from src.analysis.text.keywords   import compute_keyword_score
from src.analysis.text.sentiment  import compute_sentiment_score

from pathlib import Path

audio_files = list(Path("data/audio").glob("*.wav"))
AUDIO_PATH = str(audio_files[0]) if audio_files else None
if AUDIO_PATH is None:
    raise FileNotFoundError("No .wav file found in data/audio/ — run test_stage1.py first.")
    
# Load segments
with open("data/segments/segments.json", "r") as f:
    segments = json.load(f)

all_texts = [s["text"] for s in segments]

print(f"{'#':<3} {'Start':>6} {'End':>6} {'Energy':>8} {'Pitch':>8} {'Keywords':>10} {'Sentiment':>10}")
print("-" * 60)

for i, seg in enumerate(segments):
    energy    = compute_energy(AUDIO_PATH, seg["start"], seg["end"])
    pitch     = compute_pitch_variation(AUDIO_PATH, seg["start"], seg["end"])
    keywords  = compute_keyword_score(seg["text"], all_texts)
    sentiment = compute_sentiment_score(seg["text"])

    print(f"{i+1:<3} {seg['start']:>6.1f} {seg['end']:>6.1f} "
          f"{energy:>8.3f} {pitch:>8.3f} {keywords:>10.3f} {sentiment:>10.3f}")