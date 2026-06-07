import json
import sys
from pathlib import Path

from math_distill_stage2.solver_probe import (
    build_problem_from_row,
    probe_candidate_rows,
    probe_solver_first_message,
    summarize_solver_probe_rows,
)


def test_build_problem_from_row_uses_equation_ids_and_expected_answer():
    problem = build_problem_from_row(
        {"eq1_id": 2, "eq2_id": 1, "pair_index": 1},
        equations=["x = x", "x = y"],
        expected_verdict="false",
    )

    assert problem == {
        "id": "2_1",
        "eq1_id": 2,
        "eq2_id": 1,
        "equation1": "x = y",
        "equation2": "x = x",
        "answer": False,
    }


def test_build_problem_from_row_uses_model_representative_pair():
    problem = build_problem_from_row(
        {
            "label": "m1",
            "representative_pairs": {
                "new_order4_source_to_order5_target": [1, 3],
                "new_order5_source_to_order5_target": [2, 3],
                "overlap_existing": [1, 2],
            },
        },
        equations=["x = x", "x = y", "x = x * x"],
        expected_verdict="false",
        representative_pair_key="new_order4_source_to_order5_target",
    )

    assert problem == {
        "id": "m1:new_order4_source_to_order5_target:1_3",
        "eq1_id": 1,
        "eq2_id": 3,
        "equation1": "x = x",
        "equation2": "x = x * x",
        "answer": False,
    }


def test_probe_solver_first_message_classifies_expected_verdict(tmp_path: Path):
    solver_path = tmp_path / "dummy_solver.py"
    solver_path.write_text(
        "\n".join(
            [
                "import json, sys",
                "json.loads(sys.stdin.readline())",
                "print(json.dumps({'call': 'judge', 'verdict': 'false', 'code': 'x'}), flush=True)",
                "json.loads(sys.stdin.readline())",
            ]
        ),
        encoding="utf-8",
    )

    probe = probe_solver_first_message(
        {"id": "p", "equation1": "x = x", "equation2": "x = y"},
        solver_path=solver_path,
        expected_verdict="false",
        timeout_seconds=1.0,
        python_executable=sys.executable,
    )

    assert probe.status == "message"
    assert probe.call == "judge"
    assert probe.verdict == "false"
    assert probe.matches_expected_verdict is True
    assert probe.returncode == 0


def test_probe_solver_first_message_marks_timeout(tmp_path: Path):
    solver_path = tmp_path / "slow_solver.py"
    solver_path.write_text(
        "import time\n"
        "time.sleep(10)\n",
        encoding="utf-8",
    )

    probe = probe_solver_first_message(
        {"id": "p", "equation1": "x = x", "equation2": "x = y"},
        solver_path=solver_path,
        expected_verdict="false",
        timeout_seconds=0.1,
        python_executable=sys.executable,
    )

    assert probe.status == "timeout"
    assert probe.matches_expected_verdict is False


def test_probe_candidate_rows_summary_counts_expected_fast_hits(tmp_path: Path):
    solver_path = tmp_path / "dummy_solver.py"
    solver_path.write_text(
        "\n".join(
            [
                "import json, sys",
                "json.loads(sys.stdin.readline())",
                "print(json.dumps({'call': 'judge', 'verdict': 'false', 'code': 'x'}), flush=True)",
                "json.loads(sys.stdin.readline())",
            ]
        ),
        encoding="utf-8",
    )

    rows = probe_candidate_rows(
        [{"eq1_id": 1, "eq2_id": 2}, {"eq1_id": 2, "eq2_id": 1}],
        solver_path=solver_path,
        equations=["x = x", "x = y"],
        expected_verdict="false",
        timeout_seconds=1.0,
        python_executable=sys.executable,
        max_workers=2,
    )
    summary = summarize_solver_probe_rows(rows, expected_verdict="false")

    assert rows[0]["solver_probe"]["matches_expected_verdict"] is True
    assert rows[1]["solver_probe"]["matches_expected_verdict"] is True
    assert summary["total_count"] == 2
    assert summary["expected_fast_count"] == 2
    assert summary["solver_uncovered_count"] == 0
