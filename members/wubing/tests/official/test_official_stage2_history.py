import json
import subprocess
import sys
from pathlib import Path

from math_distill_stage2.official_stage2_history import (
    DEFAULT_OUTPUT_ROOT,
    PROBLEM_SUITES,
    OfficialRunnerSummaryInput,
    default_run_id,
    render_history_markdown,
    resolve_problem_sets,
    run_official_solo_history_parallel,
    summarize_official_runner_results,
    write_history_artifacts,
)


def test_summarizes_official_runner_results_into_stage2_history_shape(tmp_path: Path):
    results = [
        {"id": "p1", "solved": True, "verdict": "false", "elapsed_seconds": 2.5, "llm_calls": 0, "judge_calls": 1},
        {"id": "p2", "solved": False, "verdict": None, "elapsed_seconds": 1.0, "llm_calls": 1, "judge_calls": 1},
        {"id": "p3", "solved": False, "verdict": None, "elapsed_seconds": 0.5, "llm_calls": 0, "judge_calls": 0},
    ]

    summary = summarize_official_runner_results(
        OfficialRunnerSummaryInput(
            run_id="official-solo-test",
            solver_name="solver.py",
            problem_set="sample_3",
            result_path=tmp_path / "sample_3.json",
            created_at="2026-05-06T12:00:00+08:00",
            results=results,
        )
    )

    assert summary["status"] == "done"
    assert summary["accepted"] == 1
    assert summary["rejected"] == 1
    assert summary["errors"] == 1
    assert summary["totalProblems"] == 3
    assert summary["llmTotalCalls"] == 1
    assert summary["judgeTotalCalls"] == 2
    assert summary["acceptedVerdicts"] == {"false": 1}
    assert summary["progressText"] == "3/3"
    assert summary["metricsText"] == "1A / 1R / 1E / 1 calls"


def test_writes_history_artifacts(tmp_path: Path):
    result_path = tmp_path / "results" / "sample_1.json"
    result_path.parent.mkdir()
    result_path.write_text(
        json.dumps([{"id": "p1", "solved": True, "verdict": "true", "elapsed_seconds": 1.25, "llm_calls": 0, "judge_calls": 1}]),
        encoding="utf-8",
    )
    summary = summarize_official_runner_results(
        OfficialRunnerSummaryInput(
            run_id="official-solo-smoke",
            solver_name="solo_official",
            problem_set="sample_1",
            result_path=result_path,
            created_at="2026-05-06T12:00:00+08:00",
            results=json.loads(result_path.read_text(encoding="utf-8")),
        )
    )

    write_history_artifacts(tmp_path, [summary])

    written_summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    history = json.loads((tmp_path / "history.json").read_text(encoding="utf-8"))
    markdown = (tmp_path / "history.md").read_text(encoding="utf-8")

    assert written_summary["accepted"] == 1
    assert history == [summary]
    assert "| done | solo_official | official-solo-smoke | 1/1 | 1A / 0R / 0E |" in markdown


def test_renders_empty_history_markdown():
    assert "No runs" in render_history_markdown([])


def test_official_solo_history_default_suite_is_sample200_only():
    assert "sample200" in PROBLEM_SUITES
    assert "sample20" not in PROBLEM_SUITES

    paths = resolve_problem_sets(
        official_repo=Path("/repo"),
        suite="sample200",
        explicit_problem_sets=[],
    )

    assert paths == [Path("/repo/examples/problems/sample_200.json")]


def test_official_solo_history_defaults_write_under_dated_runs_root():
    assert DEFAULT_OUTPUT_ROOT.parent.name == "runs"
    assert DEFAULT_OUTPUT_ROOT.name.count("-") == 2
    assert not default_run_id("sample200").startswith(DEFAULT_OUTPUT_ROOT.name)


def test_official_solo_history_script_can_run_as_file():
    proc = subprocess.run(
        [sys.executable, "scripts/evaluator/run_official_solo_history.py", "--help"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0
    assert "official Stage 2 Solo runner" in proc.stdout


def test_parallel_history_runs_one_official_runner_shard_per_problem(
    tmp_path: Path,
    monkeypatch,
):
    official_repo = tmp_path / "official"
    official_repo.mkdir()
    submission = tmp_path / "submission"
    submission.mkdir()
    (submission / "solver.py").write_text("# solver\n", encoding="utf-8")
    problem_set = tmp_path / "sample_2.json"
    problems = [
        {
            "id": "p1",
            "eq1_id": 1,
            "eq2_id": 1,
            "equation1": "x = x",
            "equation2": "x = x",
        },
        {
            "id": "p2",
            "eq1_id": 1,
            "eq2_id": 2,
            "equation1": "x = x",
            "equation2": "x = y",
        },
    ]
    problem_set.write_text(json.dumps(problems), encoding="utf-8")
    run_dir = tmp_path / "run"
    calls: list[tuple[str, str]] = []

    def fake_run_and_tee(command: list[str], *, cwd: Path, log_path: Path) -> int:
        assert cwd == official_repo
        shard_path = Path(command[command.index("--problems") + 1])
        output_path = Path(command[command.index("--output") + 1])
        shard_problem = json.loads(shard_path.read_text(encoding="utf-8"))[0]
        calls.append((shard_problem["id"], log_path.name))
        result = {
            "id": shard_problem["id"],
            "eq1_id": shard_problem["eq1_id"],
            "eq2_id": shard_problem["eq2_id"],
            "elapsed_seconds": 0.25,
            "solved": shard_problem["id"] == "p1",
            "verdict": "true" if shard_problem["id"] == "p1" else None,
            "code": "import JudgeProblem",
            "llm_calls": 0,
            "judge_calls": 1,
            "log": [],
        }
        output_path.write_text(json.dumps([result]), encoding="utf-8")
        log_path.write_text(f"ran {shard_problem['id']}\n", encoding="utf-8")
        return 0

    monkeypatch.setattr(
        "math_distill_stage2.official_stage2_history._run_and_log",
        fake_run_and_tee,
    )

    rows = run_official_solo_history_parallel(
        submission_dir=submission,
        problem_sets=[problem_set],
        run_dir=run_dir,
        official_repo=official_repo,
        max_workers=2,
    )

    combined_results = json.loads((run_dir / "results" / "sample_2.json").read_text(encoding="utf-8"))
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    aggregate_log = (run_dir / "logs" / "sample_2.log").read_text(encoding="utf-8")

    assert [row["id"] for row in combined_results] == ["p1", "p2"]
    assert rows[0]["parallel"] is True
    assert rows[0]["maxWorkers"] == 2
    assert summary["accepted"] == 1
    assert summary["rejected"] == 1
    assert summary["errors"] == 0
    assert "parallel_logs/sample_2/000001_p1.log" in aggregate_log
    assert "parallel_logs/sample_2/000002_p2.log" in aggregate_log
    assert sorted(problem_id for problem_id, _ in calls) == ["p1", "p2"]


def test_parallel_history_can_chunk_multiple_problems_per_runner_shard(
    tmp_path: Path,
    monkeypatch,
):
    official_repo = tmp_path / "official"
    official_repo.mkdir()
    submission = tmp_path / "submission"
    submission.mkdir()
    (submission / "solver.py").write_text("# solver\n", encoding="utf-8")
    problem_set = tmp_path / "sample_5.json"
    problems = [
        {
            "id": f"p{i}",
            "eq1_id": i,
            "eq2_id": i + 10,
            "equation1": "x = x",
            "equation2": "x = x",
        }
        for i in range(1, 6)
    ]
    problem_set.write_text(json.dumps(problems), encoding="utf-8")
    run_dir = tmp_path / "run"
    shard_problem_ids: list[list[str]] = []

    def fake_run_and_tee(command: list[str], *, cwd: Path, log_path: Path) -> int:
        assert cwd == official_repo
        shard_path = Path(command[command.index("--problems") + 1])
        output_path = Path(command[command.index("--output") + 1])
        shard_problems = json.loads(shard_path.read_text(encoding="utf-8"))
        shard_problem_ids.append([problem["id"] for problem in shard_problems])
        results = [
            {
                "id": problem["id"],
                "eq1_id": problem["eq1_id"],
                "eq2_id": problem["eq2_id"],
                "elapsed_seconds": 0.25,
                "solved": True,
                "verdict": "true",
                "code": "import JudgeProblem",
                "llm_calls": 0,
                "judge_calls": 1,
                "log": [],
            }
            for problem in shard_problems
        ]
        output_path.write_text(json.dumps(results), encoding="utf-8")
        log_path.write_text(f"ran {','.join(problem['id'] for problem in shard_problems)}\n", encoding="utf-8")
        return 0

    monkeypatch.setattr(
        "math_distill_stage2.official_stage2_history._run_and_log",
        fake_run_and_tee,
    )

    rows = run_official_solo_history_parallel(
        submission_dir=submission,
        problem_sets=[problem_set],
        run_dir=run_dir,
        official_repo=official_repo,
        max_workers=2,
        problems_per_shard=2,
    )

    combined_results = json.loads((run_dir / "results" / "sample_5.json").read_text(encoding="utf-8"))
    aggregate_log = (run_dir / "logs" / "sample_5.log").read_text(encoding="utf-8")

    assert sorted(shard_problem_ids) == [["p1", "p2"], ["p3", "p4"], ["p5"]]
    assert [row["id"] for row in combined_results] == ["p1", "p2", "p3", "p4", "p5"]
    assert rows[0]["parallel"] is True
    assert rows[0]["maxWorkers"] == 2
    assert rows[0]["problemsPerShard"] == 2
    assert "parallel_logs/sample_5/000001-000002_p1.log" in aggregate_log
    assert "parallel_logs/sample_5/000005_p5.log" in aggregate_log


def test_parallel_history_reuses_exact_result_cache_for_same_solver_and_problem(
    tmp_path: Path,
    monkeypatch,
):
    official_repo = tmp_path / "official"
    official_repo.mkdir()
    submission = tmp_path / "submission"
    submission.mkdir()
    (submission / "solver.py").write_text("# solver\n", encoding="utf-8")
    problem_set = tmp_path / "sample_2.json"
    problems = [
        {
            "id": "p1",
            "eq1_id": 1,
            "eq2_id": 1,
            "equation1": "x = x",
            "equation2": "x = x",
        },
        {
            "id": "p2",
            "eq1_id": 1,
            "eq2_id": 2,
            "equation1": "x = x",
            "equation2": "x = y",
        },
    ]
    problem_set.write_text(json.dumps(problems), encoding="utf-8")
    cache_dir = tmp_path / "cache"
    calls: list[str] = []

    def fake_run_and_tee(command: list[str], *, cwd: Path, log_path: Path) -> int:
        assert cwd == official_repo
        shard_path = Path(command[command.index("--problems") + 1])
        output_path = Path(command[command.index("--output") + 1])
        shard_problems = json.loads(shard_path.read_text(encoding="utf-8"))
        calls.extend(problem["id"] for problem in shard_problems)
        results = [
            {
                "id": problem["id"],
                "eq1_id": problem["eq1_id"],
                "eq2_id": problem["eq2_id"],
                "elapsed_seconds": 0.25,
                "solved": problem["id"] == "p1",
                "verdict": "true" if problem["id"] == "p1" else None,
                "code": "import JudgeProblem",
                "llm_calls": 0,
                "judge_calls": 1,
                "log": [],
            }
            for problem in shard_problems
        ]
        output_path.write_text(json.dumps(results), encoding="utf-8")
        log_path.write_text(f"ran {','.join(problem['id'] for problem in shard_problems)}\n", encoding="utf-8")
        return 0

    monkeypatch.setattr(
        "math_distill_stage2.official_stage2_history._run_and_log",
        fake_run_and_tee,
    )

    run_official_solo_history_parallel(
        submission_dir=submission,
        problem_sets=[problem_set],
        run_dir=tmp_path / "run1",
        official_repo=official_repo,
        max_workers=2,
        cache_dir=cache_dir,
    )
    calls.clear()

    rows = run_official_solo_history_parallel(
        submission_dir=submission,
        problem_sets=[problem_set],
        run_dir=tmp_path / "run2",
        official_repo=official_repo,
        max_workers=2,
        cache_dir=cache_dir,
    )

    combined_results = json.loads((tmp_path / "run2" / "results" / "sample_2.json").read_text(encoding="utf-8"))
    aggregate_log = (tmp_path / "run2" / "logs" / "sample_2.log").read_text(encoding="utf-8")

    assert calls == []
    assert [row["id"] for row in combined_results] == ["p1", "p2"]
    assert [row["cache_hit"] for row in combined_results] == [True, True]
    assert rows[0]["cache"]["exactResultHits"] == 2
    assert rows[0]["cache"]["exactResultMisses"] == 0
    assert "exact-result-cache" in aggregate_log


def test_parallel_history_script_can_run_as_file():
    proc = subprocess.run(
        [sys.executable, "scripts/evaluator/run_official_solo_history_parallel.py", "--help"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0
    assert "--max-workers" in proc.stdout
