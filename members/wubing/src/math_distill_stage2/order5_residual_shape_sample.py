from __future__ import annotations

import json
import time
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

from math_distill_stage2.dataset_io import write_jsonl
from math_distill_stage2.equations import Equation, Expr, parse_equation
from math_distill_stage2.order5_coverage_profile import (
    covered_targets_by_source_from_profile,
    read_coverage_profile,
)
from math_distill_stage2.order5_paircheck_bank import (
    load_equation_texts,
    sample_unresolved_pairs,
)
from math_distill_stage2.order5_spine_smoke import (
    DEFAULT_EQ_SIZE5_PATH,
    DEFAULT_ORDER4_MAX_ID,
)
from math_distill_stage2.order5_strategy_registry import (
    DEFAULT_SOURCE_TARGET_CACHE_PATH,
    build_default_order5_strategy_registry,
    find_true_strategy_ids_for_pair,
)


DEFAULT_COVERAGE_SUMMARY_PATH = Path(
    "data/processed/order5_strategy_registry/coverage_summary.json"
)
DEFAULT_OUTPUT_DIR = Path("data/processed/order5_strategy_registry")


def build_current_residual_shape_sample(
    *,
    equations_path: Path = DEFAULT_EQ_SIZE5_PATH,
    coverage_summary_path: Path = DEFAULT_COVERAGE_SUMMARY_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    output_stem: str,
    sample_size: int,
    seed: int,
    order4_max_id: int = DEFAULT_ORDER4_MAX_ID,
    max_scan_attempts: int | None = None,
    top_k: int = 50,
    source_target_cache_path: Path | None = DEFAULT_SOURCE_TARGET_CACHE_PATH,
    update_source_target_cache: bool = False,
    coverage_profile_path: Path | None = None,
) -> dict[str, Any]:
    if sample_size <= 0:
        raise ValueError("sample_size must be positive")
    if top_k <= 0:
        raise ValueError("top_k must be positive")

    started = time.monotonic()
    coverage = _compact_coverage_summary(_read_coverage_summary(coverage_summary_path))
    false_uncovered_estimate = (
        int(coverage["total_pairs"]) - int(coverage["deterministic_false_covered"])
    )
    unresolved_estimate = int(coverage["unresolved_estimate"])

    registry = build_default_order5_strategy_registry(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        include_true_strategies=False,
        source_target_cache_path=source_target_cache_path,
        update_source_target_cache=update_source_target_cache,
    )
    false_pairs = sample_unresolved_pairs(
        registry=registry,
        order4_max_id=order4_max_id,
        size=sample_size,
        seed=seed,
        max_scan_attempts=max_scan_attempts,
    )
    equation_texts = load_equation_texts(equations_path)
    equations = _parse_needed_equations(false_pairs, equation_texts)

    false_rows = [
        _annotate_pair(row, equations=equations)
        for row in false_pairs
    ]
    residual_rows, true_reason_counts, true_filter_mode = _filter_true_covered_rows(
        false_rows,
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        coverage_profile_path=coverage_profile_path,
    )

    paths = {
        "false_sample_jsonl": str(output_dir / f"{output_stem}_false_uncovered_sample.jsonl"),
        "false_buckets_json": str(output_dir / f"{output_stem}_false_uncovered_buckets.json"),
        "residual_sample_jsonl": str(output_dir / f"{output_stem}_residual_sample.jsonl"),
        "residual_buckets_json": str(output_dir / f"{output_stem}_residual_buckets.json"),
        "summary_json": str(output_dir / f"{output_stem}_summary.json"),
    }
    false_buckets = {
        "schema_version": 1,
        "sampling_scope": "current_false_uncovered_before_true_filter",
        "sample_count": len(false_rows),
        "seed": seed,
        "projection_base": false_uncovered_estimate,
        "current_coverage_used": coverage,
        "notes": [
            "residual_estimate_if_uniform is sampling guidance, not union increment or soundness evidence",
        ],
        "top_pair_buckets": summarize_shape_buckets(
            false_rows,
            projection_base=false_uncovered_estimate,
            top_k=top_k,
        ),
        "top_source_buckets": summarize_single_side_buckets(
            false_rows,
            side="source_shape",
            projection_base=false_uncovered_estimate,
            top_k=top_k,
        ),
        "top_target_buckets": summarize_single_side_buckets(
            false_rows,
            side="target_shape",
            projection_base=false_uncovered_estimate,
            top_k=top_k,
        ),
    }
    residual_buckets = {
        "schema_version": 1,
        "sampling_scope": "current_residual_after_true_filter",
        "sample_count": len(residual_rows),
        "source_false_sample_count": len(false_rows),
        "seed": seed,
        "projection_base": unresolved_estimate,
        "current_coverage_used": coverage,
        "notes": [
            "residual_estimate_if_uniform is sampling guidance, not union increment or soundness evidence",
        ],
        "top_pair_buckets": summarize_shape_buckets(
            residual_rows,
            projection_base=unresolved_estimate,
            top_k=top_k,
        ),
        "top_source_buckets": summarize_single_side_buckets(
            residual_rows,
            side="source_shape",
            projection_base=unresolved_estimate,
            top_k=top_k,
        ),
        "top_target_buckets": summarize_single_side_buckets(
            residual_rows,
            side="target_shape",
            projection_base=unresolved_estimate,
            top_k=top_k,
        ),
    }
    summary = {
        "schema_version": 1,
        "seed": seed,
        "sample_size": sample_size,
        "false_uncovered_sample_count": len(false_rows),
        "current_residual_sample_count": len(residual_rows),
        "true_filtered_count": len(false_rows) - len(residual_rows),
        "true_filtered_rate_within_false_uncovered_sample": (
            (len(false_rows) - len(residual_rows)) / len(false_rows)
            if false_rows
            else 0.0
        ),
        "retained_after_true_filter_count": len(residual_rows),
        "retained_after_true_filter_rate": (
            len(residual_rows) / len(false_rows) if false_rows else 0.0
        ),
        "coverage_used": coverage,
        "coverage_profile_path": (
            str(coverage_profile_path) if coverage_profile_path else None
        ),
        "false_uncovered_estimate": false_uncovered_estimate,
        "unresolved_estimate": unresolved_estimate,
        "true_reason_counts": dict(true_reason_counts),
        "true_filter_mode": true_filter_mode,
        "top_false_pair_buckets": false_buckets["top_pair_buckets"][:10],
        "top_residual_pair_buckets": residual_buckets["top_pair_buckets"][:10],
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "paths": paths,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(Path(paths["false_sample_jsonl"]), false_rows)
    write_jsonl(Path(paths["residual_sample_jsonl"]), residual_rows)
    _write_json(Path(paths["false_buckets_json"]), false_buckets)
    _write_json(Path(paths["residual_buckets_json"]), residual_buckets)
    _write_json(Path(paths["summary_json"]), summary)
    return summary


def _filter_true_covered_rows(
    false_rows: Sequence[dict[str, Any]],
    *,
    equations_path: Path,
    order4_max_id: int,
    coverage_profile_path: Path | None,
) -> tuple[list[dict[str, Any]], Counter[str], str]:
    residual_rows: list[dict[str, Any]] = []
    true_reason_counts: Counter[str] = Counter()
    if coverage_profile_path is not None:
        profile = read_coverage_profile(coverage_profile_path)
        true_targets_by_source = covered_targets_by_source_from_profile(
            profile,
            verdict=True,
            source_ids=(int(row["eq1_id"]) for row in false_rows),
        )
        for row in false_rows:
            eq1_id = int(row["eq1_id"])
            eq2_id = int(row["eq2_id"])
            if eq2_id in true_targets_by_source.get(eq1_id, frozenset()):
                true_reason_counts.update(["coverage_profile.true_union"])
                continue
            residual_rows.append(row)
        return residual_rows, true_reason_counts, "coverage_profile"

    for row in false_rows:
        true_strategy_ids = find_true_strategy_ids_for_pair(
            int(row["eq1_id"]),
            int(row["eq2_id"]),
            equations_path=equations_path,
            order4_max_id=order4_max_id,
            include_seedbank=True,
        )
        if true_strategy_ids:
            true_reason_counts.update(true_strategy_ids)
            continue
        residual_rows.append(row)
    return residual_rows, true_reason_counts, "strategy_function"


def equation_shape_bucket(equation: Equation) -> str:
    left = equation.left
    right = equation.right
    left_vars = set(left.variable_names())
    right_vars = set(right.variable_names())
    return (
        f"roots={_root(left)}>{_root(right)}"
        f"|d={_depth(left)}>{_depth(right)}"
        f"|vc={len(left_vars | right_vars)}"
        f"|lm={int(_leftmost_var(left) == _leftmost_var(right))}"
        f"|rm={int(_rightmost_var(left) == _rightmost_var(right))}"
        f"|vs={int(left_vars == right_vars)}"
    )


def pair_shape_bucket(source: Equation, target: Equation) -> str:
    return f"{equation_shape_bucket(source)} -> {equation_shape_bucket(target)}"


def equation_feature_summary(equation: Equation) -> dict[str, Any]:
    left = equation.left
    right = equation.right
    left_vars = set(left.variable_names())
    right_vars = set(right.variable_names())
    return {
        "shape": equation_shape_bucket(equation),
        "roots": f"{_root(left)}>{_root(right)}",
        "depths": f"{_depth(left)}>{_depth(right)}",
        "var_count": len(left_vars | right_vars),
        "lhs_bare": left.kind == "var",
        "rhs_bare": right.kind == "var",
        "lhs_lm_rm": f"{_leftmost_var(left)}:{_rightmost_var(left)}",
        "rhs_lm_rm": f"{_leftmost_var(right)}:{_rightmost_var(right)}",
        "leftmost_matches": _leftmost_var(left) == _leftmost_var(right),
        "rightmost_matches": _rightmost_var(left) == _rightmost_var(right),
        "variable_sets_match": left_vars == right_vars,
    }


def summarize_shape_buckets(
    rows: Sequence[dict[str, Any]],
    *,
    projection_base: int,
    top_k: int,
) -> list[dict[str, Any]]:
    return _summarize_counter(
        Counter(str(row["shape_bucket"]) for row in rows),
        sample_count=len(rows),
        projection_base=projection_base,
        top_k=top_k,
    )


def summarize_single_side_buckets(
    rows: Sequence[dict[str, Any]],
    *,
    side: str,
    projection_base: int,
    top_k: int,
) -> list[dict[str, Any]]:
    return _summarize_counter(
        Counter(str(row[side]) for row in rows),
        sample_count=len(rows),
        projection_base=projection_base,
        top_k=top_k,
    )


def _annotate_pair(
    row: dict[str, Any],
    *,
    equations: dict[int, Equation],
) -> dict[str, Any]:
    eq1_id = int(row["eq1_id"])
    eq2_id = int(row["eq2_id"])
    source = equations[eq1_id]
    target = equations[eq2_id]
    return {
        "pair_index": int(row["pair_index"]),
        "eq1_id": eq1_id,
        "eq2_id": eq2_id,
        "stratum": str(row["stratum"]),
        "source_shape": equation_shape_bucket(source),
        "target_shape": equation_shape_bucket(target),
        "shape_bucket": pair_shape_bucket(source, target),
        "source_features": equation_feature_summary(source),
        "target_features": equation_feature_summary(target),
    }


def _summarize_counter(
    counts: Counter[str],
    *,
    sample_count: int,
    projection_base: int,
    top_k: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for bucket, count in counts.most_common(top_k):
        sample_rate = count / sample_count if sample_count else 0.0
        rows.append(
            {
                "bucket": bucket,
                "sample_count": count,
                "sample_rate": sample_rate,
                "residual_estimate_if_uniform": round(projection_base * sample_rate),
            }
        )
    return rows


def _parse_needed_equations(
    pair_rows: Sequence[dict[str, Any]],
    equation_texts: dict[int, str],
) -> dict[int, Equation]:
    needed = {
        int(row["eq1_id"])
        for row in pair_rows
    } | {
        int(row["eq2_id"])
        for row in pair_rows
    }
    return {
        equation_id: parse_equation(equation_texts[equation_id])
        for equation_id in sorted(needed)
    }


def _root(expr: Expr) -> str:
    return expr.kind


def _depth(expr: Expr) -> int:
    if expr.kind == "var":
        return 0
    assert expr.left is not None
    assert expr.right is not None
    return 1 + max(_depth(expr.left), _depth(expr.right))


def _leftmost_var(expr: Expr) -> str:
    if expr.kind == "var":
        assert expr.value is not None
        return expr.value
    assert expr.left is not None
    return _leftmost_var(expr.left)


def _rightmost_var(expr: Expr) -> str:
    if expr.kind == "var":
        assert expr.value is not None
        return expr.value
    assert expr.right is not None
    return _rightmost_var(expr.right)


def _read_coverage_summary(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _compact_coverage_summary(coverage: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "coverage_scope",
        "includes_order4_source_to_order4_target",
        "source_target_excluded_block_count",
        "total_pairs",
        "raw_false_union_covered",
        "raw_true_union_covered",
        "deterministic_false_covered",
        "deterministic_true_covered",
        "unresolved_estimate",
        "conflict_count",
    ]
    return {key: coverage[key] for key in keys if key in coverage}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
