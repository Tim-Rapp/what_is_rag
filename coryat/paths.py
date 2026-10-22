"""Project paths, resolved from the repo root so commands work from any directory."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
EVALSETS_DIR = ROOT / "evalsets"
RESULTS_DIR = ROOT / "results"

DATA_FILE = DATA_DIR / "combined_season1-42.tsv"
