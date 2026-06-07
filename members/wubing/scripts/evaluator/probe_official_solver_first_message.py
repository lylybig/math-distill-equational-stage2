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

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.order5_pair_dataset import DEFAULT_EQUATIONS_PATH, read_equations
from math_distill_stage2.solver_probe import (
    DEFAULT_SOLVER_PATH,
    probe_candidate_rows,
    summarize_solver_probe_rows,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Probe the first Solo solver message for candidate Stage 2 problem rows."
    )
    parser.add_argument("--input", type=Path, required=True, help="Input candidate JSONL.")
    parser.add_argument("--output", type=Path, required=True, help="Output JSONL with probe rows.")
    parser.add_argument("--summary", type=Path, required=True, help="Output summary JSON.")
    parser.add_argument("--solver", type=Path, default=DEFAULT_SOLVER_PATH)
    parser.add_argument("--equations", type=Path, default=DEFAULT_EQUATIONS_PATH)
    parser.add_argument("--expected-verdict", choices=("true", "false"), default=None)
    parser.add_argument("--timeout-seconds", type=float, default=5.0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--max-workers", type=int, default=1)
    parser.add_argument(
        "--representative-pair-key",
        default=None,
        help="For model-level rows, choose a representative_pairs key before fallback order.",
    )
    args = parser.parse_args()

    equations = read_equations(args.equations)
    rows = read_jsonl(args.input)
    probed_rows = probe_candidate_rows(
        rows,
        solver_path=args.solver,
        equations=equations,
        expected_verdict=args.expected_verdict,
        timeout_seconds=args.timeout_seconds,
        limit=args.limit,
        representative_pair_key=args.representative_pair_key,
        max_workers=args.max_workers,
    )
    write_jsonl(args.output, probed_rows)

    summary = summarize_solver_probe_rows(
        probed_rows,
        expected_verdict=args.expected_verdict,
    )
    summary.update(
        {
            "input_path": str(args.input),
            "output_path": str(args.output),
            "solver_path": str(args.solver),
            "equations_path": str(args.equations),
            "timeout_seconds": args.timeout_seconds,
            "limit": args.limit,
            "representative_pair_key": args.representative_pair_key,
            "max_workers": args.max_workers,
        }
    )
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print(
        "Solver probe: "
        f"{summary['expected_fast_count']}/{summary['total_count']} "
        f"fast {args.expected_verdict or 'expected'} hits; "
        f"solver_uncovered={summary['solver_uncovered_count']}; "
        f"summary={args.summary}"
    )


if __name__ == "__main__":
    main()
