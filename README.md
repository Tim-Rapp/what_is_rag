# What Is RAG?

An agentic Wikipedia RAG system for Jeopardy! clues, scored the way Jeopardy! contestants score themselves. The Python package is named `coryat`, after the scoring method.

**Status: phase 1, closed-book baseline.** The system loads the clues, asks a model each one with no retrieval, and grades the answers by exact match. Retrieval, an agent loop and richer evals come later.

## Closed-book

Closed-book means the model answers from what it learned in training only. It gets the category, the host's comments and the clue. It gets no search, no documents and no tools, and never sees the dollar value or the air date. This score is the baseline: when retrieval is added, the difference from closed-book shows what retrieval contributed.

## Quickstart

Requires [uv](https://docs.astral.sh/uv/) and an Anthropic API key. Run commands from the repo root.

```bash
uv sync
uv run pytest                                      # grader and loader tests

uv run python -m coryat.fetch_data                 # download the dataset (~80 MB) into data/
uv run python -m coryat.sample                     # only if evalsets/ is missing

export ANTHROPIC_API_KEY=
uv run python -m coryat.run_closed_book --dry-run  # see 3 prompts, no API calls
uv run python -m coryat.run_closed_book --limit 20 # cheap smoke test
uv run python -m coryat.run_closed_book            # full dev set (500 clues)
```

The run prints accuracy overall and by round, token totals, and the first 20 misses. Results are saved one line per clue in `results/<set>_<model>_p<prompt version>.jsonl`. Rerunning the same command skips clues already answered, so an interrupted run resumes where it stopped, and a finished run just prints the report again at no cost.

Calls run one at a time, so a full dev run takes several minutes. With a small model, a 500-clue run is well under a dollar in tokens.

## How grading works

Grading is exact match on content after light normalization, applied to both the response and the gold answer:

- lowercase, strip accents, `&` becomes `and`
- drop apostrophes, turn other punctuation into spaces, collapse whitespace
- drop a leading `a`, `an` or `the`
- the response may optionally start with "What is", "Who are", "What's" and similar

Question form isn't required; only the content is graded.

**One extra rule, for parentheticals:** a gold like `(Abraham) Lincoln` accepts both `Abraham Lincoln` and `Lincoln`.

Nothing else is accepted: no fuzzy matching, no surname-only answers, no alternates written as "X or Y". So "John Adams" is wrong when the gold is "John Quincy Adams," and so is "Lincoln" when the gold is plain "Abraham Lincoln." Expect the grader to undercount somewhat. Reading the printed misses shows by how much.

The report regrades from the stored responses every time, so grader changes apply to old runs too.

## Eval sets

`evalsets/dev.txt` (500 clues) and `evalsets/test.txt` (100 clues) are lists of clue IDs, sampled with a fixed seed from the filtered clues. Only IDs are committed; the clue text is rebuilt locally from the pinned dataset.

Clues are excluded when they:

- depend on images, audio or video ("seen here," "Clue Crew," and so on)
- may have a different answer today ("current," "currently," "presently," and so on). This filter is deliberately broad.
- have a gold answer that can't be graded (for example, "@")

**The test set is held out.** Day-to-day work runs on dev. The runner refuses `--set test` unless you also pass `--allow-test`. Test is meant to be run once per milestone, for closed-book and later RAG, and those are the numbers to report.

## Data

Clues come from [jwolle1/jeopardy_clue_dataset](https://github.com/jwolle1/jeopardy_clue_dataset): seasons 1 through 42 (July 2026), about 544,000 clues in `combined_season1-42.tsv`. `fetch_data.py` downloads that file pinned to commit `5a2026f` and verifies its SHA-256, so every run uses identical data.

Things to know about this dataset:

- The column named `answer` holds the clue and `question` holds the correct response, following the show's convention. The loader renames them to `clue_text` and `gold`.
- Quotes are backslash-escaped and some characters are HTML entities. The loader cleans both.
- The data is property of Jeopardy Productions, Inc., and the dataset's author asks that it not be used for a public-facing site, app or product. That's why this repo never commits clue text and stays a local research tool.

## Why not Inspect?

[Inspect](https://inspect.aisi.org.uk/) from the UK AI Security Institute is an open-source framework for LLM evals and would cover much of this harness. I chose not to use it, on purpose: the point of this project is to build the loader, grader, runner and reporting myself, and to understand each piece.

## Layout

```
coryat/
  paths.py            # repo-relative paths
  fetch_data.py       # pinned download + checksum
  clues.py            # load TSV, clean, filter
  sample.py           # seeded dev/test ID lists
  normalize.py        # exact-match grading
  run_closed_book.py  # ask, save, resume, report
tests/                # pytest
evalsets/             # dev.txt, test.txt (clue IDs only)
data/, results/       # gitignored
```

## Roadmap

1. Closed-book baseline (this phase)
2. Retrieval over Wikipedia: keyword search first, then a single-shot RAG run
3. Agent loop with search and read tools
4. Richer grading (alternates, fuzzy matching, a checked LLM judge) and Coryat scoring with abstention
