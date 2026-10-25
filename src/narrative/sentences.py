import json
import re
import sys

# A sentence ends with . ? ! (or the Hindi danda), optionally followed by a quote/bracket
END_RE = re.compile(r"[.?!\u0964]+[\"')\]]*$")
ABBREV = {"mr.", "mrs.", "ms.", "dr.", "vs.", "e.g.", "i.e."}

SOFT_SPLIT_WORDS = 30   # after this many words, split at the next real pause
SOFT_SPLIT_GAP = 0.6    # seconds of silence that counts as a real pause
HARD_SPLIT_WORDS = 60   # never let one "sentence" run longer than this


def _ends_sentence(word: str) -> bool:
    if word.lower() in ABBREV:
        return False
    return bool(END_RE.search(word))


def build_sentences(words: list) -> list:
    """
    words:  [{"word", "start", "end"}, ...] from Whisper word timestamps
    return: [{"id", "start", "end", "text", "n_words", "pause_after"}, ...]
    """
    sentences, cur = [], []

    def close():
        if not cur:
            return
        sentences.append({
            "id": len(sentences),
            "start": cur[0]["start"],
            "end": cur[-1]["end"],
            "text": " ".join(w["word"] for w in cur),
            "n_words": len(cur),
        })
        cur.clear()

    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        gap = (nxt["start"] - w["end"]) if nxt else 0.0

        if _ends_sentence(w["word"]):
            close()
        elif len(cur) >= HARD_SPLIT_WORDS:
            close()
        elif len(cur) >= SOFT_SPLIT_WORDS and gap >= SOFT_SPLIT_GAP:
            close()
    close()

    for i, s in enumerate(sentences):
        if i + 1 < len(sentences):
            s["pause_after"] = round(sentences[i + 1]["start"] - s["end"], 2)
        else:
            s["pause_after"] = None
    return sentences


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    path = sys.argv[1]
    lo = float(sys.argv[2]) if len(sys.argv) > 2 else 40.0
    hi = float(sys.argv[3]) if len(sys.argv) > 3 else 70.0

    with open(path, encoding="utf-8") as f:
        words = json.load(f)
    sents = build_sentences(words)

    durs = [s["end"] - s["start"] for s in sents]
    print(f"{len(words)} words -> {len(sents)} sentences")
    print(f"avg {sum(durs)/len(durs):.1f}s | longest {max(durs):.1f}s | over 20s: {sum(d > 20 for d in durs)}")

    print(f"\nSentences between {lo:.0f}s and {hi:.0f}s:")
    for s in sents:
        if lo <= s["start"] <= hi:
            pa = s["pause_after"]
            pa_txt = "-" if pa is None else f"{pa:.2f}s"
            print(f"  #{s['id']:03d} [{s['start']:6.1f}-{s['end']:6.1f}] pause_after={pa_txt} | {s['text']}")