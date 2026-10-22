"""Closed-book baseline: ask a model each clue with no retrieval, then grade it.

The model sees only the category, the host's comments and the clue. It never
sees the dollar value or the air date.

Results go to results/<run-id>.jsonl, one line per clue. A rerun with the same
run ID skips clues already answered, so a crashed run resumes where it stopped
and a finished run costs nothing to report again.

Usage:
    uv run python -m coryat.run_closed_book --dry-run
    uv run python -m coryat.run_closed_book --limit 20
    uv run python -m coryat.run_closed_book
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import anthropic

from coryat.clues import ROUND_NAMES, Clue, load_by_ids
from coryat.normalize import is_correct
from coryat.paths import EVALSETS_DIR, RESULTS_DIR

DEFAULT_MODEL = "claude-haiku-5-5"
PROMPT_VERSION = 1  # bump when SYSTEM_PROMPT or build_prompt changes
SYSTEM_PROMPT = "You are a Jeopardy! contestant. Reply with only your answer, no explanation."
MAX_TOKENS = 64
# No temperature: newer Claude models reject non-default values with a 400.


def build_prompt(clue: Clue) -> str:
    lines = [f"Category: {clue.category}"]
    if clue.comments:
        lines.append(clue.comments)
    lines.append(f"Clue: {clue.clue_text}")
    return "\n".join(lines)


def ask(client: anthropic.Anthropic, model: str, clue: Clue) -> dict:
    message = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_prompt(clue)}],
    )
    text = "".join(block.text for block in message.content if block.type == "text")
    return {
        "response": text.strip(),
        "input_tokens": message.usage.input_tokens,
        "output_tokens": message.usage.output_tokens,
    }


def read_results(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def report(results: list[dict]) -> None:
    """Grade from the stored responses, so grader changes apply to old runs too."""
    if not results:
        print("No results yet.")
        return

    graded = [(r, is_correct(r["response"], r["gold"])) for r in results]
    correct = sum(ok for _, ok in graded)
    print(f"\nAccuracy: {correct}/{len(graded)} = {correct / len(graded):.1%}")

    by_round: dict[int, list[bool]] = defaultdict(list)
    for r, ok in graded:
        by_round[r["round"]].append(ok)
    for round_ in sorted(by_round):
        oks = by_round[round_]
        print(f"  {ROUND_NAMES[round_]:<7} {sum(oks)}/{len(oks)} = {sum(oks) / len(oks):.1%}")

    tokens_in = sum(r["input_tokens"] for r in results)
    tokens_out = sum(r["output_tokens"] for r in results)
    print(f"Tokens: {tokens_in:,} in, {tokens_out:,} out")

    misses = [r for r, ok in graded if not ok]
    if misses:
        print(f"\nFirst {min(20, len(misses))} misses (response | gold):")
        for r in misses[:20]:
            print(f"  {r['response']!r:<45} | {r['gold']!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Closed-book Jeopardy! baseline")
    parser.add_argument("--set", default="dev", choices=["dev", "test"], help="eval set (default: dev)")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--run-id", help="results file name (default: <set>_<model>_p<prompt version>)")
    parser.add_argument("--limit", type=int, help="only answer the first N clues of the set")
    parser.add_argument("--dry-run", action="store_true", help="print 3 prompts and exit, no API calls")
    parser.add_argument("--allow-test", action="store_true", help="required to run on the test set")
    args = parser.parse_args()

    if args.set == "test" and not args.allow_test:
        sys.exit("The test set is held out. Pass --allow-test if you really mean it.")

    ids_path = EVALSETS_DIR / f"{args.set}.txt"
    if not ids_path.exists():
        sys.exit(f"{ids_path} not found. Run: uv run python -m coryat.sample")
    clues = load_by_ids(ids_path.read_text().split())
    if args.limit:
        clues = clues[: args.limit]

    if args.dry_run:
        print(f"SYSTEM: {SYSTEM_PROMPT}\n")
        for clue in clues[:3]:
            print(f"{build_prompt(clue)}\n  (gold: {clue.gold})\n")
        return

    run_id = args.run_id or f"{args.set}_{args.model}_p{PROMPT_VERSION}"
    results_path = RESULTS_DIR / f"{run_id}.jsonl"
    RESULTS_DIR.mkdir(exist_ok=True)

    done = {r["clue_id"] for r in read_results(results_path)}
    todo = [clue for clue in clues if clue.id not in done]
    print(f"Run {run_id}: {len(clues)} clues, {len(done & {c.id for c in clues})} already done, {len(todo)} to ask")

    if todo:
        client = anthropic.Anthropic(max_retries=5)  # reads ANTHROPIC_API_KEY
        with open(results_path, "a", encoding="utf-8") as out:
            for n, clue in enumerate(todo, 1):
                answer = ask(client, args.model, clue)
                record = {
                    "clue_id": clue.id,
                    "round": clue.round,
                    "category": clue.category,
                    "clue": clue.clue_text,
                    "gold": clue.gold,
                    "model": args.model,
                    "prompt_version": PROMPT_VERSION,
                    **answer,
                }
                out.write(json.dumps(record) + "\n")
                out.flush()  # every answer is saved even if the run dies
                if n % 25 == 0 or n == len(todo):
                    print(f"  {n}/{len(todo)}")

    wanted = {clue.id for clue in clues}
    report([r for r in read_results(results_path) if r["clue_id"] in wanted])


if __name__ == "__main__":
    main()
