import json
import re
import sys
from pathlib import Path

import numpy as np

try:
    from cues import start_dangle_score, end_dangle_score
except ImportError:
    from src.narrative.cues import start_dangle_score, end_dangle_score

MIN_DUR, MAX_DUR = 30.0, 60.0      # shorts mode
W_START, W_END = 0.3, 0.3          # boundary penalty weights
W_SHORT = 0.3                      # penalty for a very short first sentence
SHORT_WORDS = 3                    # "Yeah." "Right." "Okay."
PAUSE_BONUS, PAUSE_MIN = 0.05, 0.5

W_REPLY = 0.3                      # penalty for a first sentence that answers someone
REPLY_OPENER = re.compile(
    r"^\s*((yeah|yes|yep|okay|ok|exactly|sure|right)\b[,.!?]"
    r"|do you (know|see|understand)\b"
    r"|you know what i mean"
    r"|does that make sense)",
    re.I,
)
W_TINY_END = 0.3                   # penalty for ending on a 1-2 word sentence
TINY_END_WORDS = 2
W_FORCED = 0.5                     # penalty when a cap cut a sentence in half at a span edge
WIN = 3                            # sentences per window for cut strength
W_INTRO = 0.6                      # intro greetings and outro sign-offs are not highlights
INTRO = re.compile(r"^\s*(hello|hi|hey|welcome)\b|welcome back|welcome to", re.I)
OUTRO = re.compile(r"thanks? for watching|thank you for watching|see you (in|on) the next|subscribe|like and share", re.I)

W_COH = 0.5                        # reward: sentences in the span stay on one topic
W_CUT = 0.5                        # penalty: span cuts through a topic at its edges
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


def load(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        for k in ("sentences", "segments", "scores"):
            if k in data:
                return data[k]
    return data


def seg_score(seg):
    for k in ("score", "final_score", "total_score"):
        if k in seg:
            return float(seg[k])
    raise KeyError(f"no score key in {list(seg)}")


def sentence_scores(sents, segs):
    raw = [seg_score(s) for s in segs]
    lo, hi = min(raw), max(raw)
    norm = [(r - lo) / (hi - lo) if hi > lo else 0.0 for r in raw]
    out = []
    for s in sents:
        mid = (s["start"] + s["end"]) / 2
        best = min(range(len(segs)),
                   key=lambda i: 0 if segs[i]["start"] <= mid <= segs[i]["end"]
                   else min(abs(mid - segs[i]["start"]), abs(mid - segs[i]["end"])))
        out.append(norm[best])
    return out


def n_words(s):
    return s.get("n_words", len(s["text"].split()))


def get_embeddings(base, sents):
    """One unit-length vector per sentence; cached in the video's folder."""
    path = base / "embeddings.npy"
    if path.exists():
        emb = np.load(path)
        if len(emb) == len(sents):
            return emb
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(MODEL_NAME)
    emb = model.encode([s["text"] for s in sents],
                       normalize_embeddings=True, show_progress_bar=False)
    np.save(path, emb)
    return emb


def cohesion(emb, i, j):
    block = emb[i:j + 1]
    centroid = block.mean(axis=0)
    centroid = centroid / (np.linalg.norm(centroid) + 1e-9)
    return float((block @ centroid).mean())


def _unit(v):
    return v / (np.linalg.norm(v) + 1e-9)


def cut_strength(emb, i, j):
    """Similarity of the 3 sentences on each side of each cut. High = cuts through a topic."""
    before = after = 0.0
    if i > 0:
        before = float(_unit(emb[max(0, i - WIN):i].mean(axis=0))
                       @ _unit(emb[i:min(j + 1, i + WIN)].mean(axis=0)))
    if j + 1 < len(emb):
        after = float(_unit(emb[max(i, j - WIN + 1):j + 1].mean(axis=0))
                      @ _unit(emb[j + 1:j + 1 + WIN].mean(axis=0)))
    return before, after


def candidates(sents, sc, emb):
    spans = []
    for i in range(len(sents)):
        for j in range(i, len(sents)):
            dur = sents[j]["end"] - sents[i]["start"]
            if dur > MAX_DUR:
                break
            if dur < MIN_DUR:
                continue
            avg = sum(sc[i:j + 1]) / (j - i + 1)
            score = (avg
                     - W_START * start_dangle_score(sents[i]["text"])
                     - W_END * end_dangle_score(sents[j]["text"]))
            if n_words(sents[j]) <= TINY_END_WORDS:
                score -= W_TINY_END
            if sents[j].get("forced_split"):
                score -= W_FORCED
            if i > 0 and sents[i - 1].get("forced_split"):
                score -= W_FORCED
            if INTRO.search(sents[i]["text"]):
                score -= W_INTRO
            if OUTRO.search(sents[j]["text"]):
                score -= W_INTRO
            if n_words(sents[i]) <= SHORT_WORDS:
                score -= W_SHORT
            if REPLY_OPENER.match(sents[i]["text"]):
                score -= W_REPLY
            if (sents[j].get("pause_after") or 0) >= PAUSE_MIN:
                score += PAUSE_BONUS
            before, after = cut_strength(emb, i, j)
            score += W_COH * cohesion(emb, i, j) - W_CUT * (before + after)
            spans.append((score, i, j, dur))
    return sorted(spans, reverse=True)


def select_top(cands, k=3):
    """Best span first; drop anything sharing a sentence with a chosen span."""
    chosen = []
    for score, i, j, dur in cands:
        if all(j < ci or i > cj for _, ci, cj, _ in chosen):
            chosen.append((score, i, j, dur))
            if len(chosen) == k:
                break
    return chosen


if __name__ == "__main__":
    video = sys.argv[1] if len(sys.argv) > 1 else "Begging_Disappear"
    base = Path("data") / "analysis" / video
    sents = load(base / "sentences.json")
    segs = load(base / "scores.json")
    sc = sentence_scores(sents, segs)
    emb = get_embeddings(base, sents)
    for rank, (score, i, j, dur) in enumerate(select_top(candidates(sents, sc, emb)), 1):
        b, a = cut_strength(emb, i, j)
        print(f"#{rank}  score {score:.3f}  {sents[i]['start']:.1f}-{sents[j]['end']:.1f}s  ({dur:.1f}s)"
              f"  cohesion {cohesion(emb, i, j):.2f}  cut before {b:.2f} after {a:.2f}")
        if i > 0:
            print(f"   [before span] {sents[i - 1]['text']}")
        print(f"   first: {sents[i]['text']}")
        print(f"   last:  {sents[j]['text']}")
        if j + 1 < len(sents):
            print(f"   [after span]  {sents[j + 1]['text']}")