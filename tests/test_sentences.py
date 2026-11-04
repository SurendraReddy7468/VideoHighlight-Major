from src.narrative.sentences import build_sentences


def W(text, start, dur=0.3):
    return {"word": text, "start": start, "end": round(start + dur, 2)}


def make_words(tokens, t0=0.0, step=0.4):
    words, t = [], t0
    for tok in tokens:
        words.append(W(tok, t))
        t = round(t + step, 2)
    return words


def test_empty_input():
    assert build_sentences([]) == []


def test_splits_on_sentence_punctuation():
    words = make_words("What happened? I do not know. Let us see!".split())
    s = build_sentences(words)
    assert [x["text"] for x in s] == ["What happened?", "I do not know.", "Let us see!"]


def test_start_end_come_from_first_and_last_word():
    words = make_words(["Hello", "there."], t0=10.0)
    s = build_sentences(words)[0]
    assert s["start"] == 10.0
    assert s["end"] == words[-1]["end"]


def test_abbreviation_does_not_split():
    words = make_words("Ask Dr. Rao about it.".split())
    assert len(build_sentences(words)) == 1


def test_decimal_number_does_not_split():
    words = make_words("It costs 3.5 dollars today.".split())
    assert len(build_sentences(words)) == 1


def test_hindi_danda_splits():
    words = make_words(["yah", "sahi", "hai\u0964", "agla", "vakya\u0964"])
    assert len(build_sentences(words)) == 2


def test_long_run_without_punctuation_splits_at_pause():
    words = make_words([f"w{i}" for i in range(35)])
    for w in words[32:]:               # insert a 1.0s pause before word 32
        w["start"] = round(w["start"] + 1.0, 2)
        w["end"] = round(w["end"] + 1.0, 2)
    s = build_sentences(words)
    assert len(s) == 2
    assert s[0]["n_words"] == 32


def test_hard_cap_splits_even_without_pause():
    words = make_words([f"w{i}" for i in range(130)])
    s = build_sentences(words)
    assert max(x["n_words"] for x in s) <= 60


def test_pause_after():
    words = [W("One.", 0.0), W("Two.", 1.0)]
    s = build_sentences(words)
    assert s[0]["pause_after"] == 0.7
    assert s[1]["pause_after"] is None


def test_forced_split_flag():
    words = make_words([f"w{i}" for i in range(70)])
    s = build_sentences(words)
    assert s[0]["forced_split"] is True


def test_normal_sentence_not_forced():
    s = build_sentences(make_words(["Hello", "there."]))
    assert s[0]["forced_split"] is False