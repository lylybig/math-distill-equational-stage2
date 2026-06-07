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
    run_official_solo_history,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the official Stage 2 Solo runner and emit playground-history-style artifacts."
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
    args = parser.parse_args()

    problem_sets = resolve_problem_sets(
        official_repo=args.official_repo,
        suite=args.suite,
        explicit_problem_sets=args.problem_set,
    )
    run_id = args.run_id or default_run_id(args.suite)
    run_dir = args.output_root / run_id

    rows = run_official_solo_history(
        submission_dir=args.submission,
        problem_sets=problem_sets,
        run_dir=run_dir,
        official_repo=args.official_repo,
        config_path=args.config,
    )
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))

    print("\nHistory-style artifacts")
    print(f"  Run dir:  {run_dir}")
    print(f"  Summary:  {run_dir / 'summary.json'}")
    print(f"  History:  {run_dir / 'history.md'}")
    print(
        "  Result:   "
        f"{summary['accepted']}A / {summary['rejected']}R / {summary['errors']}E "
        f"over {summary['totalProblems']} problems"
    )
    if len(rows) > 1:
        print("  Sets:     " + ", ".join(f"{row['problemSet']}={row['metricsText']}" for row in rows))


if __name__ == "__main__":
    main()
