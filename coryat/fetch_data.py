"""Download the Jeopardy! clue dataset into data/.

The download is pinned to one commit of jwolle1/jeopardy_clue_dataset and
checked against a SHA-256, so every run uses exactly the same clues.

Usage:
    uv run python -m coryat.fetch_data
"""

import hashlib
import sys
import urllib.request

from coryat.paths import DATA_FILE

REPO = "jwolle1/jeopardy_clue_dataset"
COMMIT = "5a2026f465cfd9f2b80a478bd1993c9a2223befc"  # v42, seasons 1-42 (July 2026)
SHA256 = "e5e336af75210f9ecfdd68201201d9acea269ea6be8d3dc445e98bf31399c2e2"
URL = f"https://raw.githubusercontent.com/{REPO}/{COMMIT}/{DATA_FILE.name}"


def sha256_of(path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    if DATA_FILE.exists() and sha256_of(DATA_FILE) == SHA256:
        print(f"Already have {DATA_FILE} (checksum OK)")
        return

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    partial = DATA_FILE.with_suffix(".part")
    print(f"Downloading {URL} (~80 MB)...")
    urllib.request.urlretrieve(URL, partial)

    actual = sha256_of(partial)
    if actual != SHA256:
        partial.unlink()
        sys.exit(f"Checksum mismatch: expected {SHA256}, got {actual}")

    partial.rename(DATA_FILE)
    print(f"Saved {DATA_FILE}")


if __name__ == "__main__":
    main()
