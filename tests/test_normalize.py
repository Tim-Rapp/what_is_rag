import pytest

from coryat.normalize import gold_variants, is_correct, normalize


@pytest.mark.parametrize(
    "response, gold",
    [
        # Question form is optional
        ("Who is Abraham Lincoln?", "Abraham Lincoln"),
        ("Abraham Lincoln", "Abraham Lincoln"),
        ("what are loch", "loch"),
        ("Who was Molson?", "Molson"),
        ("What's the Jordan?", "the Jordan"),
        # Case, punctuation, whitespace
        ("ABRAHAM   LINCOLN.", "Abraham Lincoln"),
        ("What is upside down?", "upside-down"),
        ('What is "Aloha Oe"?', '"Aloha Oe"'),
        ("Who is O'Brien?", "O'Brien"),
        # Leading articles
        ("What is Jordan?", "the Jordan"),
        ("What is the Caspian Sea?", "Caspian Sea"),
        # Accents
        ("Who is Antonio Carlos Jobim?", "Antônio Carlos Jobim"),
        # Ampersand
        ("What is Procter and Gamble?", "Procter & Gamble"),
        # Parenthetical rule: full form and parenthetical removed
        ("Who is Lincoln?", "(Abraham) Lincoln"),
        ("Who is Abraham Lincoln?", "(Abraham) Lincoln"),
        ("Who is Hinton?", "(S.E.) Hinton"),
        ("What is AOC?", "AOC (Alexandria Ocasio-Cortez)"),
        # Titles that look like questions
        ("Who's Afraid of Virginia Woolf?", "Who's Afraid of Virginia Woolf?"),
        ("What is Who's Afraid of Virginia Woolf?", "Who's Afraid of Virginia Woolf?"),
    ],
)
def test_correct(response, gold):
    assert is_correct(response, gold)


@pytest.mark.parametrize(
    "response, gold",
    [
        # Exact match only: near misses are wrong
        ("Who is John Adams?", "John Quincy Adams"),
        ("Who is Lincoln?", "Abraham Lincoln"),  # no surname rule without parentheses
        ("Who is Shakespear?", "Shakespeare"),
        ("What are lochs?", "loch"),
        # Parenthetical content alone is not the answer
        ("Who is Abraham?", "(Abraham) Lincoln"),
        # Empty or unanswered
        ("", "Abraham Lincoln"),
        ("?", "Abraham Lincoln"),
        ("What is", "the Jordan"),
    ],
)
def test_incorrect(response, gold):
    assert not is_correct(response, gold)


def test_normalize_is_idempotent():
    for text in ["What is the Jordan?", "Antônio Carlos Jobim", "Procter & Gamble", "upside-down"]:
        assert normalize(normalize(text)) == normalize(text)


def test_gold_variants():
    assert gold_variants("(Abraham) Lincoln") == {"abraham lincoln", "lincoln"}
    assert gold_variants("the Jordan") == {"jordan"}
