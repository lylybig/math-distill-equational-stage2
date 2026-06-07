from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))
    sys.path.insert(0, str(repo_root))

from math_distill_stage2.counterexample.verified_index import build_verified_counterexample_index


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--problem-index",
        type=Path,
        default=Path("data/processed/public_problem_index.jsonl"),
    )
    parser.add_argument(
        "--countermodels",
        type=Path,
        required=True,
        help="countermodels.jsonl from scripts/counterexample/search_countermodels.py.",
    )
    parser.add_argument(
        "--certificate-run",
        type=Path,
        required=True,
        help="Run directory produced by scripts/counterexample/generate_countermodel_certificates.py.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output JSONL path. Defaults to <certificate-run>/verified_counterexamples.jsonl.",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        help="Output summary JSON path. Defaults to <output>.summary.json.",
    )
    args = parser.parse_args()

    output = args.output or (args.certificate_run / "verified_counterexamples.jsonl")
    summary = build_verified_counterexample_index(
        problem_index_path=args.problem_index,
        countermodels_path=args.countermodels,
        certificate_run_dir=args.certificate_run,
        output_path=output,
        summary_output_path=args.summary_output,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
