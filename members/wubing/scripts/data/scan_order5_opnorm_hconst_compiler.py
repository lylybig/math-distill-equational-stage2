#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))

from math_distill_stage2.heavy_task_lock import (  # noqa: E402
    HeavyTaskLockError,
    add_heavy_task_lock_args,
    heavy_task_lock_from_args,
)
from math_distill_stage2.order5_opnorm_hconst_scan import (  # noqa: E402
    CANDIDATE_KEY,
    explicit_hits_delta_from_profile,
    iter_jsonl,
    load_equations,
    scan_sample,
    summarize_hits,
)


DEFAULT_EQUATIONS_PATH = Path(
    "external/equational-theories-lean-stage2/examples/problems/eq_size5.txt"
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan a JSONL sample for order5 opnorm hconst match-collapse "
            "compiler hits. This is candidate-layer mining only."
        )
    )
    parser.add_argument("--sample", type=Path, default=None)
    parser.add_argument(
        "--existing-hits",
        type=Path,
        default=None,
        help="Use an existing hits JSONL and only recompute summary/profile delta.",
    )
    parser.add_argument("--hits-output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    parser.add_argument("--equations-file", type=Path, default=DEFAULT_EQUATIONS_PATH)
    parser.add_argument(
        "--require-mul-roots",
        action="store_true",
        help="Skip pairs unless both source and target equations have product roots.",
    )
    parser.add_argument(
        "--max-candidates-per-pair",
        type=int,
        default=8,
        help="Stop after this many generated proof candidates per pair.",
    )
    parser.add_argument(
        "--include-code",
        action="store_true",
        help="Include generated Lean certificate code in the hits JSONL.",
    )
    parser.add_argument("--max-records", type=int, default=0)
    parser.add_argument(
        "--coverage-profile",
        type=Path,
        default=None,
        help=(
            "Optional current registry coverage profile used to compute exact "
            "overlap/union increment for the scanned explicit hit set."
        ),
    )
    add_heavy_task_lock_args(parser)
    args = parser.parse_args(argv)

    try:
        with heavy_task_lock_from_args(args):
            summary = _run(args)
    except HeavyTaskLockError as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _run(args: argparse.Namespace) -> dict:
    if args.existing_hits is not None:
        hits = list(iter_jsonl(args.existing_hits))
        summary_bits = summarize_hits(hits)
        summary_bits["stats"] = {
            "compiler_hit_count": len(hits),
            "loaded_existing_hits_count": len(hits),
        }
    else:
        if args.sample is None:
            raise SystemExit("--sample is required unless --existing-hits is provided")
        equations = load_equations(args.equations_file)
        hits, summary_bits = scan_sample(
            args.sample,
            equations=equations,
            require_mul_roots=bool(args.require_mul_roots),
            max_candidates_per_pair=int(args.max_candidates_per_pair),
            include_code=bool(args.include_code),
            max_records=int(args.max_records),
        )

    args.hits_output.parent.mkdir(parents=True, exist_ok=True)
    args.hits_output.write_text(
        "\n".join(json.dumps(hit, ensure_ascii=False, sort_keys=True) for hit in hits)
        + ("\n" if hits else ""),
        encoding="utf-8",
    )
    delta_summary = None
    if args.coverage_profile is not None:
        profile = json.loads(args.coverage_profile.read_text(encoding="utf-8"))
        delta_summary = explicit_hits_delta_from_profile(profile, hits, verdict=True)
    stats = summary_bits["stats"]

    summary = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_key": CANDIDATE_KEY,
        "sample_path": str(args.sample) if args.sample else None,
        "existing_hits": str(args.existing_hits) if args.existing_hits else None,
        "equations_path": str(args.equations_file),
        "hits_path": str(args.hits_output),
        "require_mul_roots": bool(args.require_mul_roots),
        "max_candidates_per_pair": int(args.max_candidates_per_pair),
        "coverage_profile": str(args.coverage_profile) if args.coverage_profile else None,
        "sample_explicit_delta_summary": delta_summary,
        "stats": dict(stats),
        "compiler_hit_rate_within_scanned": (
            round(stats["compiler_hit_count"] / stats.get("compiler_scan_count", 0), 6)
            if stats.get("compiler_scan_count", 0)
            else 0
        ),
        "hit_stratum_counts": summary_bits["hit_stratum_counts"],
        "top_hit_shape_buckets": summary_bits["top_hit_shape_buckets"],
        "registry_status": "sample_scan_only_not_exact_union_increment",
        "next_step": (
            "Use the hits as a source/shape-pruned universe for exact current "
            "registry union-increment computation before register-layer merge."
        ),
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return summary


if __name__ == "__main__":
    raise SystemExit(main())
