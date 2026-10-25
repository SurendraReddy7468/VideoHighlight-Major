import argparse
import json
import os
import time

from src.preprocessing.video_loader import load_video
from src.preprocessing.audio_extractor import extract_audio
from src.analysis.text.transcription import transcribe_audio
from src.preprocessing.segmenter import merge_segments
from src.scoring.highlight_score import score_segments

VIDEO_EXTS = (".mp4", ".mkv", ".mov", ".avi", ".webm")


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

    with open(os.path.join(out_dir, "segments.json"), "w", encoding="utf-8") as f:
        json.dump(segments, f, indent=2, ensure_ascii=False)

    scored = score_segments(segments, audio_path, video_path, mode=video_type)
    scored.sort(key=lambda s: s["start"])  # chronological order, needed by F1

    meta = {
        "video": video_file,
        "whisper_model": whisper_model,
        "video_type": video_type,
        "segments": len(scored),
        "seconds_taken": round(time.time() - t0, 1),
    }
    with open(os.path.join(out_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    # scores.json is written last, so its existence means this video is complete
    with open(scores_path, "w", encoding="utf-8") as f:
        json.dump(scored, f, indent=2, ensure_ascii=False)

    print(f"[Cache] done: {name} ({meta['seconds_taken']}s, {len(scored)} segments)")


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
