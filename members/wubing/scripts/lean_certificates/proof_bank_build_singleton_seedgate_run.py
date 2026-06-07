#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))

from math_distill_stage2.proof_bank.singleton_seedgate import (  # noqa: E402
    DEFAULT_EQ2_ID,
    DEFAULT_EQUATIONS_PATH,
    DEFAULT_SOURCE_SEED_CANDIDATES_PATH,
    build_singleton_seedgate_run,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build a deterministic binary-grind singleton seedgate proof-bank run "
            "from order5 true-template source seed candidates."
        )
    )
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument(
        "--source-seed-candidates",
        type=Path,
        default=DEFAULT_SOURCE_SEED_CANDIDATES_PATH,
    )
    parser.add_argument("--equations-file", type=Path, default=DEFAULT_EQUATIONS_PATH)
    parser.add_argument("--eq2-id", type=int, default=DEFAULT_EQ2_ID)
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--bank-attempts", type=Path)
    parser.add_argument(
        "--previous-run-dir",
        type=Path,
        action="append",
        default=[],
        help="Exclude problem keys already present in this run's input_problems.jsonl.",
    )
    parser.add_argument("--source-run-id")
    args = parser.parse_args(argv)

    summary = build_singleton_seedgate_run(
        run_dir=args.run_dir,
        source_seed_candidates_path=args.source_seed_candidates,
        equations_path=args.equations_file,
        eq2_id=args.eq2_id,
        limit=args.limit,
        bank_attempts_path=args.bank_attempts,
        previous_run_dirs=args.previous_run_dir,
        source_run_id=args.source_run_id,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
