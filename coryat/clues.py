"""Load, clean and filter Jeopardy! clues from the dataset TSV.

Column gotcha: the dataset follows the show's convention, so the TSV column
"answer" holds the clue text and "question" holds the correct response. They
are renamed to clue_text and gold here, and nothing else uses the raw names.
"""

import csv
import hashlib
import html
import re
from collections import Counter
from dataclasses import dataclass

from coryat.normalize import gold_variants
from coryat.paths import DATA_FILE

ROUND_NAMES = {1: "Single", 2: "Double", 3: "Final"}

# Clues that depend on images, audio or video. The dataset author already
# removed most of these; this catches what's left.
MEDIA_PATTERN = re.compile(
    r"\b(seen here|shown here|heard here|pictured here|clue crew|this video)\b",
    re.IGNORECASE,
)

# Clues whose correct response may have changed since air date. Deliberately
# broad: it also catches some "electric current" clues, and losing a few
# good clues is cheaper than grading against stale answers.
TIME_PATTERN = re.compile(
    r"\b(current|currently|presently|at present|nowadays|as of this writing)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Clue:
    id: str
    round: int  # 1 Single, 2 Double, 3 Final
    category: str
    comments: str  # host's note about the category, often empty
    clue_text: str
    gold: str
    air_date: str  # kept for analysis only; never shown to the model


def clean(text: str) -> str:
    """Undo the dataset's escaping: backslash-escaped quotes and HTML entities."""
    text = text.replace('\\"', '"').replace("\\'", "'")
    return html.unescape(text).strip()


def make_id(air_date: str, round_: str, category: str, clue_text: str) -> str:
    """Stable 12-char ID, so eval sets can be stored as ID lists."""
    key = "|".join([air_date, round_, category, clue_text])
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def exclusion_reason(clue: Clue) -> str | None:
    """Why a clue is excluded from eval sets, or None to keep it."""
    # No clue, or a gold like "@" that normalizes to nothing and can't be graded.
    if not clue.clue_text or not gold_variants(clue.gold):
        return "ungradable"
    if MEDIA_PATTERN.search(clue.clue_text):
        return "media"
    if TIME_PATTERN.search(clue.clue_text):
        return "time_sensitive"
    return None


def load_all(path=DATA_FILE) -> list[Clue]:
    """Every clue in the file, cleaned. Duplicate IDs keep the first copy."""
    clues: dict[str, Clue] = {}
    with open(path, encoding="utf-8", newline="") as f:
        # QUOTE_NONE: quote characters inside fields are literal text.
        for row in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            category = clean(row["category"])
            clue_text = clean(row["answer"])
            clue_id = make_id(row["air_date"], row["round"], category, clue_text)
            if clue_id in clues:
                continue
            clues[clue_id] = Clue(
                id=clue_id,
                round=int(row["round"]),
                category=category,
                comments=clean(row["comments"]),
                clue_text=clue_text,
                gold=clean(row["question"]),
                air_date=row["air_date"],
            )
    return list(clues.values())


def load_filtered(path=DATA_FILE) -> tuple[list[Clue], Counter]:
    """Clues eligible for eval sets, plus a count of exclusions by reason."""
    kept: list[Clue] = []
    excluded: Counter = Counter()
    for clue in load_all(path):
        reason = exclusion_reason(clue)
        if reason:
            excluded[reason] += 1
        else:
            kept.append(clue)
    return kept, excluded


def load_by_ids(ids: list[str], path=DATA_FILE) -> list[Clue]:
    """Clues for an eval set, in the order the IDs are listed."""
    by_id = {clue.id: clue for clue in load_all(path)}
    missing = [i for i in ids if i not in by_id]
    if missing:
        raise KeyError(f"{len(missing)} IDs not found in {path}, e.g. {missing[:3]}")
    return [by_id[i] for i in ids]
