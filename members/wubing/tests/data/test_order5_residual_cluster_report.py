import json
from pathlib import Path

from math_distill_stage2.order5_residual_cluster_report import (
    build_residual_cluster_report,
)


def test_build_residual_cluster_report_ranks_true_then_predicate_then_setcheck(
    tmp_path: Path,
):
    coverage = _write_json(
        tmp_path / "coverage.json",
        {
            "total_pairs": 1000,
            "deterministic_false_covered": 500,
            "deterministic_true_covered": 200,
            "unresolved_estimate": 300,
            "conflict_count": 0,
        },
    )
    false_shape = _write_json(
        tmp_path / "false_shape.json",
        {
            "top_pair_buckets": [
                {"bucket": "a -> b", "sample_count": 5, "residual_estimate_if_uniform": 50},
                {"bucket": "c -> d", "sample_count": 3, "residual_estimate_if_uniform": 30},
            ]
        },
    )
    true_shape = _write_json(
        tmp_path / "true_shape.json",
        {
            "source_false_sample_count": 10,
            "cheap_true_filtered_count": 4,
            "top_pair_buckets_after_targeted_seed_filter": [
                {"bucket": "a -> b", "sample_count": 3, "residual_estimate_if_uniform": 30},
                {"bucket": "c -> d", "sample_count": 2, "residual_estimate_if_uniform": 20},
            ],
        },
    )
    top3 = _write_json(
        tmp_path / "top3.json",
        {
            "pre_top3_false_uncovered_pair_count": 5,
            "cheap_true_filtered_count": 2,
            "targeted_seed_filtered_pair_count": 1,
        },
    )
    fin3 = _write_json(
        tmp_path / "fin3.json",
        {
            "candidate_count": 20,
            "hit_count": 1,
            "hit_rate": 0.05,
            "top_models": [{"model_label": "m", "hit_count": 1}],
        },
    )
    top1 = _write_json(
        tmp_path / "top1.json",
        {
            "sample_count": 7,
            "hit_count": 0,
            "hit_rate_within_bucket_sample": 0.0,
        },
    )
    top2_3 = _write_json(
        tmp_path / "top2_3.json",
        {
            "sample_count": 9,
            "hit_count": 0,
            "hit_rate": 0.0,
        },
    )
    predicate = _write_json(
        tmp_path / "predicate.json",
        {
            "input_paircheck_rows": 2,
            "rows": [
                {
                    "source_feature": {"name": "f", "value": "s"},
                    "target_feature": {"name": "g", "value": "t"},
                    "paircheck_hit_count": 2,
                    "false_uncovered_pair_capacity": 120,
                    "top_models": [{"model_label": "m", "count": 2}],
                }
            ],
        },
    )
    setcheck = tmp_path / "setcheck.jsonl"
    setcheck.write_text(
        json.dumps({"label": "low", "increment": 1, "coverage_count": 10}) + "\n"
        + json.dumps({"label": "high", "increment": 9, "coverage_count": 20}) + "\n",
        encoding="utf-8",
    )

    report = build_residual_cluster_report(
        coverage_summary_path=coverage,
        false_shape_buckets_path=false_shape,
        true_filtered_shape_buckets_path=true_shape,
        top3_synthesis_summary_path=top3,
        fin3_selector_probe_path=fin3,
        top1_fin3_selector_probe_path=top1,
        top2_3_fin3_selector_probe_path=top2_3,
        predicate_bucket_probe_path=predicate,
        setcheck_ranking_path=setcheck,
        top_k=1,
    )

    assert report["working_universe"]["unresolved_estimate"] == 300
    assert report["clusters"]["cheap_true_filter"]["filtered_rate"] == 0.4
    assert report["clusters"]["cheap_true_filter"]["rough_projected_pairs_if_uniform"] == 120
    assert report["clusters"]["shape_buckets"]["after_true_and_seed_filter"]["top1_estimate"] == 30
    assert report["clusters"]["paircheck_predicate_probe"]["top_rows"][0][
        "false_uncovered_pair_capacity"
    ] == 120
    assert report["clusters"]["setcheck_tail"]["best_increment"] == 9
    assert [row["next_skill"] for row in report["roi_ranking"]] == [
        "stage2-strategy-mine-true-template",
        "stage2-strategy-mine-false-predicate",
        "stage2-strategy-mine-setcheck",
    ]


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path
