"""Build the dev and test eval sets as lists of clue IDs.

The sample is seeded, so the same dataset always gives the same sets. Existing
set files are never overwritten unless you pass --force, which keeps the test
set from quietly changing under you.

Usage:
    uv run python -m coryat.sample
"""

import argparse
import random
import sys

from coryat.clues import load_filtered
from coryat.paths import EVALSETS_DIR

SEED = 42
DEV_SIZE = 500
TEST_SIZE = 100


def write_ids(name: str, ids: list[str]) -> None:
    path = EVALSETS_DIR / f"{name}.txt"
    path.write_text("\n".join(ids) + "\n")
    print(f"Wrote {len(ids)} IDs to {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--force", action="store_true", help="overwrite existing sets")
    args = parser.parse_args()

    existing = [p for p in (EVALSETS_DIR / "dev.txt", EVALSETS_DIR / "test.txt") if p.exists()]
    if existing and not args.force:
        sys.exit(f"{existing[0]} already exists. Pass --force to replace the eval sets.")

    clues, excluded = load_filtered()
    print(f"Eligible clues: {len(clues):,}")
    for reason, count in excluded.most_common():
        print(f"  excluded {reason}: {count:,}")

    # Sort first so the sample depends only on the seed, not on file order.
    ids = sorted(clue.id for clue in clues)
    picked = random.Random(SEED).sample(ids, DEV_SIZE + TEST_SIZE)

    EVALSETS_DIR.mkdir(exist_ok=True)
    write_ids("dev", picked[:DEV_SIZE])
    write_ids("test", picked[DEV_SIZE:])


if __name__ == "__main__":
    main()
