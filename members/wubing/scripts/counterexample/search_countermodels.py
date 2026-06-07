from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))
    sys.path.insert(0, str(repo_root))

from math_distill_stage2.counterexample import (
    create_countermodel_search_run,
    latest_public_eval_uncovered_negatives,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--problem-index",
        type=Path,
        default=Path("data/processed/public_problem_index.jsonl"),
    )
    parser.add_argument(
        "--uncovered-negatives",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("artifacts/runs"),
    )
    parser.add_argument("--max-order", type=int, default=2)
    parser.add_argument("--max-problems", type=int)
    parser.add_argument("--run-id")
    parser.add_argument("--created-at-utc")
    args = parser.parse_args()
    uncovered_negatives = args.uncovered_negatives or latest_public_eval_uncovered_negatives(
        args.output_root
    )

    result = create_countermodel_search_run(
        problem_index_path=args.problem_index,
        uncovered_negatives_path=uncovered_negatives,
        output_root=args.output_root,
        max_order=args.max_order,
        max_problems=args.max_problems,
        run_id=args.run_id,
        created_at_utc=args.created_at_utc,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
