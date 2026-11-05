from src.narrative.cues import (
    is_question, start_dangle_score, end_dangle_score, annotate,
)


def test_question():
    assert is_question("What happens?")
    assert not is_question("That happens.")


def test_start_connective_is_dangling():
    assert start_dangle_score("and they just pushed you.") == 1.0
    assert start_dangle_score("But that was different.") == 1.0


def test_start_anaphora_is_weaker():
    assert start_dangle_score("This is why it matters.") == 0.5


def test_start_lowercase_without_connective():
    assert start_dangle_score("eight hours in a day, I am sure.") == 0.5


def test_clean_start():
    assert start_dangle_score("Most of the people around you are poisoned.") == 0.0


def test_end_trailing_comma():
    assert end_dangle_score("Hello everyone, welcome back and in this video,") == 1.0


def test_end_trailing_connective():
    assert end_dangle_score("We tried it because.") == 0.9


def test_end_setup_phrase():
    assert end_dangle_score("Most people are poisoned because think about this.") == 0.8


def test_end_question():
    assert end_dangle_score("Do you know why?") == 0.7


def test_clean_end():
    assert end_dangle_score("You need to just disappear for everyone.") == 0.0


def test_annotate_adds_fields():
    out = annotate([{"text": "What happens?"}])
    assert out[0]["is_question"] is True
    assert out[0]["dangle_end"] >= 0.7
    assert out[0]["dangle_start"] == 0.0

def test_forced_split_marks_both_sides():
    out = annotate([
        {"text": "a long thought with no ending", "forced_split": True},
        {"text": "continues here.", "forced_split": False},
    ])
    assert out[0]["dangle_end"] == 1.0
    assert out[1]["dangle_start"] == 1.0