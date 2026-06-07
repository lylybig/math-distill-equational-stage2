import json
from pathlib import Path

from math_distill_stage2.dataset_io import write_jsonl
from math_distill_stage2.proof_bank.bank import init_bank, rebuild_indexes
from math_distill_stage2.proof_bank.quality_audit import audit_proof_bank_quality
from math_distill_stage2.proof_bank.storage import write_content_addressed_text, write_json


def test_quality_audit_continues_for_healthy_recent_cycle(tmp_path: Path):
    bank = tmp_path / "bank"
    init_bank(bank)
    certificate = write_content_addressed_text(bank, "certificates", "certificate\n", ".lean")
    proof_body = write_content_addressed_text(bank, "proof_bodies", "proof\n", ".lean")
    judge_result = write_content_addressed_text(
        bank, "judge_results", '{"status":"accepted"}\n', ".json"
    )
    write_jsonl(
        bank / "attempts.jsonl",
        [
            {
                "schema_version": 1,
                "attempt_id": "attempt:run-1:000001",
                "problem_key": "implication:sig:1111111111111111:2222222222222222",
                "certificate_kind": "true_proof",
                "certificate_sha256": certificate.sha256,
                "proof_body_sha256": proof_body.sha256,
                "judge_result_sha256": judge_result.sha256,
                "official_judge_status": "accepted",
                "judge_status": "accepted",
                "judge_error_kind": "none",
                "source_run_id": "run-1",
                "created_at": "2026-05-11T00:00:00Z",
            },
            {
                "schema_version": 1,
                "attempt_id": "attempt:run-1:000002",
                "problem_key": "implication:sig:3333333333333333:4444444444444444",
                "certificate_kind": "true_proof",
                "official_judge_status": "incorrect",
                "judge_status": "rejected",
                "judge_error_kind": "lean_type_error",
                "source_run_id": "run-1",
                "created_at": "2026-05-11T00:01:00Z",
            },
        ],
    )
    rebuild_indexes(bank)
    run_summary = tmp_path / "summary.json"
    write_json(
        run_summary,
        {
            "source_run_id": "run-1",
            "attempt_count": 2,
            "accepted_count": 1,
            "rejected_count": 1,
            "skipped_count": 0,
            "error_count": 0,
            "timeout_count": 0,
            "missing_response_count": 0,
        },
    )
    sampled_manifest = tmp_path / "sample.manifest.json"
    write_json(
        sampled_manifest,
        {
            "selected_count": 10,
            "selected_by_stratum": {
                "high_signal_failed_attempts": 6,
                "unsolved_trace_or_timeout": 2,
                "direct_order4_true_exploration": 2,
            },
            "excluded_accepted_count": 1,
            "excluded_attempt_ceiling_count": 0,
        },
    )

    audit = audit_proof_bank_quality(
        bank=bank,
        run_summary_path=run_summary,
        sampled_manifest_path=sampled_manifest,
    )

    assert audit["decision"] == "continue"
    assert audit["cycle"]["accepted_yield"] == 0.5
    assert audit["source_balance"]["direct_order4_true_exploration"]["selected_count"] == 2
    assert audit["bank_check"]["ok"] is True


def test_quality_audit_adjusts_sampling_when_direct_order4_is_missing(tmp_path: Path):
    bank = tmp_path / "bank"
    init_bank(bank)
    run_summary = tmp_path / "summary.json"
    write_json(
        run_summary,
        {
            "source_run_id": "run-1",
            "attempt_count": 2,
            "accepted_count": 0,
            "rejected_count": 2,
            "skipped_count": 0,
            "error_count": 0,
            "timeout_count": 0,
            "missing_response_count": 0,
        },
    )
    sampled_manifest = tmp_path / "sample.manifest.json"
    write_json(
        sampled_manifest,
        {
            "selected_count": 10,
            "selected_by_stratum": {
                "high_signal_failed_attempts": 8,
                "unsolved_trace_or_timeout": 2,
            },
        },
    )

    audit = audit_proof_bank_quality(
        bank=bank,
        run_summary_path=run_summary,
        sampled_manifest_path=sampled_manifest,
    )

    assert audit["decision"] == "continue_with_adjusted_sampling"
    assert "missing direct_order4_true_exploration samples" in audit["notes"]


def test_quality_audit_pauses_after_repeated_zero_accepted_cycles(tmp_path: Path):
    bank = tmp_path / "bank"
    init_bank(bank)
    run_summary = tmp_path / "summary.json"
    write_json(
        run_summary,
        {
            "source_run_id": "run-3",
            "attempt_count": 1,
            "accepted_count": 0,
            "rejected_count": 1,
            "skipped_count": 0,
            "error_count": 0,
            "timeout_count": 0,
            "missing_response_count": 0,
        },
    )
    marathon_state = tmp_path / "marathon_state.json"
    write_json(
        marathon_state,
        {
            "marathon_id": "fixture",
            "consecutive_zero_accepted_cycles": 2,
        },
    )

    audit = audit_proof_bank_quality(
        bank=bank,
        run_summary_path=run_summary,
        marathon_state_path=marathon_state,
    )

    assert audit["decision"] == "pause_for_debug"
    assert "too many consecutive zero-accepted cycles" in audit["notes"]
