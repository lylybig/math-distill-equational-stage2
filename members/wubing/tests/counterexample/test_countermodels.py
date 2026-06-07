import json
import subprocess
import sys
from pathlib import Path

from math_distill_stage2.counterexample import (
    FiniteMagma,
    create_countermodel_search_run,
    find_countermodel,
    latest_public_eval_uncovered_negatives,
)
from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.equations import parse_equation


def test_finite_magma_checks_equation_for_all_assignments():
    left_projection = FiniteMagma(order=2, table=((0, 0), (1, 1)))

    assert left_projection.satisfies(parse_equation("x = x * y"))
    assert not left_projection.satisfies(parse_equation("x = y * x"))


def test_find_countermodel_discovers_size_two_left_projection():
    result = find_countermodel(
        lhs_equation=parse_equation("x = x * y"),
        rhs_equation=parse_equation("x = y * x"),
        max_order=2,
    )

    assert result is not None
    assert result.order == 2
    assert result.table == ((0, 0), (1, 1))


def test_create_countermodel_search_run_writes_found_and_unsolved_rows(tmp_path: Path):
    problem_index = tmp_path / "public_problem_index.jsonl"
    uncovered = tmp_path / "uncovered_negatives.jsonl"
    output_root = tmp_path / "runs"

    write_jsonl(
        problem_index,
        [
            {
                "id": "p-found",
                "subset": "normal",
                "eq1_id": 10,
                "eq2_id": 11,
                "equation1": "x = x * y",
                "equation2": "x = y * x",
                "answer": False,
            },
            {
                "id": "p-unsolved",
                "subset": "normal",
                "eq1_id": 12,
                "eq2_id": 13,
                "equation1": "x = x",
                "equation2": "x = x",
                "answer": False,
            },
        ],
    )
    write_jsonl(
        uncovered,
        [
            {
                "id": "p-found",
                "subset": "normal",
                "eq1_id": 10,
                "eq2_id": 11,
                "answer": False,
                "coverage_status": "missing_finite_refutation",
            },
            {
                "id": "p-unsolved",
                "subset": "normal",
                "eq1_id": 12,
                "eq2_id": 13,
                "answer": False,
                "coverage_status": "missing_finite_refutation",
            },
        ],
    )

    result = create_countermodel_search_run(
        problem_index_path=problem_index,
        uncovered_negatives_path=uncovered,
        output_root=output_root,
        max_order=2,
        run_id="2026-04-29-000000-countermodel-search-test",
        created_at_utc="2026-04-29T00:00:00Z",
    )

    run_dir = output_root / "2026-04-29-000000-countermodel-search-test"
    assert result["run_dir"] == str(run_dir)
    assert (run_dir / "manifest.json").exists()
    assert (run_dir / "metrics.json").exists()
    assert (run_dir / "countermodels.jsonl").exists()
    assert (run_dir / "unsolved.jsonl").exists()

    metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    countermodels = read_jsonl(run_dir / "countermodels.jsonl")
    unsolved = read_jsonl(run_dir / "unsolved.jsonl")

    assert metrics == {
        "found": 1,
        "max_order": 2,
        "searched": 2,
        "unsolved": 1,
    }
    assert countermodels == [
        {
            "eq1_id": 10,
            "eq2_id": 11,
            "id": "p-found",
            "order": 2,
            "subset": "normal",
            "table": [[0, 0], [1, 1]],
        }
    ]
    assert unsolved == [
        {
            "eq1_id": 12,
            "eq2_id": 13,
            "id": "p-unsolved",
            "reason": "not_found_up_to_order",
            "subset": "normal",
        }
    ]


def test_latest_public_eval_uncovered_negatives_uses_newest_public_eval_run(tmp_path: Path):
    older = tmp_path / "2026-04-29-000000-public-eval"
    newer = tmp_path / "2026-04-29-000001-public-eval"
    other = tmp_path / "2026-04-29-000002-countermodel-search"
    for run_dir, kind in ((older, "public_eval"), (newer, "public_eval"), (other, "countermodel_search")):
        run_dir.mkdir(parents=True)
        (run_dir / "manifest.json").write_text(json.dumps({"kind": kind}), encoding="utf-8")
        (run_dir / "uncovered_negatives.jsonl").write_text("", encoding="utf-8")

    assert latest_public_eval_uncovered_negatives(tmp_path) == newer / "uncovered_negatives.jsonl"


def test_search_countermodels_script_help_runs_when_invoked_by_path():
    root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [sys.executable, "scripts/counterexample/search_countermodels.py", "--help"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
