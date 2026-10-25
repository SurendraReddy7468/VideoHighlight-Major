import argparse
import json
import os
import time

from src.preprocessing.video_loader import load_video
from src.preprocessing.audio_extractor import extract_audio
from src.analysis.text.transcription import transcribe_audio
from src.preprocessing.segmenter import merge_segments
from src.scoring.highlight_score import score_segments
from src.narrative.sentences import build_sentences

VIDEO_EXTS = (".mp4", ".mkv", ".mov", ".avi", ".webm")


def _dump(obj, path, indent=2):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=indent, ensure_ascii=False)


def build_one(video_file, out_root, whisper_model, video_type):
    name = os.path.splitext(os.path.basename(video_file))[0]
    out_dir = os.path.join(out_root, name)
    scores_path = os.path.join(out_dir, "scores.json")

    if os.path.exists(scores_path):
        print(f"[Cache] skip (already cached): {name}")
        return

    os.makedirs(out_dir, exist_ok=True)
    t0 = time.time()

    video_path = load_video(video_file)
    audio_path = extract_audio(video_path)
    raw = transcribe_audio(audio_path, model_size=whisper_model)
    segments = merge_segments(raw)
    _dump(segments, os.path.join(out_dir, "segments.json"))

    # Word timestamps are saved by transcribe_audio; build sentence units from them
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    words_path = os.path.join("data", "transcripts", f"{base_name}_words.json")
    with open(words_path, encoding="utf-8") as f:
        words = json.load(f)
    sentences = build_sentences(words)
    _dump(words, os.path.join(out_dir, "words.json"), indent=None)
    _dump(sentences, os.path.join(out_dir, "sentences.json"))

    scored = score_segments(segments, audio_path, video_path, mode=video_type)
    scored.sort(key=lambda s: s["start"])  # chronological order, needed by F1

    meta = {
        "video": video_file,
        "whisper_model": whisper_model,
        "video_type": video_type,
        "segments": len(scored),
        "sentences": len(sentences),
        "seconds_taken": round(time.time() - t0, 1),
    }
    _dump(meta, os.path.join(out_dir, "meta.json"))

    # scores.json is written last, so its existence means this video is complete
    _dump(scored, scores_path)

    print(f"[Cache] done: {name} ({meta['seconds_taken']}s, "
          f"{len(scored)} segments, {len(sentences)} sentences)")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--videos", default="data/raw_videos")
    p.add_argument("--out", default="data/analysis")
    p.add_argument("--whisper", default="base")
    p.add_argument("--type", default="podcast")
    p.add_argument("--limit", type=int, default=0, help="process only the first N videos")
    args = p.parse_args()

    files = sorted(
        os.path.join(args.videos, f)
        for f in os.listdir(args.videos)
        if f.lower().endswith(VIDEO_EXTS)
    )
    if args.limit:
        files = files[: args.limit]

    print(f"[Cache] {len(files)} video(s) to process")
    for i, vf in enumerate(files, 1):
        print(f"\n===== {i}/{len(files)}: {os.path.basename(vf)} =====")
        build_one(vf, args.out, args.whisper, args.type)


if __name__ == "__main__":
    main()