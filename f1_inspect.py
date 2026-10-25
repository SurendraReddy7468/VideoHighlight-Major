import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

TARGETS = {"shorts": (30, 60), "highlights": (60, 180)}


def old_greedy(scored, mn, mx):
    """Same logic as generate_clip() in src/editing/clip_generator.py"""
    ranked = sorted(scored, key=lambda s: s["score"], reverse=True)
    selected, total = [], 0.0
    for seg in ranked:
        d = seg["end"] - seg["start"]
        if total + d > mx:
            continue
        selected.append(seg)
        total += d
        if total >= mn:
            break
    return selected, total


def main(name, mode):
    path = f"data/analysis/{name}/scores.json"
    with open(path, encoding="utf-8") as f:
        scored = json.load(f)
    scored.sort(key=lambda s: s["start"])

    mn, mx = TARGETS[mode]
    selected, total = old_greedy(scored, mn, mx)
    picked = {s["start"] for s in selected}

    print(f"\n{name} | mode={mode} | {len(scored)} segments | old selector picks {len(selected)} ({total:.1f}s)\n")
    for i, s in enumerate(scored):
        mark = ">>" if s["start"] in picked else "  "
        dur = s["end"] - s["start"]
        print(f"{mark} #{i:02d} [{s['start']:7.1f}-{s['end']:7.1f}] {dur:4.1f}s  score={s['score']:.3f} | {s['text'][:110]}")

    print("\nOLD CLIP, in play order:")
    prev_end = None
    for s in sorted(selected, key=lambda x: x["start"]):
        if prev_end is not None:
            print(f"      ... JUMP of {s['start'] - prev_end:.1f}s in the original video ...")
        print(f"  [{s['start']:.1f}-{s['end']:.1f}] {s['text']}")
        prev_end = s["end"]


if __name__ == "__main__":
    video = sys.argv[1] if len(sys.argv) > 1 else "Begging_Disappear"
    mode = sys.argv[2] if len(sys.argv) > 2 else "shorts"
    main(video, mode)