#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from math_distill_stage2.order5_coverage_profile import (
    coverage_delta_summary_from_profile,
    read_coverage_profile,
)
from math_distill_stage2.order5_pair_dataset import read_equations
from math_distill_stage2.order5_strategy_registry import (
    DEFAULT_EQ_SIZE5_PATH,
    DEFAULT_ORDER4_MAX_ID,
    DEFAULT_SOURCE_TARGET_CACHE_PATH,
    SourceTargetSetsRule,
    _product_anchor_sets,
    build_default_order5_strategy_registry,
)


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    raise ValueError(f"cannot parse verdict as bool: {value!r}")


def _read_candidate_row(
    path: Path,
    *,
    row_index: int,
    candidate_key: str | None,
) -> dict[str, Any]:
    with path.open() as handle:
        for index, line in enumerate(handle):
            if not line.strip():
                continue
            row = json.loads(line)
            if candidate_key is not None and row.get("candidate_key") != candidate_key:
                continue
            if candidate_key is None and index != row_index:
                continue
            return row
    selector = f"candidate_key={candidate_key!r}" if candidate_key else f"row_index={row_index}"
    raise ValueError(f"no candidate row matched {selector}")


def _product_root_target_ids(equations_path: Path) -> frozenset[int]:
    _, _, target_ids, _ = _product_anchor_sets(equations_path)
    return target_ids


def _all_target_ids(equations_path: Path) -> frozenset[int]:
    return frozenset(range(1, len(read_equations(equations_path)) + 1))


def _resolve_ids(
    *,
    explicit_ids: list[int],
    candidate_row: dict[str, Any] | None,
    row_field: str,
) -> frozenset[int] | None:
    if explicit_ids:
        return frozenset(explicit_ids)
    if candidate_row is None:
        return None
    row_value = candidate_row.get(row_field)
    if row_value is None:
        return None
    return frozenset(int(item) for item in row_value)


def _build_source_target_rule(
    *,
    source_ids: frozenset[int],
    target_ids: frozenset[int],
    order4_max_id: int,
    exclude_order4_block: bool,
) -> SourceTargetSetsRule:
    excluded_blocks = ()
    if exclude_order4_block:
        order4_sources = frozenset(eq_id for eq_id in source_ids if eq_id <= order4_max_id)
        order4_targets = frozenset(eq_id for eq_id in target_ids if eq_id <= order4_max_id)
        if order4_sources and order4_targets:
            excluded_blocks = ((order4_sources, order4_targets),)
    return SourceTargetSetsRule(
        source_ids=source_ids,
        target_ids=target_ids,
        excluded_blocks=excluded_blocks,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Preview exact incremental coverage for one bounded order5 "
            "source/target-set candidate without recomputing full coverage_summary()."
        )
    )
    parser.add_argument("--candidate-jsonl", type=Path)
    parser.add_argument("--candidate-row-index", type=int, default=0)
    parser.add_argument("--candidate-key")
    parser.add_argument("--equations-file", type=Path, default=DEFAULT_EQ_SIZE5_PATH)
    parser.add_argument("--source-target-cache", type=Path, default=DEFAULT_SOURCE_TARGET_CACHE_PATH)
    parser.add_argument(
        "--coverage-profile-json",
        type=Path,
        help="Use a prebuilt coverage profile and skip registry construction.",
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--source-id", type=int, action="append", default=[])
    parser.add_argument("--target-id", type=int, action="append", default=[])
    parser.add_argument(
        "--target-condition",
        choices=["product_root_target", "all"],
        help="Derive target ids from a supported named target condition.",
    )
    parser.add_argument("--verdict", choices=["true", "false"])
    parser.add_argument("--order4-max-id", type=int, default=DEFAULT_ORDER4_MAX_ID)
    parser.add_argument(
        "--exclude-order4-block",
        action=argparse.BooleanOptionalAction,
        default=False,
        help=(
            "Legacy preview mode: exclude the source<=order4_max_id and "
            "target<=order4_max_id block. The default canonical preview includes it."
        ),
    )
    parser.add_argument("--exact-pair-threshold", type=int, default=1_000_000)
    args = parser.parse_args()

    started_at = time.perf_counter()
    candidate_row = (
        _read_candidate_row(
            args.candidate_jsonl,
            row_index=args.candidate_row_index,
            candidate_key=args.candidate_key,
        )
        if args.candidate_jsonl is not None
        else None
    )

    source_ids = _resolve_ids(
        explicit_ids=args.source_id,
        candidate_row=candidate_row,
        row_field="source_ids",
    )
    target_ids = _resolve_ids(
        explicit_ids=args.target_id,
        candidate_row=candidate_row,
        row_field="target_ids",
    )
    target_condition = args.target_condition
    if target_condition is None and candidate_row is not None:
        target_condition = (candidate_row.get("target_condition") or {}).get("kind")
    if target_ids is None and target_condition == "product_root_target":
        target_ids = _product_root_target_ids(args.equations_file)
    if target_ids is None and target_condition == "all":
        target_ids = _all_target_ids(args.equations_file)

    if source_ids is None or target_ids is None:
        raise ValueError("source_ids and target_ids must be provided or derivable")

    verdict_value = args.verdict
    if verdict_value is None and candidate_row is not None:
        verdict_value = candidate_row.get("verdict")
    if verdict_value is None:
        raise ValueError("--verdict is required when candidate row has no verdict")
    verdict = _parse_bool(verdict_value)

    rule = _build_source_target_rule(
        source_ids=source_ids,
        target_ids=target_ids,
        order4_max_id=args.order4_max_id,
        exclude_order4_block=args.exclude_order4_block,
    )

    delta_started_at = time.perf_counter()
    registry_build_seconds = 0.0
    profile_load_seconds = 0.0
    if args.coverage_profile_json is not None:
        profile_started_at = time.perf_counter()
        profile = read_coverage_profile(args.coverage_profile_json)
        profile_load_seconds = time.perf_counter() - profile_started_at
        delta = coverage_delta_summary_from_profile(
            profile,
            rule,
            verdict=verdict,
            exact_pair_threshold=args.exact_pair_threshold,
        )
    else:
        build_started_at = time.perf_counter()
        registry = build_default_order5_strategy_registry(
            equations_path=args.equations_file,
            source_target_cache_path=(
                args.source_target_cache if args.source_target_cache.exists() else None
            ),
        )
        registry_build_seconds = time.perf_counter() - build_started_at
        delta = registry.coverage_delta_summary(
            rule,
            verdict=verdict,
            exact_pair_threshold=args.exact_pair_threshold,
        )
    delta_seconds = time.perf_counter() - delta_started_at

    result = {
        "schema_version": 1,
        "candidate_key": (candidate_row or {}).get("candidate_key"),
        "source_count": len(source_ids),
        "target_count": len(target_ids),
        "excluded_block_count": len(rule.excluded_blocks),
        "coverage_rule": rule.manifest_fragment(),
        "delta": delta,
        "timings_seconds": {
            "coverage_profile_load": profile_load_seconds,
            "registry_build": registry_build_seconds,
            "delta": delta_seconds,
            "total": time.perf_counter() - started_at,
        },
    }
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(output)
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
