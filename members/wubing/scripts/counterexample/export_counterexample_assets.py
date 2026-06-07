from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))
    sys.path.insert(0, str(repo_root))

from math_distill_stage2.counterexample.assets import export_counterexample_assets


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verified-counterexamples",
        type=Path,
        required=True,
        help="verified_counterexamples.jsonl produced by build_verified_counterexample_index.py.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("data/assets/counterexamples"),
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--created-at-utc")
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify each generated certificate with bare lean.",
    )
    parser.add_argument("--verify-workers", type=int, default=4)
    args = parser.parse_args()

    summary = export_counterexample_assets(
        verified_counterexamples_path=args.verified_counterexamples,
        output_root=args.output_root,
        run_id=args.run_id,
        created_at_utc=args.created_at_utc,
        verify=args.verify,
        verify_workers=args.verify_workers,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
