import os
import json
import whisper


def transcribe_audio(
    audio_path: str,
    output_dir: str = "data/transcripts",
    model_size: str = "base",
) -> list:
    """
    Transcribe audio to text with timestamps using OpenAI Whisper.

    Model size guide (pick based on your machine):
      tiny   → fastest, lowest accuracy  (good for quick tests)
      base   → fast, decent accuracy     ← recommended default
      small  → slower, better accuracy
      medium → slow, very good accuracy  (needs 5 GB+ RAM)
      large  → slowest, best accuracy    (needs 10 GB+ RAM / GPU)

    Args:
        audio_path:  Path to the .wav audio file
        output_dir:  Where to save the transcript JSON
        model_size:  Whisper model size string (see above)

    Returns:
        List of segment dicts: [{"start": float, "end": float, "text": str}, ...]
    """
    os.makedirs(output_dir, exist_ok=True)

    print(f"[Transcription] 🤖 Loading Whisper model: '{model_size}' ...")
    model = whisper.load_model(model_size)

    print(f"[Transcription] 🎙️  Transcribing: {audio_path}")
    result = model.transcribe(
        audio_path,
        verbose=False,
        word_timestamps=True,
        # fp16=False forces CPU mode — remove this line if you have a CUDA GPU
        fp16=False,
    )

    # Extract clean segment list
    raw_segments = []
    for seg in result["segments"]:
        raw_segments.append({
            "start": round(float(seg["start"]), 2),
            "end":   round(float(seg["end"]),   2),
            "text":  seg["text"].strip(),
        })

    # Save transcript to JSON
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    out_path = os.path.join(output_dir, f"{base_name}_transcript.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(raw_segments, f, indent=2, ensure_ascii=False)
    # Word-level timestamps (used by sentence builder and karaoke captions)
    words = []
    for seg in result["segments"]:
        for w in seg.get("words", []):
            words.append({
                "word":  w["word"].strip(),
                "start": round(float(w["start"]), 2),
                "end":   round(float(w["end"]),   2),
            })
    words_path = os.path.join(output_dir, f"{base_name}_words.json")
    with open(words_path, "w", encoding="utf-8") as f:
        json.dump(words, f, indent=2, ensure_ascii=False)
    print(f"[Transcription] 🔤 {len(words)} words → {words_path}")
    print(f"[Transcription] ✅ {len(raw_segments)} segments → {out_path}")
    return raw_segments


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python transcription.py <audio.wav> [model_size]")
        sys.exit(1)

    audio  = sys.argv[1]
    size   = sys.argv[2] if len(sys.argv) > 2 else "base"
    segs   = transcribe_audio(audio, model_size=size)

    print("\nFirst 3 segments:")
    for s in segs[:3]:
        print(f"  [{s['start']}s → {s['end']}s]  {s['text']}")