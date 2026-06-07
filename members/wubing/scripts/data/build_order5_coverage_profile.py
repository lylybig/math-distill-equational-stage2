#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from math_distill_stage2.heavy_task_lock import (
    HeavyTaskLockError,
    add_heavy_task_lock_args,
    heavy_task_lock_from_args,
)
from math_distill_stage2.order5_coverage_profile import (
    build_coverage_profile,
    write_coverage_profile,
)
from math_distill_stage2.order5_strategy_registry import (
    DEFAULT_EQ_SIZE5_PATH,
    DEFAULT_SOURCE_TARGET_CACHE_PATH,
    build_default_order5_strategy_registry,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a compact order5 current coverage profile for fast candidate deltas."
    )
    parser.add_argument("--equations-file", type=Path, default=DEFAULT_EQ_SIZE5_PATH)
    parser.add_argument("--source-target-cache", type=Path, default=DEFAULT_SOURCE_TARGET_CACHE_PATH)
    parser.add_argument(
        "--output-json",
        type=Path,
        required=True,
        help="Path for the generated coverage profile JSON.",
    )
    add_heavy_task_lock_args(parser)
    args = parser.parse_args()

    try:
        with heavy_task_lock_from_args(args):
            summary = _run(args)
    except HeavyTaskLockError as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(summary, indent=2, sort_keys=True))


def _run(args: argparse.Namespace) -> dict:
    started_at = time.perf_counter()
    registry_started_at = time.perf_counter()
    registry = build_default_order5_strategy_registry(
        equations_path=args.equations_file,
        source_target_cache_path=(
            args.source_target_cache if args.source_target_cache.exists() else None
        ),
    )
    registry_build_seconds = time.perf_counter() - registry_started_at
    profile = build_coverage_profile(registry)
    profile["timings_seconds"]["registry_build"] = registry_build_seconds
    profile["timings_seconds"]["total"] = time.perf_counter() - started_at
    write_coverage_profile(profile, args.output_json)

    verdict_profiles = profile["verdict_profiles"]
    return {
        "output_json": str(args.output_json),
        "law_count": profile["law_count"],
        "false_source_target_group_count": verdict_profiles["false"][
            "source_target_group_count"
        ],
        "true_source_target_group_count": verdict_profiles["true"][
            "source_target_group_count"
        ],
        "false_explicit_pair_count": verdict_profiles["false"][
            "explicit_pair_count"
        ],
        "false_explicit_source_count": verdict_profiles["false"][
            "explicit_source_count"
        ],
        "true_explicit_pair_count": verdict_profiles["true"][
            "explicit_pair_count"
        ],
        "true_explicit_source_count": verdict_profiles["true"][
            "explicit_source_count"
        ],
        "timings_seconds": profile["timings_seconds"],
    }


if __name__ == "__main__":
    main()
