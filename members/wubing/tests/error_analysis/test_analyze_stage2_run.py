import json
import subprocess
import sys
from pathlib import Path

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.error_analysis.stage2_run import analyze_stage2_run, classify_record


def _record(problem_id: str, **overrides) -> dict:
    base = {
        "problem_id": problem_id,
        "request_status": "ok",
        "parsed_status": "parsed",
        "verdict_check_status": "passed",
        "lean4_status": "passed",
        "expected_verdict": "false",
        "actual_verdict": "false",
        "reasoning_correct": True,
        "judge_call": {"verdict": "false", "code": "theorem certificate : False := by\n  contradiction"},
        "lean4_result": {"stdout": "", "stderr": "", "elapsed_seconds": 0.1},
        "latency_seconds": 1.0,
    }
    base.update(overrides)
    return base


def test_classify_record_prioritizes_pipeline_stage_failures():
    assert classify_record(_record("request", request_status="error", parsed_status="request_error"))[
        "category"
    ] == "request_failure"
    assert classify_record(_record("parse", parsed_status="malformed"))["category"] == "parse_failure"
    assert classify_record(_record("verdict", verdict_check_status="failed"))["category"] == "verdict_failure"

    forbidden = classify_record(
        _record(
            "forbidden",
            lean4_status="failed",
            reasoning_correct=False,
            judge_call={"verdict": "false", "code": "import Mathlib\n\ntheorem certificate : True := by\n  trivial"},
            lean4_result={"stdout": "unknown module prefix 'Mathlib'", "stderr": ""},
        )
    )
    assert forbidden["category"] == "lean4_failure"
    assert forbidden["subcategory"] == "lean_forbidden_pattern"
    assert "import" in forbidden["forbidden_patterns"]
    assert "Mathlib" in forbidden["forbidden_patterns"]

    semantic = classify_record(
        _record(
            "semantic",
            lean4_status="failed",
            reasoning_correct=False,
            lean4_result={"stdout": "Tactic `rfl` failed", "stderr": ""},
        )
    )
    assert semantic["subcategory"] == "lean_semantic_failure"

    arity = classify_record(
        _record(
            "arity",
            lean4_status="failed",
            reasoning_correct=False,
            lean4_result={
                "stdout": "Function expected at\n  op y (op y x)\nbut this term has type\n  α",
                "stderr": "",
            },
        )
    )
    assert arity["subcategory"] == "lean_arity_failure"

    pipeline = classify_record(
        _record(
            "pipeline",
            lean4_status="failed",
            reasoning_correct=False,
            judge_call={"verdict": "false", "code": "theorem certificate : False := by\n  exact False.elim ((fun t => t) |> id)"},
            lean4_result={
                "stdout": "Application type mismatch: The argument\n  x = op x y\nhas type\n  Prop\nbut is expected to have type\n  α",
                "stderr": "",
            },
        )
    )
    assert pipeline["subcategory"] == "lean_bad_translation_failure"

    simp_loop = classify_record(
        _record(
            "simp_loop",
            lean4_status="failed",
            reasoning_correct=False,
            lean4_result={"stdout": "maximum recursion depth has been reached", "stderr": ""},
        )
    )
    assert simp_loop["subcategory"] == "lean_simp_loop_failure"

    no_goals = classify_record(
        _record(
            "no_goals",
            lean4_status="failed",
            reasoning_correct=False,
            lean4_result={"stdout": "No goals to be solved", "stderr": ""},
        )
    )
    assert no_goals["subcategory"] == "lean_tactic_state_failure"

    name_error = classify_record(
        _record(
            "name_error",
            lean4_status="failed",
            reasoning_correct=False,
            lean4_result={"stdout": "`Bool` has already been declared\nNo goals to be solved", "stderr": ""},
        )
    )
    assert name_error["subcategory"] == "lean_name_error"


def test_analyze_stage2_run_writes_taxonomy_errors_and_markdown(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    write_jsonl(
        run_dir / "per_run.jsonl",
        [
            _record("ok"),
            _record("request", request_status="error", parsed_status="request_error", reasoning_correct=False),
            _record("parse", parsed_status="malformed", reasoning_correct=False),
            _record("verdict", verdict_check_status="failed", reasoning_correct=False),
            _record(
                "lean",
                lean4_status="failed",
                reasoning_correct=False,
                lean4_result={"stdout": "failed to synthesize instance HMul", "stderr": ""},
            ),
        ],
    )
    (run_dir / "summary.json").write_text(
        json.dumps(
            {
                "leaderboard_metrics": {"accuracy": 0.2, "f1_score": 0.0},
                "stage_metrics": {"verdict_accuracy": 0.5, "lean4_strict_pass_rate": 0.2},
            }
        ),
        encoding="utf-8",
    )

    taxonomy = analyze_stage2_run(run_dir)

    errors = read_jsonl(run_dir / "errors.jsonl")
    taxonomy_json = json.loads((run_dir / "failure_taxonomy.json").read_text(encoding="utf-8"))
    analysis = (run_dir / "analysis.md").read_text(encoding="utf-8")
    assert taxonomy == taxonomy_json
    assert len(errors) == 4
    assert taxonomy["category_counts"] == {
        "lean4_failure": 1,
        "parse_failure": 1,
        "request_failure": 1,
        "verdict_failure": 1,
    }
    assert taxonomy["subcategory_counts"]["lean_typeclass_failure"] == 1
    assert "Leaderboard Metrics" in analysis
    assert "Failure Taxonomy" in analysis


def test_analyze_stage2_run_supports_official_runner_results(tmp_path: Path):
    run_dir = tmp_path / "official-run"
    results_dir = run_dir / "results"
    results_dir.mkdir(parents=True)
    (results_dir / "sample.json").write_text(
        json.dumps(
            [
                {
                    "id": "ok_false",
                    "solved": True,
                    "verdict": "false",
                    "elapsed_seconds": 2.0,
                    "llm_calls": 0,
                    "judge_calls": 1,
                    "log": [],
                },
                {
                    "id": "no_candidate",
                    "solved": False,
                    "verdict": None,
                    "elapsed_seconds": 0.1,
                    "llm_calls": 0,
                    "judge_calls": 0,
                    "log": [],
                },
                {
                    "id": "judge_rejected",
                    "solved": False,
                    "verdict": "true",
                    "elapsed_seconds": 1.5,
                    "llm_calls": 0,
                    "judge_calls": 1,
                    "log": [{"call": "judge", "status": "rejected"}],
                },
                {
                    "id": "llm_failed",
                    "solved": False,
                    "verdict": None,
                    "elapsed_seconds": 3.0,
                    "llm_calls": 1,
                    "judge_calls": 0,
                    "log": [{"call": "llm", "error": "endpoint failed"}],
                },
            ]
        ),
        encoding="utf-8",
    )
    (run_dir / "summary.json").write_text(
        json.dumps({"accepted": 1, "rejected": 1, "errors": 2, "metricsText": "1A / 1R / 2E"}),
        encoding="utf-8",
    )

    taxonomy = analyze_stage2_run(run_dir)

    errors = read_jsonl(run_dir / "errors.jsonl")
    assert taxonomy["input_format"] == "official_runner_results"
    assert taxonomy["success_count"] == 1
    assert taxonomy["failure_count"] == 3
    assert taxonomy["category_counts"] == {
        "judge_rejected": 1,
        "llm_failure": 1,
        "no_candidate": 1,
    }
    assert [row["problem_id"] for row in errors] == ["no_candidate", "judge_rejected", "llm_failed"]
    assert "Official Runner Metrics" in (run_dir / "analysis.md").read_text(encoding="utf-8")


def test_analyze_stage2_run_script_help_runs_when_invoked_by_path():
    root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [sys.executable, "scripts/error_analysis/analyze_stage2_run.py", "--help"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "--run-dir" in result.stdout


def test_layered_analyze_stage2_run_script_help_runs_when_invoked_by_path():
    root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [sys.executable, "scripts/error_analysis/analyze_stage2_run.py", "--help"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "--run-dir" in result.stdout
