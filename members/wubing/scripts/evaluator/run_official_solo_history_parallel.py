#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))
    sys.path.insert(0, str(repo_root))

from math_distill_stage2.official_stage2_history import (
    DEFAULT_OFFICIAL_STAGE2_REPO,
    DEFAULT_OUTPUT_ROOT,
    DEFAULT_SOLO_SUBMISSION,
    PROBLEM_SUITES,
    default_run_id,
    resolve_problem_sets,
    run_official_solo_history_parallel,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run official Stage 2 Solo evaluation with one runner shard per problem."
    )
    parser.add_argument("--submission", type=Path, default=DEFAULT_SOLO_SUBMISSION)
    parser.add_argument("--official-repo", type=Path, default=DEFAULT_OFFICIAL_STAGE2_REPO)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--suite", choices=sorted(PROBLEM_SUITES), default="sample200")
    parser.add_argument(
        "--problem-set",
        type=Path,
        action="append",
        default=[],
        help="Problem JSON/JSONL path. May be repeated. Overrides --suite when present.",
    )
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Maximum number of per-problem official runner shards to run at once.",
    )
    parser.add_argument(
        "--problems-per-shard",
        type=int,
        default=1,
        help="Number of problems to send to each official runner shard.",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help=(
            "Enable evaluator-side caches under this directory "
            "(exact_results.sqlite and judge_calls.sqlite)."
        ),
    )
    args = parser.parse_args()

    problem_sets = resolve_problem_sets(
        official_repo=args.official_repo,
        suite=args.suite,
        explicit_problem_sets=args.problem_set,
    )
    run_id = args.run_id or default_run_id(f"{args.suite}-parallel")
    run_dir = args.output_root / run_id

    rows = run_official_solo_history_parallel(
        submission_dir=args.submission,
        problem_sets=problem_sets,
        run_dir=run_dir,
        official_repo=args.official_repo,
        config_path=args.config,
        max_workers=args.max_workers,
        problems_per_shard=args.problems_per_shard,
        cache_dir=args.cache_dir,
    )
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))

    print("\nParallel history-style artifacts")
    print(f"  Run dir:     {run_dir}")
    print(f"  Summary:     {run_dir / 'summary.json'}")
    print(f"  History:     {run_dir / 'history.md'}")
    print(f"  Max workers: {max(1, args.max_workers)}")
    print(f"  Shard size:  {max(1, args.problems_per_shard)}")
    if args.cache_dir is not None:
        print(f"  Cache dir:   {args.cache_dir}")
    print(
        "  Result:      "
        f"{summary['accepted']}A / {summary['rejected']}R / {summary['errors']}E "
        f"over {summary['totalProblems']} problems"
    )
    if len(rows) > 1:
        print("  Sets:        " + ", ".join(f"{row['problemSet']}={row['metricsText']}" for row in rows))


if __name__ == "__main__":
    main()
