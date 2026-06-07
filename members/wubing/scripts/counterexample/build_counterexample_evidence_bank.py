from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))
    sys.path.insert(0, str(repo_root))

from math_distill_stage2.counterexample.evidence import build_counterexample_evidence_bank


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--asset-root",
        type=Path,
        default=Path("data/assets/counterexamples"),
        help="Counterexample asset root containing per-problem folders.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output evidence JSONL path for offline solver analysis.",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        help="Output summary JSON path. Defaults to <output>.summary.json.",
    )
    parser.add_argument(
        "--include-unverified",
        action="store_true",
        help="Include assets whose latest.json has verified=false.",
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--max-certificate-chars",
        type=int,
        default=0,
        help="Optional Lean certificate excerpt length. Default keeps prompts compact.",
    )
    args = parser.parse_args()

    summary_output = args.summary_output or args.output.with_suffix(args.output.suffix + ".summary.json")
    summary = build_counterexample_evidence_bank(
        asset_root=args.asset_root,
        output_path=args.output,
        summary_output_path=summary_output,
        verified_only=not args.include_unverified,
        limit=args.limit,
        max_certificate_chars=args.max_certificate_chars,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
