import json
import subprocess
import sys
from pathlib import Path

from math_distill_stage2.order5_strategy_mining_state import (
    build_candidate_index,
    build_merge_review_queue,
    build_mining_state,
    render_merge_review_markdown,
    summarize_candidate_file,
)


def _write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _write_minimal_registry(registry_dir: Path) -> None:
    _write_json(
        registry_dir / "coverage_summary.json",
        {
            "schema_version": 1,
            "total_pairs": 1000,
            "deterministic_false_covered": 300,
            "deterministic_true_covered": 200,
            "unresolved_estimate": 500,
            "conflict_count": 0,
        },
    )
    _write_json(
        registry_dir / "strategies.json",
        [
            {
                "strategy_key": "false.finmodel.setcheck.demo",
                "verdict": False,
                "priority": 100,
                "deprecated": False,
                "verification_mode": "setcheck",
            },
            {
                "strategy_key": "true.proof.templatecheck.demo",
                "verdict": True,
                "priority": 200,
                "deprecated": False,
                "verification_mode": "templatecheck",
                "template_component_candidate_keys": [
                    "true.proof.templatecheck.demo_component.v1"
                ],
            },
        ],
    )


def test_candidate_index_classifies_register_ready_blocked_and_parking(tmp_path: Path):
    candidates_dir = tmp_path / "candidates"
    _write_json(
        candidates_dir / "true_high_summary.json",
        {
            "candidate_key": "true.high",
            "verdict": True,
            "exact_union_increment": 1_200_000,
            "remote_smoke_status": "accepted",
            "accepted_count": 12,
            "total_count": 12,
        },
    )
    _write_json(
        candidates_dir / "false_affine_summary.json",
        {
            "candidate_family": "false.finmodel.setcheck.affine_mod_probe.mod17",
            "candidate_batch": {
                "cumulative_exact_current_false_union_increment": 4_256_474,
            },
            "candidate_layer_decision": {
                "affine_mod17_batch_status": "high_roi_but_still_blocked_not_merge_ready",
                "reason": "critical representative smoke rejected by remote judge",
            },
            "direct_split_smoke_followup": {
                "single_tests": [
                    {
                        "accepted_count": 0,
                        "total_count": 1,
                        "status_counts": {"incorrect": 1},
                    }
                ]
            },
        },
    )
    _write_json(
        candidates_dir / "false_tail_summary.json",
        {
            "candidate_key": "false.small",
            "best_increment": 485,
            "status": "parking_lot_below_100k",
        },
    )
    _write_json(
        candidates_dir / "true_merged_summary.json",
        {
            "candidate_key": "true.merged",
            "exact_union_increment": 677_528,
            "registry_status": "register_layer_merged",
            "remote_smoke_status": "accepted_100_of_100",
        },
    )

    rows, summary = build_candidate_index(candidates_dir=candidates_dir)

    statuses = {row["candidate_key"]: row["status"] for row in rows}
    assert statuses["true.high"] == "register_ready"
    assert (
        statuses["false.finmodel.setcheck.affine_mod_probe.mod17"]
        == "certificate_blocked"
    )
    assert statuses["true.merged"] == "merged_or_subsumed"
    assert statuses["false.small"] == "parking_lot"
    assert summary["status_counts"] == {
        "certificate_blocked": 1,
        "merged_or_subsumed": 1,
        "parking_lot": 1,
        "register_ready": 1,
    }


def test_candidate_index_marks_current_rescore_artifact_as_absorbed(tmp_path: Path):
    candidates_dir = tmp_path / "candidates"
    absorbed_path = "data/processed/order5_strategy_registry/candidates/old_summary.json"
    _write_json(
        candidates_dir / "controller_rescore_summary.json",
        {
            "controller_action": "register_ready_main_current_v26_rescore_only_no_formal_registry_write",
            "rows": [
                {
                    "summary_path": absorbed_path,
                    "status": "demoted_after_current_rescore",
                    "current_v26_delta": {
                        "candidate_verdict_deterministic_increment": 0,
                        "conflict_increment": 0,
                    },
                }
            ],
        },
    )

    rows, _ = build_candidate_index(candidates_dir=candidates_dir)

    assert rows[0]["status"] == "merged_or_subsumed"
    assert rows[0]["absorbed_candidate_summary_paths"] == [absorbed_path]


def test_candidate_index_marks_top_level_current_rescore_demotion(tmp_path: Path):
    candidates_dir = tmp_path / "candidates"
    absorbed_path = "data/processed/order5_strategy_registry/candidates/high_summary.json"
    _write_json(
        candidates_dir / "controller_top_rescore_summary.json",
        {
            "controller_action": "top_candidate_current_v26_rescore_only_no_formal_registry_write",
            "source_summary_path": absorbed_path,
            "status": "demoted_after_current_rescore",
            "old_latest_registry_increment_delta": {
                "candidate_verdict_deterministic_increment": 6_000_000
            },
            "current_v26_delta": {
                "candidate_verdict_deterministic_increment": 0,
                "conflict_increment": 0,
            },
            "remote_smoke": {
                "accepted_count_total": 1000,
                "total_count": 1000,
            },
        },
    )

    rows, _ = build_candidate_index(candidates_dir=candidates_dir)

    assert rows[0]["status"] == "merged_or_subsumed"
    assert rows[0]["absorbed_candidate_summary_paths"] == [absorbed_path]


def test_candidate_index_absorbs_stale_current_registry_rescore_rows(tmp_path: Path):
    candidates_dir = tmp_path / "candidates"
    absorbed_path = "data/processed/order5_strategy_registry/candidates/old_hconst_summary.json"
    _write_json(
        candidates_dir / "controller_stale_rescore_summary.json",
        {
            "controller_action": "hconst_queue_current_rescore_no_formal_registry_write",
            "results": [
                {
                    "summary_path": absorbed_path,
                    "current_review_status": "stale_or_subsumed_by_current_registry_v25",
                    "current_delta_against_v25": {
                        "candidate_verdict_deterministic_increment": 0,
                        "total_deterministic_increment": 0,
                        "conflict_increment": 0,
                    },
                }
            ],
        },
    )

    rows, _ = build_candidate_index(candidates_dir=candidates_dir)

    assert rows[0]["status"] == "merged_or_subsumed"
    assert rows[0]["absorbed_candidate_summary_paths"] == [absorbed_path]


def test_candidate_index_marks_closed_fresh_subsumed_rescore(tmp_path: Path):
    candidates_dir = tmp_path / "candidates"
    absorbed_path = "data/processed/order5_strategy_registry/candidates/source_summary.json"
    _write_json(
        candidates_dir / "closed_fresh_rescore_summary.json",
        {
            "candidate_key": "true.rescore.current_v26",
            "source_summary_path": absorbed_path,
            "old_delta_against_profile_v17": {
                "candidate_verdict_deterministic_increment": 6_200_000,
            },
            "delta_current_v26": {
                "candidate_verdict_deterministic_increment": 0,
                "conflict_increment": 0,
            },
            "registry_status_recommendation": "closed_fresh_subsumed",
            "remote_smoke": {"accepted_count": 120, "total_count": 120},
        },
    )

    rows, _ = build_candidate_index(candidates_dir=candidates_dir)

    assert rows[0]["status"] == "merged_or_subsumed"
    assert rows[0]["absorbed_candidate_summary_paths"] == [absorbed_path]


def test_candidate_index_marks_controller_review_artifact_as_subsumed(tmp_path: Path):
    candidates_dir = tmp_path / "candidates"
    _write_json(
        candidates_dir / "controller_dispatch_summary.json",
        {
            "controller_action": "current_residual_postedge7_dispatch_matrix",
            "candidate_layer_only": True,
            "formal_registry_modified": False,
            "best_increment": 6_200_000,
            "output_paths": {
                "dispatch_jsonl": "data/processed/order5_strategy_registry/candidates/dispatch.jsonl"
            },
        },
    )

    rows, _ = build_candidate_index(candidates_dir=candidates_dir)

    assert rows[0]["status"] == "merged_or_subsumed"
    assert rows[0]["controller_review_artifact"] is True


def test_candidate_index_reads_aggregate_remote_smoke_counts(tmp_path: Path):
    candidates_dir = tmp_path / "candidates"
    _write_json(
        candidates_dir / "aggregate_smoke_summary.json",
        {
            "candidate_key": "true.aggregate",
            "exact_union_increment": 1_200_000,
            "remote_smoke": {
                "accepted_count_total": 1000,
                "total_count": 1000,
            },
        },
    )

    rows, _ = build_candidate_index(candidates_dir=candidates_dir)

    assert rows[0]["status"] == "register_ready"
    assert rows[0]["smoke"]["all_accepted_observed"] is True
    assert rows[0]["smoke"]["max_accepted_count"] == 1000


def test_candidate_index_reads_flat_remote_smoke_counts(tmp_path: Path):
    candidates_dir = tmp_path / "candidates"
    _write_json(
        candidates_dir / "flat_smoke_summary.json",
        {
            "candidate_key": "true.flat",
            "exact_union_increment": 1_200_000,
            "remote_smoke_accepted_count": 23,
            "remote_smoke_total_count": 23,
        },
    )

    rows, _ = build_candidate_index(candidates_dir=candidates_dir)

    assert rows[0]["status"] == "register_ready"
    assert rows[0]["smoke"]["all_accepted_observed"] is True
    assert rows[0]["smoke"]["max_accepted_count"] == 23


def test_candidate_index_marks_formal_registry_merged_as_subsumed(tmp_path: Path):
    candidates_dir = tmp_path / "candidates"
    _write_json(
        candidates_dir / "formal_merged_summary.json",
        {
            "candidate_key": "true.formal",
            "exact_union_increment": 1_200_000,
            "registry_status": "formal_registry_merged_and_postmerge_smoke_passed",
            "remote_smoke_accepted_count": 23,
            "remote_smoke_total_count": 23,
        },
    )

    rows, _ = build_candidate_index(candidates_dir=candidates_dir)

    assert rows[0]["status"] == "merged_or_subsumed"


def test_candidate_index_routes_non_mergeable_mainline_artifacts(tmp_path: Path):
    candidates_dir = tmp_path / "candidates"
    _write_json(
        candidates_dir / "recursive_seedgate_summary.json",
        {
            "candidate_key": "true.recursive",
            "estimated_union_increment": 100_000_000,
            "status": "candidate_needs_remote_judge_seedgate",
            "reason": "each source seed needs accepted singleton certificate before registry merge",
        },
    )
    _write_json(
        candidates_dir / "mod17_selection_summary.json",
        {
            "top_selected": [
                {
                    "candidate_key": "false.finmodel.setcheck.affine_mod_probe.mod17.a7.b11.c0.all_equations",
                    "exact_union_increment": 4_200_000,
                }
            ]
        },
    )
    _write_json(
        candidates_dir / "partial_scan_summary.json",
        {
            "status": "stopped_after_high_value_partial_scan",
            "last_progress": {"best_increment": 2_000_000},
        },
    )
    _write_json(
        candidates_dir / "support_review_summary.json",
        {
            "candidate_key": "false.predicate",
            "max_estimated_union_increment": 1_200_000,
            "conclusion": "model_family_predicate_candidates_found_but_require_registry_support_review",
        },
    )
    _write_json(
        candidates_dir / "selected_summary.json",
        {
            "selected_path": "selected.jsonl",
            "rank_path": "rank.jsonl",
            "positive_count": 1,
            "top_candidates": [{"increment": 1_300_000}],
        },
    )

    rows, _ = build_candidate_index(candidates_dir=candidates_dir)
    statuses = {row["candidate_key"]: row["status"] for row in rows}

    assert statuses["true.recursive"] == "certificate_blocked"
    assert (
        statuses["false.finmodel.setcheck.affine_mod_probe.mod17.a7.b11.c0.all_equations"]
        == "certificate_blocked"
    )
    assert statuses["partial_scan_summary"] == "needs_review"
    assert statuses["false.predicate"] == "needs_review"
    assert statuses["selected_summary"] == "needs_review"


def test_build_mining_state_summarizes_baseline_and_candidates(tmp_path: Path):
    registry_dir = tmp_path / "registry"
    _write_minimal_registry(registry_dir)
    candidate_summary = {
        "summary_file_count": 1,
        "status_counts": {"register_ready": 1},
        "top_by_increment": [{"candidate_key": "true.high", "best_increment": 1_200_000}],
        "blocked_high_roi": [],
    }

    state = build_mining_state(
        registry_dir=registry_dir,
        candidate_index_summary=candidate_summary,
        codex_state_sqlite=None,
        cwd=tmp_path,
    )

    assert state["baseline"]["coverage"]["unresolved_estimate"] == 500
    assert state["baseline"]["strategies"]["counts_by_verdict"] == {
        "False": 1,
        "True": 1,
    }
    assert state["baseline"]["strategies"]["absorbed_strategy_keys"] == [
        "true.proof.templatecheck.demo_component"
    ]
    assert state["candidate_index"]["status_counts"] == {"register_ready": 1}
    assert state["coordination"]["merge_lock_recommended"] is False


def test_build_merge_review_queue_prioritizes_postedge7_and_blocked_affine():
    rows = [
        {
            "candidate_key": "true.proof.templatecheck.postedge7.v1",
            "status": "register_ready",
            "best_increment": 2_700_000,
            "path": "candidates/postedge7_summary.json",
            "smoke": {
                "observed_run_count": 1,
                "all_accepted_observed": True,
                "rejection_observed": False,
                "max_accepted_count": 120,
                "max_total_count": 120,
            },
        },
        {
            "candidate_key": "false.finmodel.setcheck.affine_mod_probe.mod17",
            "status": "certificate_blocked",
            "best_increment": 4_200_000,
            "path": "candidates/affine_summary.json",
            "status_text_sample": "high_roi_but_still_blocked_not_merge_ready",
            "smoke": {
                "observed_run_count": 1,
                "all_accepted_observed": False,
                "rejection_observed": True,
                "max_accepted_count": 0,
                "max_total_count": 1,
            },
        },
        {
            "candidate_key": "true.old.v1",
            "status": "needs_smoke_or_merge_review",
            "best_increment": 9_000_000,
            "path": "candidates/old_summary.json",
            "status_text_sample": "stale superseded by v2",
            "smoke": {},
        },
    ]
    mining_state = {
        "baseline": {
            "coverage": {
                "total_pairs": 1000,
                "unresolved_estimate": 100,
                "conflict_count": 0,
            }
        },
        "active_goal_sessions": [{"short_id": "abc", "title": "continue"}],
    }

    queue = build_merge_review_queue(rows=rows, mining_state=mining_state)

    assert queue["queue_counts"]["postedge7_controller_review"] == 1
    assert queue["queue_counts"]["register_ready_main"] == 1
    assert queue["queue_counts"]["certificate_blocked_high_roi"] == 1
    assert queue["queue_counts"]["stale_or_subsumed"] == 1
    markdown = render_merge_review_markdown(queue)
    assert "postedge7 总控复核" in markdown
    assert "affine_mod_probe.mod17" in markdown


def test_build_merge_review_queue_removes_registered_candidates_from_active_queue():
    rows = [
        {
            "candidate_key": "true.proof.templatecheck.postedge7.v1",
            "status": "register_ready",
            "best_increment": 2_700_000,
            "path": "candidates/postedge7_summary.json",
            "smoke": {},
        }
    ]
    mining_state = {
        "baseline": {
            "coverage": {"unresolved_estimate": 100},
            "strategies": {
                "active_strategy_keys": ["true.proof.templatecheck.postedge7"],
            },
        },
        "active_goal_sessions": [],
    }

    queue = build_merge_review_queue(rows=rows, mining_state=mining_state)

    assert queue["queue_counts"]["postedge7_controller_review"] == 0
    assert queue["queue_counts"]["register_ready_main"] == 0
    assert queue["queue_counts"]["stale_or_subsumed"] == 1


def test_build_merge_review_queue_removes_absorbed_component_candidates():
    rows = [
        {
            "candidate_key": "true.proof.templatecheck.component.v1",
            "status": "register_ready",
            "best_increment": 1_200_000,
            "path": "candidates/component_summary.json",
            "smoke": {},
        }
    ]
    mining_state = {
        "baseline": {
            "coverage": {"unresolved_estimate": 100},
            "strategies": {
                "active_strategy_keys": ["true.proof.templatecheck.rollup"],
                "absorbed_strategy_keys": ["true.proof.templatecheck.component"],
            },
        },
        "active_goal_sessions": [],
    }

    queue = build_merge_review_queue(rows=rows, mining_state=mining_state)

    assert queue["queue_counts"]["register_ready_main"] == 0
    assert queue["queue_counts"]["stale_or_subsumed"] == 1


def test_build_merge_review_queue_removes_current_rescore_absorbed_candidates():
    absorbed_path = "data/processed/order5_strategy_registry/candidates/old_summary.json"
    rows = [
        {
            "candidate_key": "true.old.v1",
            "status": "register_ready",
            "best_increment": 2_700_000,
            "path": absorbed_path,
            "smoke": {
                "observed_run_count": 1,
                "all_accepted_observed": True,
                "rejection_observed": False,
                "max_accepted_count": 120,
                "max_total_count": 120,
            },
        },
        {
            "candidate_key": "controller_rescore",
            "status": "merged_or_subsumed",
            "path": "data/processed/order5_strategy_registry/candidates/rescore_summary.json",
            "absorbed_candidate_summary_paths": [absorbed_path],
        },
    ]
    mining_state = {
        "baseline": {
            "coverage": {
                "total_pairs": 1000,
                "unresolved_estimate": 100,
                "conflict_count": 0,
            }
        },
        "active_goal_sessions": [],
    }

    queue = build_merge_review_queue(rows=rows, mining_state=mining_state)

    assert queue["queue_counts"]["register_ready_main"] == 0
    assert queue["queue_counts"]["stale_or_subsumed"] == 2


def test_candidate_summary_can_explicitly_absorb_superseded_paths(tmp_path: Path):
    old_path = "data/processed/order5_strategy_registry/candidates/old_main_summary.json"
    summary_path = tmp_path / "current_rescore_summary.json"
    _write_json(
        summary_path,
        {
            "candidate_key": "false.current_graph.tail",
            "status": "current_graph_tail_candidate",
            "best_increment": 250_000,
            "absorbed_candidate_summary_paths": [old_path],
        },
    )

    row = summarize_candidate_file(summary_path)

    assert row["status"] == "tail_candidate"
    assert row["absorbed_candidate_summary_paths"] == [old_path]


def test_build_merge_review_queue_removes_explicitly_absorbed_candidates():
    old_path = "data/processed/order5_strategy_registry/candidates/old_main_summary.json"
    rows = [
        {
            "candidate_key": "false.old.main",
            "status": "needs_smoke_or_merge_review",
            "best_increment": 2_700_000,
            "path": old_path,
            "smoke": {},
        },
        {
            "candidate_key": "false.current_graph.tail",
            "status": "tail_candidate",
            "best_increment": 250_000,
            "path": "data/processed/order5_strategy_registry/candidates/current_rescore_summary.json",
            "absorbed_candidate_summary_paths": [old_path],
            "smoke": {},
        },
    ]
    mining_state = {
        "baseline": {
            "coverage": {
                "total_pairs": 1000,
                "unresolved_estimate": 100,
                "conflict_count": 0,
            }
        },
        "active_goal_sessions": [],
    }

    queue = build_merge_review_queue(rows=rows, mining_state=mining_state)

    assert queue["queue_counts"]["needs_rescore_or_smoke_main"] == 0
    assert queue["queue_counts"]["tail_candidates"] == 1
    assert queue["queue_counts"]["stale_or_subsumed"] == 1


def test_render_merge_review_markdown_reports_empty_main_queue():
    queue = {
        "baseline": {
            "total_pairs": 1000,
            "deterministic_false_covered": 300,
            "deterministic_true_covered": 200,
            "unresolved_estimate": 500,
            "conflict_count": 0,
        },
        "active_goal_count": 0,
        "queue_counts": {
            "postedge7_controller_review": 0,
            "register_ready_main": 0,
            "needs_rescore_or_smoke_main": 0,
            "certificate_blocked_high_roi": 1,
            "tail_candidates": 0,
            "parking_lot": 0,
            "needs_metadata_review": 0,
            "stale_or_subsumed": 1,
        },
        "queues": {
            "postedge7_controller_review": [],
            "register_ready_main": [],
            "needs_rescore_or_smoke_main": [],
            "certificate_blocked_high_roi": [],
            "tail_candidates": [],
        },
    }

    markdown = render_merge_review_markdown(queue)

    assert "当前没有 register-ready 或 needs-rescore/smoke 主线候选" in markdown


def test_update_order5_strategy_mining_state_cli_writes_outputs(tmp_path: Path):
    registry_dir = tmp_path / "registry"
    _write_minimal_registry(registry_dir)
    _write_json(
        registry_dir / "candidates" / "candidate_summary.json",
        {
            "candidate_key": "true.high",
            "exact_union_increment": 1_200_000,
            "smoke": {"accepted_count": 2, "total_count": 2},
        },
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/data/update_order5_strategy_mining_state.py",
            "--registry-dir",
            str(registry_dir),
            "--no-codex-sessions",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )

    payload = json.loads(result.stdout)
    assert payload["summary_file_count"] == 1
    assert (registry_dir / "mining_state.json").exists()
    assert (registry_dir / "candidate_index.jsonl").exists()
    assert (registry_dir / "candidate_index_summary.json").exists()


def test_build_order5_strategy_merge_review_queue_cli_writes_report(tmp_path: Path):
    registry_dir = tmp_path / "registry"
    _write_minimal_registry(registry_dir)
    _write_json(
        registry_dir / "mining_state.json",
        {
            "baseline": {
                "coverage": {
                    "total_pairs": 1000,
                    "unresolved_estimate": 500,
                    "conflict_count": 0,
                }
            },
            "active_goal_sessions": [],
        },
    )
    candidate_index = registry_dir / "candidate_index.jsonl"
    candidate_index.write_text(
        json.dumps(
            {
                "candidate_key": "true.proof.templatecheck.postedge7.v1",
                "status": "register_ready",
                "best_increment": 2_700_000,
                "path": "candidate_summary.json",
                "smoke": {
                    "observed_run_count": 1,
                    "all_accepted_observed": True,
                    "rejection_observed": False,
                    "max_accepted_count": 120,
                    "max_total_count": 120,
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    output_json = tmp_path / "queue.json"
    output_md = tmp_path / "queue.md"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/data/build_order5_strategy_merge_review_queue.py",
            "--registry-dir",
            str(registry_dir),
            "--output-json",
            str(output_json),
            "--output-markdown",
            str(output_md),
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )

    payload = json.loads(result.stdout)
    assert payload["queue_counts"]["postedge7_controller_review"] == 1
    assert output_json.exists()
    assert "postedge7 总控复核" in output_md.read_text(encoding="utf-8")
