import csv
import sys
from pathlib import Path

from src.narrative.spans import load, seg_score, pick_spans
from src.narrative.cues import start_dangle_score, end_dangle_score

ROOT = Path("data") / "analysis"
TOL = 0.5     # seconds: a cut this close to a sentence edge counts as clean
JUMP = 1.0    # seconds: a gap bigger than this between joined pieces is a time jump


def old_greedy(scored, mn=30.0, mx=60.0):
    """Same rule as generate_clip: best score first, skip overflow, stop at the minimum."""
    picked, total = [], 0.0
    for seg in sorted(scored, key=seg_score, reverse=True):
        d = seg["end"] - seg["start"]
        if total + d > mx:
            continue
        picked.append(seg)
        total += d
        if total >= mn:
            break
    return picked, total


def sentence_at(sents, t):
    return min(sents, key=lambda s: 0 if s["start"] <= t <= s["end"]
               else min(abs(t - s["start"]), abs(t - s["end"])))


def measure(pieces, sents):
    """pieces are in the order they are joined in the final clip."""
    jumps = sum(1 for a, b in zip(pieces, pieces[1:]) if abs(b["start"] - a["end"]) > JUMP)
    starts = [s["start"] for s in sents]
    ends = [s["end"] for s in sents]
    mid = 0
    for p in pieces:
        if min(abs(p["start"] - t) for t in starts) > TOL:
            mid += 1
        if min(abs(p["end"] - t) for t in ends) > TOL:
            mid += 1
    first = sentence_at(sents, pieces[0]["start"])
    last = sentence_at(sents, pieces[-1]["end"])
    return {
        "pieces": len(pieces),
        "jumps": jumps,
        "mid_cuts": mid,
        "start_risk": round(start_dangle_score(first["text"]), 2),
        "end_risk": round(end_dangle_score(last["text"]), 2),
        "seconds": round(sum(p["end"] - p["start"] for p in pieces), 1),
    }


def main(names):
    if not names:
        names = sorted(p.name for p in ROOT.iterdir()
                       if (p / "scores.json").exists() and (p / "sentences.json").exists())
    rows = []
    for name in names:
        base = ROOT / name
        try:
            sents = load(base / "sentences.json")
            scored = load(base / "scores.json")
            old, _ = old_greedy(scored)
            new = pick_spans(sents, scored, base, k=1)
            if not old or not new:
                print(f"skip {name}: nothing selected")
                continue
            for label, pieces in (("old", old), ("narrative", new)):
                rows.append({"video": name, "method": label, **measure(pieces, sents)})
            print(f"done {name}")
        except Exception as e:
            print(f"skip {name}: {e}")

    if not rows:
        print("no videos compared")
        return

    cols = ["video", "method", "pieces", "jumps", "mid_cuts", "start_risk", "end_risk", "seconds"]
    with open("f1_compare.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    print("\nAverages per method (lower is better except seconds)")
    print(f"{'method':<10}{'videos':>7}{'pieces':>8}{'jumps':>7}{'mid_cuts':>10}{'start_risk':>12}{'end_risk':>10}")
    for method in ("old", "narrative"):
        r = [x for x in rows if x["method"] == method]
        n = len(r)
        avg = lambda k: sum(x[k] for x in r) / n
        print(f"{method:<10}{n:>7}{avg('pieces'):>8.2f}{avg('jumps'):>7.2f}"
              f"{avg('mid_cuts'):>10.2f}{avg('start_risk'):>12.2f}{avg('end_risk'):>10.2f}")


if __name__ == "__main__":
    main(sys.argv[1:])