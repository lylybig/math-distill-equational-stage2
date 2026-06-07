from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))

from math_distill_stage2.proof_bank.candidate_sampling import sample_candidate_pool


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sample a Stage 2 proof bank candidate pool with train-first strata and direct order4 true exploration."
    )
    parser.add_argument("--bank", type=Path, required=True)
    parser.add_argument("--output-pool", type=Path, required=True)
    parser.add_argument("--output-manifest", type=Path)
    parser.add_argument("--pool-id", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--high-signal-pool", type=Path, action="append", default=[])
    parser.add_argument("--unsolved-pool", type=Path, action="append", default=[])
    parser.add_argument("--order4-source", type=Path)
    parser.add_argument("--repair-from-bank", action="store_true")
    parser.add_argument("--max-attempts-per-problem", type=int, default=3)
    parser.add_argument("--allow-existing-accepted", action="store_true")
    parser.add_argument(
        "--sampling-strategy",
        choices=("default", "recovery-after-zero-yield"),
        default="default",
    )
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    output_manifest = args.output_manifest
    if output_manifest is None:
        output_manifest = args.output_pool.with_suffix(".manifest.json")
    summary = sample_candidate_pool(
        bank=args.bank,
        output_pool=args.output_pool,
        output_manifest=output_manifest,
        pool_id=args.pool_id,
        seed=args.seed,
        limit=args.limit,
        high_signal_pools=args.high_signal_pool,
        unsolved_pools=args.unsolved_pool,
        order4_source=args.order4_source,
        repair_from_bank=args.repair_from_bank,
        max_attempts_per_problem=args.max_attempts_per_problem,
        allow_existing_accepted=args.allow_existing_accepted,
        sampling_strategy=args.sampling_strategy,
        overwrite=args.overwrite,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
