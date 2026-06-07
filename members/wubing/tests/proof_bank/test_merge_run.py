import json
from pathlib import Path

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.proof_bank.bank import check_bank, init_bank, merge_run, preview_merge_run
from math_distill_stage2.proof_bank.storage import (
    content_addressed_path,
    write_content_addressed_text,
)


def test_merge_run_is_idempotent(tmp_path: Path):
    bank = tmp_path / "bank"
    run = tmp_path / "run"
    init_bank(bank)
    run.mkdir()
    (run / "manifest.json").write_text(json.dumps({"source_run_id": "run-1"}), encoding="utf-8")
    write_jsonl(
        run / "input_problems.jsonl",
        [
            {
                "schema_version": 1,
                "problem_key": "implication:sig:1111111111111111:2222222222222222",
                "problem_aliases": ["fixture:true_1_2"],
                "equation1": "x = x",
                "equation2": "x = x",
                "eq1_signature": "v0=v0",
                "eq2_signature": "v0=v0",
                "source_datasets": ["fixture"],
            }
        ],
    )
    certificate = write_content_addressed_text(run, "certificates", "certificate\n", ".lean")
    proof_body = write_content_addressed_text(run, "proof_bodies", "proof body\n", ".lean")
    judge_result = write_content_addressed_text(
        run, "judge_results", '{"status":"accepted"}\n', ".json"
    )
    raw_response = write_content_addressed_text(
        run, "raw_responses_by_hash", '{"verdict":"true"}\n', ".txt"
    )
    write_jsonl(
        run / "generated_attempts.jsonl",
        [
            {
                "schema_version": 1,
                "attempt_id": "attempt:run-1:000001",
                "problem_key": "implication:sig:1111111111111111:2222222222222222",
                "certificate_kind": "true_proof",
                "certificate_sha256": certificate.sha256,
                "proof_body_sha256": proof_body.sha256,
                "judge_result_sha256": judge_result.sha256,
                "raw_response_sha256": raw_response.sha256,
                "judge_commit": "6805e2323018fbd8a85f41ca09fc33d74d5a02a5",
                "official_judge_status": "accepted",
                "judge_status": "accepted",
                "judge_error_kind": "none",
                "source_run_id": "run-1",
                "created_at": "2026-05-11T00:00:00Z",
            }
        ],
    )

    first = merge_run(bank, run)
    second = merge_run(bank, run)

    assert first["new_problems"] == 1
    assert first["new_attempts"] == 1
    assert second["new_problems"] == 0
    assert second["new_attempts"] == 0
    assert len(read_jsonl(bank / "attempts.jsonl")) == 1
    assert len(read_jsonl(bank / "accepted.jsonl")) == 1


def test_preview_merge_run_validates_without_writing_bank(tmp_path: Path):
    bank = tmp_path / "bank"
    run = tmp_path / "run"
    init_bank(bank)
    run.mkdir()
    (run / "manifest.json").write_text(json.dumps({"source_run_id": "run-1"}), encoding="utf-8")
    write_jsonl(
        run / "input_problems.jsonl",
        [
            {
                "schema_version": 1,
                "problem_key": "implication:sig:1111111111111111:2222222222222222",
                "equation1": "x = x",
                "equation2": "x = x",
                "eq1_signature": "v0=v0",
                "eq2_signature": "v0=v0",
                "source_datasets": ["fixture"],
            }
        ],
    )
    certificate = write_content_addressed_text(run, "certificates", "certificate\n", ".lean")
    proof_body = write_content_addressed_text(run, "proof_bodies", "proof body\n", ".lean")
    judge_result = write_content_addressed_text(
        run, "judge_results", '{"status":"accepted"}\n', ".json"
    )
    write_jsonl(
        run / "generated_attempts.jsonl",
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
            }
        ],
    )

    preview = preview_merge_run(bank, run)

    assert preview["dry_run"] is True
    assert preview["new_problems"] == 1
    assert preview["new_attempts"] == 1
    assert read_jsonl(bank / "attempts.jsonl") == []
    assert read_jsonl(bank / "problems.jsonl") == []


def test_merge_run_copies_attempt_blobs_into_global_bank(tmp_path: Path):
    bank = tmp_path / "bank"
    run = tmp_path / "run"
    init_bank(bank)
    run.mkdir()
    (run / "manifest.json").write_text(json.dumps({"source_run_id": "run-1"}), encoding="utf-8")
    write_jsonl(
        run / "input_problems.jsonl",
        [
            {
                "schema_version": 1,
                "problem_key": "implication:sig:1111111111111111:2222222222222222",
                "equation1": "x = x",
                "equation2": "x = x",
                "eq1_signature": "v0=v0",
                "eq2_signature": "v0=v0",
                "source_datasets": ["fixture"],
            }
        ],
    )
    certificate = write_content_addressed_text(run, "certificates", "certificate\n", ".lean")
    proof_body = write_content_addressed_text(run, "proof_bodies", "proof body\n", ".lean")
    judge_result = write_content_addressed_text(
        run, "judge_results", '{"status":"accepted"}\n', ".json"
    )
    raw_response = write_content_addressed_text(
        run, "raw_responses_by_hash", '{"verdict":"true"}\n', ".txt"
    )
    write_jsonl(
        run / "generated_attempts.jsonl",
        [
            {
                "schema_version": 1,
                "attempt_id": "attempt:run-1:000001",
                "problem_key": "implication:sig:1111111111111111:2222222222222222",
                "certificate_kind": "true_proof",
                "certificate_sha256": certificate.sha256,
                "proof_body_sha256": proof_body.sha256,
                "judge_result_sha256": judge_result.sha256,
                "raw_response_sha256": raw_response.sha256,
                "official_judge_status": "accepted",
                "judge_status": "accepted",
                "judge_error_kind": "none",
                "source_run_id": "run-1",
                "created_at": "2026-05-11T00:00:00Z",
            }
        ],
    )

    first = merge_run(bank, run)
    second = merge_run(bank, run)

    assert first["copied_blobs"] == 4
    assert second["copied_blobs"] == 0
    assert content_addressed_path(bank, "certificates", certificate.sha256, ".lean").exists()
    assert content_addressed_path(bank, "proof_bodies", proof_body.sha256, ".lean").exists()
    assert content_addressed_path(bank, "judge_results", judge_result.sha256, ".json").exists()
    assert content_addressed_path(bank, "raw_responses", raw_response.sha256, ".txt").exists()
    assert check_bank(bank)["ok"] is True


def test_merge_run_writes_readable_by_problem_certificate_view(tmp_path: Path):
    bank = tmp_path / "bank"
    run = tmp_path / "run"
    init_bank(bank)
    run.mkdir()
    (run / "manifest.json").write_text(json.dumps({"source_run_id": "run-1"}), encoding="utf-8")
    write_jsonl(
        run / "input_problems.jsonl",
        [
            {
                "schema_version": 1,
                "problem_key": "implication:sig:1111111111111111:2222222222222222",
                "eq1_id": 392,
                "eq2_id": 4366,
                "equation1": "x ◇ y = (y ◇ z) ◇ z",
                "equation2": "x ◇ (y ◇ z) = y ◇ (w ◇ x)",
                "eq1_signature": "(v0*v1)=((v1*v2)*v2)",
                "eq2_signature": "(v0*(v1*v2))=(v1*(v3*v0))",
                "source_datasets": ["fixture"],
            }
        ],
    )
    certificate = write_content_addressed_text(run, "certificates", "certificate\n", ".lean")
    proof_body = write_content_addressed_text(run, "proof_bodies", "proof body\n", ".lean")
    judge_result = write_content_addressed_text(
        run, "judge_results", '{"status":"accepted"}\n', ".json"
    )
    write_jsonl(
        run / "generated_attempts.jsonl",
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
            }
        ],
    )

    merge_run(bank, run)

    view = bank / "by_problem" / "eq1-392-eq2-4366"
    metadata = json.loads((view / "metadata.json").read_text(encoding="utf-8"))
    assert (view / "certificate.lean").read_text(encoding="utf-8") == "certificate\n"
    assert metadata["eq1_id"] == 392
    assert metadata["eq2_id"] == 4366
    assert metadata["equation1"] == "x ◇ y = (y ◇ z) ◇ z"
    assert metadata["equation2"] == "x ◇ (y ◇ z) = y ◇ (w ◇ x)"
    assert metadata["certificate_sha256"] == certificate.sha256


def test_by_problem_view_lists_multiple_accepted_certificates(tmp_path: Path):
    bank = tmp_path / "bank"
    run = tmp_path / "run"
    init_bank(bank)
    run.mkdir()
    (run / "manifest.json").write_text(json.dumps({"source_run_id": "run-1"}), encoding="utf-8")
    write_jsonl(
        run / "input_problems.jsonl",
        [
            {
                "schema_version": 1,
                "problem_key": "implication:sig:1111111111111111:2222222222222222",
                "eq1_id": 392,
                "eq2_id": 4366,
                "equation1": "x ◇ y = (y ◇ z) ◇ z",
                "equation2": "x ◇ (y ◇ z) = y ◇ (w ◇ x)",
                "eq1_signature": "(v0*v1)=((v1*v2)*v2)",
                "eq2_signature": "(v0*(v1*v2))=(v1*(v3*v0))",
                "source_datasets": ["fixture"],
            }
        ],
    )
    certificate_1 = write_content_addressed_text(run, "certificates", "certificate 1\n", ".lean")
    proof_body_1 = write_content_addressed_text(run, "proof_bodies", "proof body 1\n", ".lean")
    judge_result_1 = write_content_addressed_text(
        run, "judge_results", '{"status":"accepted","n":1}\n', ".json"
    )
    certificate_2 = write_content_addressed_text(run, "certificates", "certificate 2\n", ".lean")
    proof_body_2 = write_content_addressed_text(run, "proof_bodies", "proof body 2\n", ".lean")
    judge_result_2 = write_content_addressed_text(
        run, "judge_results", '{"status":"accepted","n":2}\n', ".json"
    )
    write_jsonl(
        run / "generated_attempts.jsonl",
        [
            {
                "schema_version": 1,
                "attempt_id": "attempt:run-1:000001",
                "problem_key": "implication:sig:1111111111111111:2222222222222222",
                "certificate_kind": "true_proof",
                "certificate_sha256": certificate_1.sha256,
                "proof_body_sha256": proof_body_1.sha256,
                "judge_result_sha256": judge_result_1.sha256,
                "official_judge_status": "accepted",
                "judge_status": "accepted",
                "judge_error_kind": "none",
                "source_run_id": "run-1",
                "created_at": "2026-05-11T00:00:00Z",
            },
            {
                "schema_version": 1,
                "attempt_id": "attempt:run-1:000002",
                "problem_key": "implication:sig:1111111111111111:2222222222222222",
                "certificate_kind": "true_proof",
                "certificate_sha256": certificate_2.sha256,
                "proof_body_sha256": proof_body_2.sha256,
                "judge_result_sha256": judge_result_2.sha256,
                "official_judge_status": "accepted",
                "judge_status": "accepted",
                "judge_error_kind": "none",
                "source_run_id": "run-1",
                "created_at": "2026-05-11T00:01:00Z",
            },
        ],
    )

    merge_run(bank, run)

    view = bank / "by_problem" / "eq1-392-eq2-4366"
    metadata = json.loads((view / "metadata.json").read_text(encoding="utf-8"))
    first_view = view / "certificates" / "000001_attempt-run-1-000001" / "certificate.lean"
    second_view = view / "certificates" / "000002_attempt-run-1-000002" / "certificate.lean"
    assert metadata["accepted_attempt_count"] == 2
    assert metadata["best_attempt_id"] == "attempt:run-1:000001"
    assert metadata["certificates"][0]["attempt_id"] == "attempt:run-1:000001"
    assert metadata["certificates"][0]["certificate_path"] == (
        "certificates/000001_attempt-run-1-000001/certificate.lean"
    )
    assert metadata["certificates"][1]["attempt_id"] == "attempt:run-1:000002"
    assert (view / "certificate.lean").read_text(encoding="utf-8") == "certificate 1\n"
    assert first_view.read_text(encoding="utf-8") == "certificate 1\n"
    assert second_view.read_text(encoding="utf-8") == "certificate 2\n"


def test_check_bank_reports_missing_accepted_attempt_blobs(tmp_path: Path):
    bank = tmp_path / "bank"
    init_bank(bank)
    write_jsonl(
        bank / "attempts.jsonl",
        [
            {
                "schema_version": 1,
                "attempt_id": "attempt:run-1:000001",
                "problem_key": "implication:sig:1111111111111111:2222222222222222",
                "certificate_kind": "true_proof",
                "certificate_sha256": "a" * 64,
                "proof_body_sha256": "b" * 64,
                "judge_result_sha256": "c" * 64,
                "official_judge_status": "accepted",
                "judge_status": "accepted",
                "judge_error_kind": "none",
            }
        ],
    )

    result = check_bank(bank)

    assert result["ok"] is False
    assert "missing certificates blob for attempt:run-1:000001" in result["errors"]
    assert "missing proof_bodies blob for attempt:run-1:000001" in result["errors"]
    assert "missing judge_results blob for attempt:run-1:000001" in result["errors"]
