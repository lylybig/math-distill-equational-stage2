from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))

from math_distill_stage2.order5_paircheck_bank import (
    build_paircheck_bank_artifacts,
    write_paircheck_bank,
)
from math_distill_stage2.order5_spine_smoke import (
    DEFAULT_EQ_SIZE5_PATH,
    DEFAULT_ORDER4_MAX_ID,
)
from math_distill_stage2.order5_strategy_registry import build_default_order5_strategy_registry
from math_distill_stage2.order5_strategy_registry import Order5StrategyRegistry


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build order5 paircheck bank artifacts from sampled unresolved pairs."
    )
    parser.add_argument(
        "--countermodels",
        type=Path,
        help="Existing countermodels JSONL to convert directly into verified_bank.jsonl.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed/order5_paircheck_bank"),
    )
    parser.add_argument("--equations-file", type=Path, default=DEFAULT_EQ_SIZE5_PATH)
    parser.add_argument(
        "--model-manifest",
        type=Path,
        default=Path("data/processed/order5_strategy_registry/strategies.json"),
    )
    parser.add_argument("--sample-size", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--order4-max-id", type=int, default=DEFAULT_ORDER4_MAX_ID)
    parser.add_argument("--model-limit", type=int)
    parser.add_argument(
        "--enumerate-model-order",
        type=int,
        action="append",
        default=[],
        help="Add all finite magma tables of this order to the paircheck model pool.",
    )
    parser.add_argument(
        "--enumerate-model-limit",
        type=int,
        help="Optional per-order cap for --enumerate-model-order.",
    )
    parser.add_argument("--smoke-limit", type=int, default=100)
    parser.add_argument("--max-scan-attempts", type=int)
    parser.add_argument(
        "--false-only-registry",
        action="store_true",
        help=(
            "Build only false finite-model setcheck strategies for candidate "
            "filtering. This skips true proofbank/template registry construction "
            "and is intended for fast paircheck exploration."
        ),
    )
    parser.add_argument(
        "--empty-registry",
        action="store_true",
        help=(
            "Do not filter sampled pairs through the current registry. This is "
            "only for pipeline smoke and does not estimate unresolved increment."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if args.countermodels is not None:
        rows = [
            json.loads(line)
            for line in args.countermodels.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        summary = write_paircheck_bank(rows, output_dir=args.output_dir)
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    if args.empty_registry:
        law_count = sum(
            1
            for line in args.equations_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
        registry = Order5StrategyRegistry(law_count=law_count, strategies=[])
    else:
        registry = build_default_order5_strategy_registry(
            equations_path=args.equations_file,
            order4_max_id=args.order4_max_id,
            include_true_strategies=not args.false_only_registry,
        )
    summary = build_paircheck_bank_artifacts(
        registry=registry,
        equations_path=args.equations_file,
        model_manifest_path=args.model_manifest,
        output_dir=args.output_dir,
        sample_size=args.sample_size,
        seed=args.seed,
        order4_max_id=args.order4_max_id,
        model_limit=args.model_limit,
        enumerate_model_orders=args.enumerate_model_order,
        enumerate_model_limit=args.enumerate_model_limit,
        smoke_limit=args.smoke_limit,
        max_scan_attempts=args.max_scan_attempts,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
