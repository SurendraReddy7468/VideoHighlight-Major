import os
import json
import time

from src.preprocessing.video_loader    import load_video
from src.preprocessing.audio_extractor import extract_audio
from src.analysis.text.transcription   import transcribe_audio
from src.preprocessing.segmenter       import merge_segments, save_segments
from src.scoring.highlight_score        import score_segments, save_scores
from src.editing.clip_generator         import generate_clip
from src.editing.format_converter       import convert_to_vertical, convert_to_horizontal


def run_pipeline(
    source: str,
    mode: str = "shorts",
    video_type: str = "podcast",
    whisper_model: str = "base",
    output_name: str = "final_clip",
    narrative: bool = False,
) -> str:
    """
    Full end-to-end pipeline: video → highlight clip.

    Args:
        source:        Local video path OR YouTube URL
        mode:          'shorts'     → 30–60s vertical  9:16
                       'highlights' → 60–180s horizontal 16:9
        video_type:    'podcast' or 'normal' (affects scoring weights)
        whisper_model: Whisper model size: tiny / base / small / medium
        output_name:   Output filename (without extension)

    Returns:
        Path to the final output clip
    """
    print("\n" + "="*55)
    print("  🎙️  Podcast Video Highlight Generator")
    print(f"  Mode      : {mode}")
    print(f"  Type      : {video_type}")
    print(f"  Source    : {source}")
    print("="*55 + "\n")

    # ── STEP 1: Load video ───────────────────────────────────
    print("── STEP 1/7  Load Video ──────────────────────────────")
    video_path = load_video(source)

    # ── STEP 2: Extract audio ────────────────────────────────
    print("\n── STEP 2/7  Extract Audio ───────────────────────────")
    audio_path = extract_audio(video_path)

    # ── STEP 3: Transcribe ───────────────────────────────────
    print("\n── STEP 3/7  Transcribe Audio ────────────────────────")
    raw_segments = transcribe_audio(audio_path, model_size=whisper_model)

    # ── STEP 4: Segment ──────────────────────────────────────
    print("\n── STEP 4/7  Merge Segments ──────────────────────────")
    segments = merge_segments(raw_segments)
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    save_segments(segments, name=base_name)

    # ── STEP 5: Score ────────────────────────────────────────
    print("\n── STEP 5/7  Score Segments ──────────────────────────")
    scored = score_segments(segments, audio_path, video_path, mode=video_type)
    save_scores(scored)

    narrative_spans = None
    if narrative:
        if mode != "shorts":
            print("[Narrative] only 'shorts' is supported so far; using the old selector")
        else:
            try:
                from src.narrative.sentences import build_sentences
                from src.narrative.spans import pick_spans
                words_path = os.path.join("data", "transcripts", f"{base_name}_words.json")
                with open(words_path, encoding="utf-8") as f:
                    words = json.load(f)
                sents = build_sentences(words)
                chrono = sorted(scored, key=lambda s: s["start"])
                narrative_spans = pick_spans(sents, chrono, k=3)
                print(f"[Narrative] {len(narrative_spans)} candidate spans; "
                      f"using {narrative_spans[0]['start']:.1f}-{narrative_spans[0]['end']:.1f}s")
            except Exception as e:
                print(f"[Narrative] failed ({e}); using the old selector")
                narrative_spans = None

    # ── STEP 6: Generate raw clip ────────────────────────────
    print("\n── STEP 6/7  Generate Clip ───────────────────────────")

    # Define out_dir early — needed by both intro and normal modes
    import time
    base_name = os.path.splitext(os.path.basename(source))[0]
    timestamp = int(time.time())
    out_dir = f"data/outputs/{mode}"
    os.makedirs(out_dir, exist_ok=True)

    if mode == "intro":
        from src.editing.clip_generator import generate_intro_clip
        raw_clip = generate_intro_clip(
            video_path, scored,
            output_dir=out_dir,
            output_name=f"{base_name}_intro_{timestamp}",
        )
        print(f"\n{'='*55}\n  🎉 DONE!\n  Output → {raw_clip}\n{'='*55}\n")
        return raw_clip

    raw_clip, selected_segments = generate_clip(
        video_path, narrative_spans or scored,
        mode=mode,
        output_name="raw_clip",
    )

    # ── STEP 7: Convert format ───────────────────────────────
    print("\n── STEP 7/7  Convert Format ──────────────────────────")
    final_path = os.path.join(out_dir, f"{base_name}_{mode}_{timestamp}.mp4")

    if mode == "shorts":
        # Build per-segment face positions using actual selected segments
        # These timestamps are relative to the joined raw_clip (start from 0)
        per_segment_faces = []
        running = 0.0
        for seg in selected_segments:
            dur    = seg["end"] - seg["start"]
            face_x = seg.get("face_center_x", 0.5)
            per_segment_faces.append((running, running + dur, face_x))
            running += dur

        print(f"[Pipeline] 👤 Per-segment face positions:")
        for s, e, fx in per_segment_faces:
            print(f"           [{s:.1f}s-{e:.1f}s] face_x={fx:.3f}")

        final_path = convert_to_vertical(
            raw_clip, final_path,
            face_center_x=per_segment_faces[0][2],
            per_segment_faces=per_segment_faces
        )
    else:
        final_path = convert_to_horizontal(raw_clip, final_path)

    if os.path.exists(raw_clip) and raw_clip != final_path:
        os.remove(raw_clip)

    print("\n" + "="*55)
    print(f"  🎉 DONE!")
    print(f"  Output → {final_path}")
    print("="*55 + "\n")

    return final_path