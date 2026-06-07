from pathlib import Path

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.proof_bank.bank import (
    check_bank,
    init_bank,
    rebuild_indexes,
)


def accepted_attempt(problem_key: str, attempt_id: str) -> dict:
    return {
        "schema_version": 1,
        "attempt_id": attempt_id,
        "problem_key": problem_key,
        "certificate_kind": "true_proof",
        "certificate_sha256": "a" * 64,
        "judge_commit": "6805e2323018fbd8a85f41ca09fc33d74d5a02a5",
        "official_judge_status": "accepted",
        "judge_status": "accepted",
        "judge_error_kind": "none",
        "source_run_id": "run-1",
        "created_at": "2026-05-11T00:00:00Z",
    }


def test_init_bank_writes_empty_ledgers_and_manifest(tmp_path: Path):
    summary = init_bank(tmp_path)

    assert summary["bank"] == str(tmp_path)
    assert (tmp_path / "bank_manifest.json").exists()
    assert (tmp_path / "problems.jsonl").read_text(encoding="utf-8") == ""
    assert (tmp_path / "attempts.jsonl").read_text(encoding="utf-8") == ""
    assert (tmp_path / "accepted.jsonl").read_text(encoding="utf-8") == ""
    assert (tmp_path / "latest_by_problem.jsonl").read_text(encoding="utf-8") == ""


def test_rebuild_indexes_derives_accepted_and_latest(tmp_path: Path):
    init_bank(tmp_path)
    problem_key = "implication:sig:1111111111111111:2222222222222222"
    write_jsonl(
        tmp_path / "problems.jsonl",
        [
            {
                "schema_version": 1,
                "problem_key": problem_key,
                "problem_aliases": [],
                "equation1": "x = x",
                "equation2": "x = x",
                "eq1_signature": "v0=v0",
                "eq2_signature": "v0=v0",
                "source_datasets": ["fixture"],
            }
        ],
    )
    write_jsonl(
        tmp_path / "attempts.jsonl",
        [
            {
                **accepted_attempt(problem_key, "attempt:run-1:000001"),
                "judge_result_sha256": "b" * 64,
            },
            {
                "schema_version": 1,
                "attempt_id": "attempt:run-1:000002",
                "problem_key": problem_key,
                "certificate_kind": "true_proof",
                "judge_status": "rejected",
                "official_judge_status": "incorrect",
                "judge_error_kind": "lean_type_error",
                "source_run_id": "run-1",
                "created_at": "2026-05-11T00:01:00Z",
            },
        ],
    )

    summary = rebuild_indexes(tmp_path)

    accepted_rows = read_jsonl(tmp_path / "accepted.jsonl")
    latest_rows = read_jsonl(tmp_path / "latest_by_problem.jsonl")
    assert summary["accepted_count"] == 1
    assert accepted_rows[0]["attempt_id"] == "attempt:run-1:000001"
    assert latest_rows[0]["latest_attempt_id"] == "attempt:run-1:000002"
    assert latest_rows[0]["accepted_attempt_count"] == 1
    assert latest_rows[0]["rejected_attempt_count"] == 1


def test_check_bank_reports_duplicate_attempt_ids(tmp_path: Path):
    init_bank(tmp_path)
    problem_key = "implication:sig:1111111111111111:2222222222222222"
    row = accepted_attempt(problem_key, "attempt:run-1:000001")
    write_jsonl(tmp_path / "attempts.jsonl", [row, row])

    result = check_bank(tmp_path)

    assert result["ok"] is False
    assert "duplicate attempt_id: attempt:run-1:000001" in result["errors"]
