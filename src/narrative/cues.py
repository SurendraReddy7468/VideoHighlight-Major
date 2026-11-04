import json
import string
import sys

PUNCT = string.punctuation + "\u2018\u2019\u201c\u201d\u2026\u0964\u2014\u2013"

# Sentence starts that depend on what came before
STRONG_START = {
    "and", "but", "because", "which", "or", "plus", "although", "though",
    "whereas", "cause", "cuz", "nor",
    # basic Hindi (romanized + Devanagari), to be extended
    "aur", "lekin", "kyunki", "magar", "\u0914\u0930", "\u0932\u0947\u0915\u093f\u0928",
    "\u0915\u094d\u092f\u094b\u0902\u0915\u093f", "\u092e\u0917\u0930",
}
MEDIUM_START = {
    "so", "then", "also", "anyway", "however", "yet",
    "toh", "isliye", "phir", "\u0924\u094b", "\u0907\u0938\u0932\u093f\u090f", "\u092b\u093f\u0930",
}
ANAPHORIC_START = {
    "this", "that", "these", "those", "it", "its", "they", "them", "their",
    "he", "she", "him", "her", "such",
}

# Words a sentence should not end on
TRAILING_WORDS = {
    "and", "but", "so", "because", "the", "a", "an", "to", "of", "that",
    "which", "or", "with", "for", "in", "on", "at", "is", "are", "was",
    "were", "if", "when", "as", "like", "my", "your", "our", "their",
}

# Endings that set up what comes next
SETUP_ENDINGS = (
    "think about this", "here's the thing", "here is the thing", "here's what",
    "here's why", "here is why", "here's how", "this is how", "let me explain",
    "let me tell you", "listen to this", "for example", "for instance",
    "the reason is", "what happens", "let's talk about", "like this",
    "the first one is", "the second one is",
)


def _tokens(text: str) -> list:
    return [t.strip(PUNCT).lower() for t in text.split() if t.strip(PUNCT)]


def is_question(text: str) -> bool:
    return text.rstrip().endswith("?")


def start_dangle_score(text: str) -> float:
    text = text.strip()
    toks = _tokens(text)
    if not toks:
        return 0.0
    first = toks[0]
    score = 0.0
    if first in STRONG_START:
        score = 1.0
    elif first in MEDIUM_START:
        score = 0.6
    elif first in ANAPHORIC_START:
        score = 0.5
    first_char = text.lstrip(PUNCT + " ")[:1]
    if first_char.islower():           # Whisper capitalises real sentence starts
        score = max(score, 0.5)
    return score


def end_dangle_score(text: str) -> float:
    text = text.strip()
    if not text:
        return 0.0
    if text[-1] in ",:;-\u2014\u2013" or text.endswith("...") or text.endswith("\u2026"):
        return 1.0
    toks = _tokens(text)
    if toks and toks[-1] in TRAILING_WORDS:
        return 0.9
    body = text.rstrip(PUNCT + " ").lower().replace("\u2019", "'")
    if any(body.endswith(p) for p in SETUP_ENDINGS):
        return 0.8
    if text[-1] == "?":
        return 0.7
    return 0.0


def annotate(sentences: list) -> list:
    """Adds is_question, dangle_start, dangle_end to each sentence dict (in place)."""
    for s in sentences:
        s["is_question"] = is_question(s["text"])
        s["dangle_start"] = start_dangle_score(s["text"])
        s["dangle_end"] = end_dangle_score(s["text"])
    return sentences


def annotate(sentences: list) -> list:
    """Adds is_question, dangle_start, dangle_end to each sentence dict (in place)."""
    for s in sentences:
        s["is_question"] = is_question(s["text"])
        s["dangle_start"] = start_dangle_score(s["text"])
        s["dangle_end"] = end_dangle_score(s["text"])

    # A sentence cut by the word cap breaks a thought in two: mark both halves
    for i, s in enumerate(sentences):
        if s.get("forced_split"):
            s["dangle_end"] = 1.0
            if i + 1 < len(sentences):
                sentences[i + 1]["dangle_start"] = 1.0
    return sentences