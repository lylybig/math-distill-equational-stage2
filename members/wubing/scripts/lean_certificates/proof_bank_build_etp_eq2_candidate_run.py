from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))

from math_distill_stage2.proof_bank.etp_candidate_import import (
    DEFAULT_ETP_EQ2_SOURCE_RUN_ID,
    build_etp_eq2_candidate_run,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Materialize accepted ETP Equation2 candidate rows as a proof-bank run."
    )
    parser.add_argument(
        "--accepted-sources",
        type=Path,
        default=Path(
            "data/processed/order5_strategy_registry/candidates/"
            "true_template_etp_order5_eq2_native_explicit_remote_accepted_sources_20260520.jsonl"
        ),
    )
    parser.add_argument(
        "--candidates-dir",
        type=Path,
        default=Path("data/processed/order5_strategy_registry/candidates"),
    )
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--source-run-id", default=DEFAULT_ETP_EQ2_SOURCE_RUN_ID)
    args = parser.parse_args(argv)

    summary = build_etp_eq2_candidate_run(
        accepted_sources_path=args.accepted_sources,
        candidates_dir=args.candidates_dir,
        run_dir=args.run_dir,
        source_run_id=args.source_run_id,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
