import json
from pathlib import Path

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.proof_bank.import_responses import (
    extract_response,
    import_responses,
    normalize_proof_body,
    official_problem_for_judge,
    preflight_raw_responses,
    wrap_true_certificate,
)
from math_distill_stage2.proof_bank.judge_classification import classify_official_result


def test_extract_response_from_strict_json():
    extracted = extract_response('{"verdict":"true","proof":"intro x\\nexact h x"}')

    assert extracted.proof == "intro x\nexact h x"
    assert extracted.error_kind is None


def test_extract_response_accepts_common_proof_aliases():
    extracted = extract_response('{"verdict":"true","code":"intro x\\nexact h x"}')

    assert extracted.proof == "intro x\nexact h x"
    assert extracted.error_kind is None


def test_extract_response_accepts_nested_answer_payload():
    extracted = extract_response(
        '{"answer":{"verdict":"true","proof":"intro x\\nexact h x"}}'
    )

    assert extracted.proof == "intro x\nexact h x"
    assert extracted.error_kind is None


def test_extract_response_from_lean_fence():
    extracted = extract_response("```lean\nintro x\nexact h x\n```")

    assert extracted.proof == "intro x\nexact h x"
    assert extracted.error_kind is None


def test_normalize_proof_body_records_safe_actions():
    normalized = normalize_proof_body("intro x\nhave hx := congr_arg (fun t => t * x) rfl")

    assert normalized.proof == "intro x\nhave hx := congrArg (fun t => t ◇ x) rfl"
    assert normalized.actions == ["replace_star_with_diamond", "replace_congr_arg_with_congrArg"]


def test_wrap_true_certificate_uses_judge_problem_wrapper():
    code = wrap_true_certificate("intro x\nexact h x")

    assert code.startswith("import JudgeProblem\n\n")
    assert "def submission : Goal := by\n  intro G _ h\n" in code
    assert "  intro x\n  exact h x\n" in code


def test_preflight_raw_responses_requires_strict_json_and_blocks_forbidden_text(
    tmp_path: Path,
):
    run_dir = tmp_path / "run"
    (run_dir / "raw_responses").mkdir(parents=True)
    write_jsonl(
        run_dir / "input_problems.jsonl",
        [
            {
                "item_id": "000001",
                "problem_key": "p1",
                "eq1_id": 1,
                "eq2_id": 2,
                "equation1": "x = x",
                "equation2": "x = x",
            },
            {
                "item_id": "000002",
                "problem_key": "p2",
                "eq1_id": 1,
                "eq2_id": 3,
                "equation1": "x = x",
                "equation2": "x = y",
            },
            {
                "item_id": "000003",
                "problem_key": "p3",
                "eq1_id": 1,
                "eq2_id": 4,
                "equation1": "x = x",
                "equation2": "x = z",
            },
        ],
    )
    (run_dir / "raw_responses" / "000001.txt").write_text(
        '{"verdict":"true","proof":""}\n',
        encoding="utf-8",
    )
    (run_dir / "raw_responses" / "000002.txt").write_text(
        "```lean\nexact h\n```\n",
        encoding="utf-8",
    )
    (run_dir / "raw_responses" / "000003.txt").write_text(
        '{"verdict":"true","proof":"sorry"}\n',
        encoding="utf-8",
    )

    preflight = preflight_raw_responses(run_dir)

    assert preflight["ok"] is False
    issue_kinds = {(issue["item_id"], issue["error_kind"]) for issue in preflight["issues"]}
    assert ("000002", "invalid_raw_response_json") in issue_kinds
    assert ("000003", "forbidden_raw_response_text") in issue_kinds


def test_official_problem_for_judge_strips_proofbank_metadata():
    official = official_problem_for_judge(
        {
            "schema_version": 1,
            "item_id": "000001",
            "problem_key": "implication:sig:1111111111111111:2222222222222222",
            "source_problem_id": "true_1_2",
            "source_dataset": "fixture",
            "eq1_id": 1,
            "eq2_id": 2,
            "equation1": "x = x",
            "equation2": "x = x",
            "expected_verdict": True,
            "external_trace_available": False,
        }
    )

    assert official == {
        "id": "true_1_2",
        "eq1_id": 1,
        "eq2_id": 2,
        "equation1": "x = x",
        "equation2": "x = x",
        "answer": True,
    }


def test_classify_official_result_maps_accepted_and_type_errors():
    accepted = classify_official_result(
        {"status": "accepted", "stderr": "", "message": "", "error_code": ""}
    )
    rejected = classify_official_result(
        {"status": "incorrect", "stderr": "application type mismatch", "message": "", "error_code": ""}
    )

    assert accepted["judge_status"] == "accepted"
    assert accepted["judge_error_kind"] == "none"
    assert rejected["judge_status"] == "rejected"
    assert rejected["judge_error_kind"] == "lean_type_error"


def test_import_responses_writes_attempts_and_summary(tmp_path: Path):
    run_dir = tmp_path / "run"
    (run_dir / "raw_responses").mkdir(parents=True)
    write_jsonl(
        run_dir / "input_problems.jsonl",
        [
            {
                "schema_version": 1,
                "item_id": "000001",
                "problem_key": "implication:sig:1111111111111111:2222222222222222",
                "source_problem_id": "true_1_2",
                "source_dataset": "fixture",
                "eq1_id": 1,
                "eq2_id": 2,
                "equation1": "x = x",
                "equation2": "x = x",
                "expected_verdict": True,
            }
        ],
    )
    (run_dir / "manifest.json").write_text(
        json.dumps({"source_run_id": "run-1", "generator": {"model": "codex-gpt-5.5"}}),
        encoding="utf-8",
    )
    (run_dir / "raw_responses" / "000001.txt").write_text(
        '{"verdict":"true","proof":"intro x\\nexact rfl"}',
        encoding="utf-8",
    )

    def fake_judge(problem: dict, answer: dict) -> dict:
        assert set(problem) == {"id", "eq1_id", "eq2_id", "equation1", "equation2", "answer"}
        assert problem["id"] == "true_1_2"
        assert answer["verdict"] == "true"
        assert "def submission : Goal := by" in answer["code"]
        return {"status": "accepted", "stderr": "", "stdout": "", "message": "", "error_code": ""}

    summary = import_responses(run_dir, judge=fake_judge)

    attempts = read_jsonl(run_dir / "generated_attempts.jsonl")
    assert summary["accepted_count"] == 1
    assert attempts[0]["attempt_id"] == "attempt:run-1:000001"
    assert attempts[0]["judge_status"] == "accepted"
    assert attempts[0]["certificate_sha256"]
    assert (run_dir / "summary.json").exists()


def test_import_responses_can_verify_with_one_batch_judge_call(tmp_path: Path):
    run_dir = tmp_path / "run"
    (run_dir / "raw_responses").mkdir(parents=True)
    write_jsonl(
        run_dir / "input_problems.jsonl",
        [
            {
                "schema_version": 1,
                "item_id": "000001",
                "problem_key": "implication:sig:1111111111111111:2222222222222222",
                "source_problem_id": "true_1_2",
                "source_dataset": "fixture",
                "eq1_id": 1,
                "eq2_id": 2,
                "equation1": "x = x",
                "equation2": "x = x",
                "expected_verdict": True,
            },
            {
                "schema_version": 1,
                "item_id": "000002",
                "problem_key": "implication:sig:1111111111111111:3333333333333333",
                "source_problem_id": "true_1_3",
                "source_dataset": "fixture",
                "eq1_id": 1,
                "eq2_id": 3,
                "equation1": "x = x",
                "equation2": "x = y",
                "expected_verdict": True,
            },
        ],
    )
    (run_dir / "manifest.json").write_text(
        json.dumps({"source_run_id": "run-1", "generator": {"model": "codex-gpt-5.5"}}),
        encoding="utf-8",
    )
    (run_dir / "raw_responses" / "000001.txt").write_text(
        '{"verdict":"true","proof":"intro x\\nexact rfl"}',
        encoding="utf-8",
    )
    (run_dir / "raw_responses" / "000002.txt").write_text(
        '{"verdict":"true","proof":"intro x y\\nexact h x"}',
        encoding="utf-8",
    )
    calls = []

    def fake_batch_judge(requests: list[tuple[dict, dict]]) -> list[dict]:
        calls.append(requests)
        assert [problem["id"] for problem, _answer in requests] == ["true_1_2", "true_1_3"]
        assert all(answer["verdict"] == "true" for _problem, answer in requests)
        return [
            {"status": "accepted", "stderr": "", "stdout": "", "message": "", "error_code": ""},
            {
                "status": "incorrect",
                "stderr": "application type mismatch",
                "stdout": "",
                "message": "",
                "error_code": "",
            },
        ]

    summary = import_responses(run_dir, batch_judge=fake_batch_judge)

    attempts = read_jsonl(run_dir / "generated_attempts.jsonl")
    assert len(calls) == 1
    assert summary["attempt_count"] == 2
    assert summary["accepted_count"] == 1
    assert summary["rejected_count"] == 1
    assert [attempt["judge_status"] for attempt in attempts] == ["accepted", "rejected"]
    assert attempts[1]["judge_error_kind"] == "lean_type_error"
