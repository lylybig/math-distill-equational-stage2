import json
from pathlib import Path

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.proof_bank.external_olean_harvest import (
    build_external_olean_harvest_run,
    collect_external_olean_candidates,
    extract_submission_proof_body,
    parse_equations_file,
)
from math_distill_stage2.proof_bank.keying import problem_key_from_equations


def test_parse_equations_file_strips_quantified_variables(tmp_path: Path):
    equations_path = tmp_path / "equations.txt"
    equations_path.write_text(
        "def Equation1000 (G: Type*) [Magma G] := ∀ x y z w : G, "
        "x = y ◇ ((z ◇ w) ◇ (y ◇ y))\n",
        encoding="utf-8",
    )

    equations = parse_equations_file(equations_path)

    assert equations == {1000: "x = y ◇ ((z ◇ w) ◇ (y ◇ y))"}


def test_extract_submission_proof_body_strips_judge_wrapper():
    source = """import JudgeProblem

def submission : Goal := by
  intro G _ h
  intro x
  have hx := h x x
  exact hx
"""

    proof = extract_submission_proof_body(source)

    assert proof == "intro x\nhave hx := h x x\nexact hx"


def test_collect_external_olean_candidates_requires_olean_and_skips_accepted(
    tmp_path: Path,
):
    artifacts = tmp_path / ".artifacts"
    equations_path = _write_equations(
        tmp_path,
        {
            1000: "x = x",
            1133: "x = y",
            3653: "y = y",
            7777: "z = z",
            8888: "z = x",
        },
    )
    _write_submission_artifact(artifacts, "true_1000_1133.accepted", compiled=True)
    _write_submission_artifact(artifacts, "true_1000_3653.missing_olean", compiled=False)
    _write_submission_artifact(artifacts, "true_1000_7777.collect", compiled=True)
    _write_submission_artifact(artifacts, "true_1000_8888.external_rejected", compiled=True)

    bank = tmp_path / "bank"
    accepted_key = problem_key_from_equations("x = x", "x = y")
    external_rejected_key = problem_key_from_equations("x = x", "z = x")
    write_jsonl(
        bank / "attempts.jsonl",
        [
            {"problem_key": accepted_key, "judge_status": "accepted"},
            {
                "problem_key": external_rejected_key,
                "judge_status": "rejected",
                "source_run_id": "proofbank-20260513-external-olean-harvest-previous",
            },
        ],
    )

    candidates = collect_external_olean_candidates(
        artifacts_root=artifacts,
        equations_path=equations_path,
        bank=bank,
        limit=10,
    )

    assert len(candidates) == 1
    assert candidates[0].row["eq2_id"] == 7777
    assert candidates[0].row["source_candidate_stratum"] == "external_submission_olean_harvest"
    assert candidates[0].proof == "intro x\nexact x"


def test_build_external_olean_harvest_run_writes_preflight_clean_run(tmp_path: Path):
    artifacts = tmp_path / ".artifacts"
    equations_path = _write_equations(tmp_path, {1000: "x = x", 1133: "x = y"})
    _write_submission_artifact(artifacts, "true_1000_1133.good", compiled=True)

    run_dir = tmp_path / "runs" / "harvest"
    result = build_external_olean_harvest_run(
        run_dir=run_dir,
        source_run_id="harvest",
        artifacts_root=artifacts,
        equations_path=equations_path,
        bank=tmp_path / "bank",
        limit=1,
    )

    problems = read_jsonl(run_dir / "input_problems.jsonl")
    raw_payload = json.loads((run_dir / "raw_responses" / "000001.txt").read_text(encoding="utf-8"))
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))

    assert result["candidate_count"] == 1
    assert result["preflight"]["ok"] is True
    assert problems[0]["source_problem_id"] == "true_1000_1133"
    assert raw_payload == {"verdict": "true", "proof": "intro x\nexact x"}
    assert manifest["generator"]["mode"] == "external_submission_olean_harvest"


def test_collect_external_olean_candidates_can_follow_candidate_pool_order(tmp_path: Path):
    artifacts = tmp_path / ".artifacts"
    equations_path = _write_equations(
        tmp_path,
        {
            1000: "x = x",
            1133: "x = y",
            7777: "z = z",
        },
    )
    _write_submission_artifact(artifacts, "true_1000_1133.low_priority", compiled=True)
    _write_submission_artifact(artifacts, "true_1000_7777.high_priority", compiled=True)
    pool = tmp_path / "pool.jsonl"
    write_jsonl(
        pool,
        [
            {
                "source_problem_id": "true_1000_7777",
                "source_dataset": "order4_splits/dev_main",
                "source_candidate_stratum": "high_signal_failed_attempts",
                "source_result_path": "artifacts/runs/fixture.result.json",
                "eq1_id": 1000,
                "eq2_id": 7777,
                "equation1": "x = x",
                "equation2": "z = z",
                "expected_verdict": True,
                "priority_score": 99,
            }
        ],
    )

    candidates = collect_external_olean_candidates(
        artifacts_root=artifacts,
        equations_path=equations_path,
        bank=tmp_path / "bank",
        limit=10,
        candidate_pool=pool,
    )

    assert len(candidates) == 1
    row = candidates[0].row
    assert row["eq2_id"] == 7777
    assert row["source_dataset"] == "order4_splits/dev_main"
    assert row["source_candidate_stratum"] == (
        "external_submission_olean_harvest:high_signal_failed_attempts"
    )
    assert row["source_result_path"] == "artifacts/runs/fixture.result.json"
    assert row["source_candidate_pool"] == str(pool)


def _write_equations(tmp_path: Path, equations: dict[int, str]) -> Path:
    path = tmp_path / "equations.txt"
    lines = [
        f"def Equation{equation_id} (G: Type*) [Magma G] := ∀ x y z : G, {body}"
        for equation_id, body in equations.items()
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_submission_artifact(artifacts: Path, name: str, *, compiled: bool) -> None:
    artifact_dir = artifacts / name
    artifact_dir.mkdir(parents=True)
    (artifact_dir / "Submission.lean").write_text(
        """import JudgeProblem

def submission : Goal := by
  intro G _ h
  intro x
  exact x
""",
        encoding="utf-8",
    )
    if compiled:
        (artifact_dir / "Submission.olean").write_bytes(b"compiled fixture")
