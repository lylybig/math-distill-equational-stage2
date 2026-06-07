from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))
    sys.path.insert(0, str(repo_root))

from math_distill_stage2.public_eval import create_public_eval_run


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--problem-index",
        type=Path,
        default=Path("data/processed/public_problem_index.jsonl"),
    )
    parser.add_argument(
        "--implications",
        type=Path,
        default=Path("data/processed/etp/etp_implications.jsonl"),
    )
    parser.add_argument(
        "--facts",
        type=Path,
        default=Path("data/processed/etp/etp_facts.jsonl"),
    )
    parser.add_argument(
        "--countermodels",
        type=Path,
        help="Optional countermodels.jsonl from scripts/counterexample/search_countermodels.py.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("artifacts/runs"),
    )
    parser.add_argument("--run-id")
    parser.add_argument("--created-at-utc")
    args = parser.parse_args()

    result = create_public_eval_run(
        problem_index_path=args.problem_index,
        implications_path=args.implications,
        facts_path=args.facts,
        output_root=args.output_root,
        countermodels_path=args.countermodels,
        run_id=args.run_id,
        created_at_utc=args.created_at_utc,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
