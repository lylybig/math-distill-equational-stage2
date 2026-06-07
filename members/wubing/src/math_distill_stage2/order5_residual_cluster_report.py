from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_REGISTRY_DIR = Path("data/processed/order5_strategy_registry")
DEFAULT_COVERAGE_SUMMARY_PATH = DEFAULT_REGISTRY_DIR / "coverage_summary.json"
DEFAULT_FALSE_SHAPE_BUCKETS_PATH = (
    DEFAULT_REGISTRY_DIR
    / "current_false_unresolved_after_bank_shape_buckets_50000_seed20260521.json"
)
DEFAULT_TRUE_FILTERED_SHAPE_BUCKETS_PATH = (
    DEFAULT_REGISTRY_DIR
    / "current_unresolved_after_bank_top_shape_buckets_with_targeted_seed_filter_seed20260521.json"
)
DEFAULT_TOP3_SYNTHESIS_SUMMARY_PATH = (
    DEFAULT_REGISTRY_DIR
    / "current_unresolved_after_bank_top3_shape_synthesis_targets_seed20260521_summary.json"
)
DEFAULT_FIN3_SELECTOR_PROBE_PATH = (
    DEFAULT_REGISTRY_DIR
    / "current_false_unresolved_after_bank_fin3_selector_probe_2000xall_seed20260521.json"
)
DEFAULT_TOP1_FIN3_SELECTOR_PROBE_PATH = (
    DEFAULT_REGISTRY_DIR
    / "current_false_unresolved_after_bank_top1_shape_fin3_selector_probe_seed20260521.json"
)
DEFAULT_TOP2_3_FIN3_SELECTOR_PROBE_PATH = (
    DEFAULT_REGISTRY_DIR
    / "current_false_unresolved_after_bank_top2_3_shape_fin3_selector_probe_seed20260521.json"
)
DEFAULT_PREDICATE_BUCKET_PROBE_PATH = (
    DEFAULT_REGISTRY_DIR / "predicate_bucket_probe_from_paircheck_v1.json"
)
DEFAULT_SETCHECK_RANKING_PATH = (
    DEFAULT_REGISTRY_DIR / "current_high_setcheck_candidate_rankings_seed20260521.jsonl"
)


def build_residual_cluster_report(
    *,
    coverage_summary_path: Path = DEFAULT_COVERAGE_SUMMARY_PATH,
    false_shape_buckets_path: Path = DEFAULT_FALSE_SHAPE_BUCKETS_PATH,
    true_filtered_shape_buckets_path: Path = DEFAULT_TRUE_FILTERED_SHAPE_BUCKETS_PATH,
    top3_synthesis_summary_path: Path = DEFAULT_TOP3_SYNTHESIS_SUMMARY_PATH,
    fin3_selector_probe_path: Path = DEFAULT_FIN3_SELECTOR_PROBE_PATH,
    top1_fin3_selector_probe_path: Path = DEFAULT_TOP1_FIN3_SELECTOR_PROBE_PATH,
    top2_3_fin3_selector_probe_path: Path = DEFAULT_TOP2_3_FIN3_SELECTOR_PROBE_PATH,
    predicate_bucket_probe_path: Path = DEFAULT_PREDICATE_BUCKET_PROBE_PATH,
    setcheck_ranking_path: Path = DEFAULT_SETCHECK_RANKING_PATH,
    top_k: int = 10,
) -> dict[str, Any]:
    if top_k <= 0:
        raise ValueError("top_k must be positive")

    coverage = _read_json(coverage_summary_path)
    unresolved_estimate = int(coverage["unresolved_estimate"])
    total_pairs = int(coverage["total_pairs"])
    deterministic_false = int(coverage["deterministic_false_covered"])
    deterministic_true = int(coverage["deterministic_true_covered"])

    false_shape = _read_json(false_shape_buckets_path)
    true_filtered_shape = _read_json(true_filtered_shape_buckets_path)
    top3_synthesis = _read_json(top3_synthesis_summary_path)
    fin3_selector = _read_json(fin3_selector_probe_path)
    top1_fin3_selector = _read_json_if_exists(top1_fin3_selector_probe_path)
    top2_3_fin3_selector = _read_json_if_exists(top2_3_fin3_selector_probe_path)
    predicate_probe = _read_json(predicate_bucket_probe_path)
    setcheck_rows = _read_jsonl(setcheck_ranking_path)

    cheap_true_sample_count = int(true_filtered_shape["source_false_sample_count"])
    cheap_true_filtered_count = int(true_filtered_shape["cheap_true_filtered_count"])
    cheap_true_rate = _safe_ratio(cheap_true_filtered_count, cheap_true_sample_count)
    top3_pre_count = int(top3_synthesis["pre_top3_false_uncovered_pair_count"])
    top3_cheap_true_filtered_count = int(top3_synthesis["cheap_true_filtered_count"])
    top3_cheap_true_rate = _safe_ratio(top3_cheap_true_filtered_count, top3_pre_count)

    false_top_buckets = false_shape.get("top_pair_buckets", [])
    true_filtered_top_buckets = true_filtered_shape.get(
        "top_pair_buckets_after_targeted_seed_filter", []
    )
    setcheck_rows_sorted = sorted(
        setcheck_rows,
        key=lambda row: (
            int(row.get("increment", 0)),
            int(row.get("coverage_count", 0)),
            str(row.get("label", "")),
        ),
        reverse=True,
    )
    predicate_rows = predicate_probe.get("rows", [])

    report = {
        "schema_version": 1,
        "working_universe": {
            "name": "current_unresolved_residual",
            "unresolved_estimate": unresolved_estimate,
            "total_pairs_denominator_only": total_pairs,
            "note": (
                "Candidate mining should use current unresolved samples, top buckets, "
                "registry masks, paircheck clusters, and proof clusters. Full pair "
                "space is only for final summary and conflict checks."
            ),
        },
        "coverage": {
            "total_pairs": total_pairs,
            "deterministic_false_covered": deterministic_false,
            "deterministic_true_covered": deterministic_true,
            "deterministic_covered_sum": deterministic_false + deterministic_true,
            "unresolved_estimate": unresolved_estimate,
            "conflict_count": int(coverage.get("conflict_count", 0)),
        },
        "clusters": {
            "cheap_true_filter": {
                "sample_count": cheap_true_sample_count,
                "filtered_count": cheap_true_filtered_count,
                "filtered_rate": cheap_true_rate,
                "rough_projected_pairs_if_uniform": round(
                    unresolved_estimate * cheap_true_rate
                ),
                "top3_pre_filter_sample_count": top3_pre_count,
                "top3_filtered_count": top3_cheap_true_filtered_count,
                "top3_filtered_rate": top3_cheap_true_rate,
                "top3_targeted_seed_filtered_count": int(
                    top3_synthesis.get("targeted_seed_filtered_pair_count", 0)
                ),
            },
            "shape_buckets": {
                "false_uncovered_before_true_filter": _bucket_summary(false_top_buckets),
                "after_true_and_seed_filter": _bucket_summary(true_filtered_top_buckets),
                "top_buckets_after_true_and_seed_filter": _trim_buckets(
                    true_filtered_top_buckets, top_k
                ),
            },
            "fin3_selector": {
                "global_probe": _selector_summary(fin3_selector),
                "top1_shape_probe": _selector_summary(top1_fin3_selector),
                "top2_3_shape_probe": _selector_summary(top2_3_fin3_selector),
            },
            "paircheck_predicate_probe": {
                "input_paircheck_rows": int(predicate_probe.get("input_paircheck_rows", 0)),
                "top_rows": _trim_predicate_rows(predicate_rows, top_k),
                "note": (
                    "false_uncovered_pair_capacity is only capacity, not union "
                    "increment. Use these rows as predicate seeds."
                ),
            },
            "setcheck_tail": {
                "candidate_count": len(setcheck_rows),
                "best_increment": int(setcheck_rows_sorted[0].get("increment", 0))
                if setcheck_rows_sorted
                else 0,
                "top_rows": _trim_setcheck_rows(setcheck_rows_sorted, top_k),
            },
        },
        "roi_ranking": _roi_ranking(
            cheap_true_rate=cheap_true_rate,
            top3_cheap_true_rate=top3_cheap_true_rate,
            true_filtered_top_buckets=true_filtered_top_buckets,
            predicate_rows=predicate_rows,
            setcheck_rows_sorted=setcheck_rows_sorted,
            fin3_selector=fin3_selector,
            top1_fin3_selector=top1_fin3_selector,
            top2_3_fin3_selector=top2_3_fin3_selector,
        ),
        "source_paths": {
            "coverage_summary": str(coverage_summary_path),
            "false_shape_buckets": str(false_shape_buckets_path),
            "true_filtered_shape_buckets": str(true_filtered_shape_buckets_path),
            "top3_synthesis_summary": str(top3_synthesis_summary_path),
            "fin3_selector_probe": str(fin3_selector_probe_path),
            "top1_fin3_selector_probe": str(top1_fin3_selector_probe_path),
            "top2_3_fin3_selector_probe": str(top2_3_fin3_selector_probe_path),
            "predicate_bucket_probe": str(predicate_bucket_probe_path),
            "setcheck_ranking": str(setcheck_ranking_path),
        },
    }
    return report


def write_residual_cluster_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return _read_json(path)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _safe_ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _sum_estimate(rows: list[dict[str, Any]], limit: int | None = None) -> int:
    selected = rows if limit is None else rows[:limit]
    return sum(int(row.get("residual_estimate_if_uniform", 0)) for row in selected)


def _bucket_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "bucket_count": len(rows),
        "top1_estimate": _sum_estimate(rows, 1),
        "top3_estimate": _sum_estimate(rows, 3),
        "top5_estimate": _sum_estimate(rows, 5),
        "top10_estimate": _sum_estimate(rows, 10),
        "top20_estimate": _sum_estimate(rows, 20),
        "listed_estimate": _sum_estimate(rows),
    }


def _trim_buckets(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    trimmed = []
    for row in rows[:limit]:
        trimmed.append(
            {
                "bucket": row.get("bucket"),
                "sample_count": int(row.get("sample_count", 0)),
                "residual_estimate_if_uniform": int(
                    row.get("residual_estimate_if_uniform", 0)
                ),
            }
        )
    return trimmed


def _selector_summary(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if payload is None:
        return None
    return {
        "candidate_count": int(payload.get("candidate_count", payload.get("sample_count", 0))),
        "hit_count": int(payload.get("hit_count", 0)),
        "hit_rate": float(
            payload.get(
                "hit_rate",
                payload.get("hit_rate_within_bucket_sample", 0.0),
            )
        ),
        "estimated_false_uncovered_selector_hits": payload.get(
            "estimated_false_uncovered_selector_hits"
        ),
        "rough_unresolved_selector_hits_if_uniform": payload.get(
            "rough_unresolved_selector_hits_if_uniform"
        ),
        "top_models": payload.get("top_models", [])[:5],
    }


def _trim_predicate_rows(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    trimmed = []
    for row in rows[:limit]:
        trimmed.append(
            {
                "source_feature": row.get("source_feature"),
                "target_feature": row.get("target_feature"),
                "paircheck_hit_count": int(row.get("paircheck_hit_count", 0)),
                "false_uncovered_pair_capacity": int(
                    row.get("false_uncovered_pair_capacity", 0)
                ),
                "top_models": row.get("top_models", [])[:3],
            }
        )
    return trimmed


def _trim_setcheck_rows(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    trimmed = []
    for row in rows[:limit]:
        trimmed.append(
            {
                "label": row.get("label"),
                "order": int(row.get("order", 0)),
                "increment": int(row.get("increment", 0)),
                "coverage_count": int(row.get("coverage_count", 0)),
                "source_count": int(row.get("source_count", 0)),
                "target_count": int(row.get("target_count", 0)),
            }
        )
    return trimmed


def _roi_ranking(
    *,
    cheap_true_rate: float,
    top3_cheap_true_rate: float,
    true_filtered_top_buckets: list[dict[str, Any]],
    predicate_rows: list[dict[str, Any]],
    setcheck_rows_sorted: list[dict[str, Any]],
    fin3_selector: dict[str, Any],
    top1_fin3_selector: dict[str, Any] | None,
    top2_3_fin3_selector: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    top20_after_true = _sum_estimate(true_filtered_top_buckets, 20)
    best_predicate_capacity = (
        int(predicate_rows[0].get("false_uncovered_pair_capacity", 0))
        if predicate_rows
        else 0
    )
    best_setcheck_increment = (
        int(setcheck_rows_sorted[0].get("increment", 0)) if setcheck_rows_sorted else 0
    )
    top_shape_selector_hits = int((top1_fin3_selector or {}).get("hit_count", 0)) + int(
        (top2_3_fin3_selector or {}).get("hit_count", 0)
    )
    return [
        {
            "rank": 1,
            "direction": "true_template_on_residual_shape_buckets",
            "next_skill": "stage2-strategy-mine-true-template",
            "why": [
                f"cheap_true_filtered_rate={cheap_true_rate:.4f}",
                f"top3_cheap_true_filtered_rate={top3_cheap_true_rate:.4f}",
                f"top20_after_true_filter_estimate={top20_after_true}",
            ],
        },
        {
            "rank": 2,
            "direction": "false_predicate_from_paircheck_feature_clusters",
            "next_skill": "stage2-strategy-mine-false-predicate",
            "why": [
                f"best_predicate_capacity={best_predicate_capacity}",
                "capacity_is_not_increment",
                "paircheck_rows_are_seeds_for_predicate_verification",
            ],
        },
        {
            "rank": 3,
            "direction": "setcheck_tail_as_seed_or_parking_lot",
            "next_skill": "stage2-strategy-mine-setcheck",
            "why": [
                f"best_current_union_increment={best_setcheck_increment}",
                f"fin3_global_hit_rate={float(fin3_selector.get('hit_rate', 0.0)):.4f}",
                f"top_shape_selector_hits={top_shape_selector_hits}",
            ],
        },
    ]
