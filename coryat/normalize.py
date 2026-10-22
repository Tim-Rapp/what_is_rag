"""Exact-match grading after light cleanup.

A response is correct when, after normalization, it equals the gold response
or one of its parenthetical variants. Only content is graded: the response
doesn't need to be phrased as a question, but it may be.

Parenthetical rule: "(Abraham) Lincoln" accepts "Abraham Lincoln" and "Lincoln".
"""

import re
import unicodedata

# "What is", "who are", "where was", ... at the start of a response.
QUESTION_PREFIX = re.compile(r"^\s*(what|who|where|when|which)\s+(is|are|was|were)\s+", re.IGNORECASE)
# Contracted form: "what's", "who's", "where's" (straight or curly apostrophe).
QUESTION_CONTRACTION = re.compile(r"^\s*(what|who|where)['’]s\s+", re.IGNORECASE)
LEADING_ARTICLE = re.compile(r"^(a|an|the)\s+")
PARENTHETICAL = re.compile(r"\s*\([^)]*\)\s*")


def normalize(text: str) -> str:
    """Lowercase, strip accents and punctuation, drop a leading article."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().replace("&", " and ")
    text = re.sub(r"['’]", "", text)  # o'brien -> obrien, don't -> dont
    text = re.sub(r"[^a-z0-9\s]", " ", text)  # all other punctuation -> space
    text = " ".join(text.split())
    return LEADING_ARTICLE.sub("", text)


def strip_question_prefix(text: str) -> str:
    """Remove one leading question phrase, if there is one."""
    for pattern in (QUESTION_PREFIX, QUESTION_CONTRACTION):
        stripped = pattern.sub("", text, count=1)
        if stripped != text:
            return stripped
    return text


def gold_variants(gold: str) -> set[str]:
    """Normalized forms of the gold that count as correct."""
    variants = {
        gold,
        PARENTHETICAL.sub(" ", gold),  # "(Abraham) Lincoln" -> "Lincoln"
    }
    # normalize() drops the parentheses themselves, so the gold as written
    # also covers "Abraham Lincoln".
    return {v for v in map(normalize, variants) if v}


def is_correct(response: str, gold: str) -> bool:
    # Try the response with and without a question prefix, so a gold like
    # "Who's Afraid of Virginia Woolf?" still matches when answered bare.
    candidates = {normalize(response), normalize(strip_question_prefix(response))}
    candidates.discard("")
    return bool(candidates & gold_variants(gold))
