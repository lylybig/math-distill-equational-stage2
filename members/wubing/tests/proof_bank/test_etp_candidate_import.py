import hashlib
import json
from pathlib import Path

from math_distill_stage2.dataset_io import read_jsonl
from math_distill_stage2.proof_bank.etp_candidate_import import (
    build_etp_eq2_candidate_run,
    extract_submission_proof_body,
)


def test_extract_submission_proof_body_keeps_singleton_prefix():
    code = _certificate_code()

    proof_body = extract_submission_proof_body(code)

    assert proof_body.startswith("have singleton")
    assert "intro G _ h" not in proof_body
    assert "exact singleton x y" in proof_body


def test_build_etp_eq2_candidate_run_materializes_accepted_attempt(tmp_path: Path):
    candidates = tmp_path / "candidates"
    candidates.mkdir()
    code = _certificate_code()
    problem_id = "etp_eq42_to_eq2_native_explicit_test"
    accepted_sources = candidates / "accepted.jsonl"
    accepted_sources.write_text(
        json.dumps(
            {
                "artifact_path": "http://judge/jobs/test",
                "candidate_key": (
                    "true.proof.templatecheck.etp_order5_eq2_singleton."
                    "native_explicit.native_explicit_ge5m.combo0001.v1"
                ),
                "code_bytes": len(code.encode("utf-8")),
                "code_sha256": hashlib.sha256(code.encode("utf-8")).hexdigest(),
                "eq1_id": 42,
                "eq2_id": 2,
                "error_code": "",
                "problem_id": problem_id,
                "raw_true_increment": 7,
                "status": "accepted",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (candidates / "smoke_input.jsonl").write_text(
        json.dumps(
            {
                "id": problem_id,
                "answer": {"call": "judge", "code": code, "verdict": "true"},
                "problem": {
                    "answer": True,
                    "eq1_id": 42,
                    "eq2_id": 2,
                    "equation1": "x = y",
                    "equation2": "x = y",
                    "id": problem_id,
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (candidates / "smoke_results.jsonl").write_text(
        json.dumps(
            {
                "artifact_path": "http://judge/jobs/test",
                "message": "remote judge-v2 accepted certificate",
                "problem_id": problem_id,
                "status": "accepted",
                "verdict": "true",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    summary = build_etp_eq2_candidate_run(
        accepted_sources_path=accepted_sources,
        candidates_dir=candidates,
        run_dir=tmp_path / "run",
        source_run_id="full-eq1-to-equation2-seedgate-test-etp",
    )

    assert summary["accepted_count"] == 1
    [attempt] = read_jsonl(tmp_path / "run" / "generated_attempts.jsonl")
    assert attempt["judge_status"] == "accepted"
    assert attempt["official_judge_status"] == "accepted"
    assert attempt["source_run_id"] == "full-eq1-to-equation2-seedgate-test-etp"
    [problem] = read_jsonl(tmp_path / "run" / "input_problems.jsonl")
    assert problem["eq1_id"] == 42
    assert problem["eq2_id"] == 2
    assert (tmp_path / "run" / "proof_bodies" / attempt["proof_body_sha256"][:2]).exists()
    assert (tmp_path / "run" / "certificates" / attempt["certificate_sha256"][:2]).exists()
    assert (tmp_path / "run" / "judge_results" / attempt["judge_result_sha256"][:2]).exists()


def _certificate_code() -> str:
    return (
        "import JudgeProblem\n"
        "set_option linter.unusedVariables false\n\n"
        "def submission : Goal := by\n"
        "  intro G _ h\n"
        "  have singleton : ∀ (x y : G), x = y := by\n"
        "    intro x y\n"
        "    exact h x y\n"
        "  intro x y\n"
        "  exact singleton x y\n"
    )
