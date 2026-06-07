import json
import subprocess
import sys
from pathlib import Path

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.public_eval import create_public_eval_run


def test_create_public_eval_run_writes_reproducible_artifacts(tmp_path: Path):
    problems = tmp_path / "public_problem_index.jsonl"
    implications = tmp_path / "etp_implications.jsonl"
    facts = tmp_path / "etp_facts.jsonl"
    output_root = tmp_path / "runs"

    write_jsonl(
        problems,
        [
            {
                "id": "normal_0001",
                "subset": "normal",
                "eq1_id": 2,
                "eq2_id": 8,
                "equation1": "x = x * x",
                "equation2": "x = x * (x * x)",
                "answer": True,
            },
            {
                "id": "normal_0002",
                "subset": "normal",
                "eq1_id": 23,
                "eq2_id": 39,
                "equation1": "x = y * x",
                "equation2": "x = x * y",
                "answer": False,
            },
            {
                "id": "hard3_0001",
                "subset": "hard3",
                "eq1_id": 40,
                "eq2_id": 3,
                "equation1": "x = x * y",
                "equation2": "x = y * x",
                "answer": False,
            },
        ],
    )
    write_jsonl(
        implications,
        [
            {"lhs_id": 2, "rhs_id": 3, "name": "Equation2_implies_Equation3"},
            {"lhs_id": 3, "rhs_id": 8, "name": "Equation3_implies_Equation8"},
        ],
    )
    write_jsonl(
        facts,
        [
            {
                "satisfied_ids": [23],
                "refuted_ids": [39],
                "finite": True,
                "name": "Equation23_not_implies_Equation39",
            }
        ],
    )

    result = create_public_eval_run(
        problem_index_path=problems,
        implications_path=implications,
        facts_path=facts,
        output_root=output_root,
        run_id="2026-04-29-000000-public-eval-test",
        created_at_utc="2026-04-29T00:00:00Z",
    )

    run_dir = output_root / "2026-04-29-000000-public-eval-test"
    assert result["run_dir"] == str(run_dir)
    assert (run_dir / "manifest.json").exists()
    assert (run_dir / "metrics.json").exists()
    assert (run_dir / "errors.jsonl").exists()
    assert (run_dir / "uncovered_negatives.jsonl").exists()

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    errors = read_jsonl(run_dir / "errors.jsonl")
    uncovered_negatives = read_jsonl(run_dir / "uncovered_negatives.jsonl")

    assert manifest["run_id"] == "2026-04-29-000000-public-eval-test"
    assert manifest["schema_version"] == 1
    assert metrics["total_rows"] == 3
    assert metrics["positive_path_covered"] == 1
    assert metrics["negative_finite_fact_covered"] == 1
    assert metrics["uncovered_positive_count"] == 0
    assert metrics["uncovered_negative_count"] == 1
    assert errors == [
        {
            "answer": False,
            "coverage_status": "missing_finite_refutation",
            "eq1_id": 40,
            "eq2_id": 3,
            "id": "hard3_0001",
            "subset": "hard3",
        }
    ]
    assert uncovered_negatives == errors


def test_create_public_eval_run_counts_countermodel_bank_coverage(tmp_path: Path):
    problems = tmp_path / "public_problem_index.jsonl"
    implications = tmp_path / "etp_implications.jsonl"
    facts = tmp_path / "etp_facts.jsonl"
    countermodels = tmp_path / "countermodels.jsonl"
    output_root = tmp_path / "runs"

    write_jsonl(
        problems,
        [
            {
                "id": "p-positive",
                "subset": "normal",
                "eq1_id": 2,
                "eq2_id": 8,
                "equation1": "x = x",
                "equation2": "x = x",
                "answer": True,
            },
            {
                "id": "p-etp",
                "subset": "normal",
                "eq1_id": 23,
                "eq2_id": 39,
                "equation1": "x = y * x",
                "equation2": "x = x * y",
                "answer": False,
            },
            {
                "id": "p-search",
                "subset": "hard3",
                "eq1_id": 40,
                "eq2_id": 3,
                "equation1": "x = x * y",
                "equation2": "x = y * x",
                "answer": False,
            },
        ],
    )
    write_jsonl(
        implications,
        [
            {"lhs_id": 2, "rhs_id": 8, "name": "Equation2_implies_Equation8"},
        ],
    )
    write_jsonl(
        facts,
        [
            {
                "satisfied_ids": [23],
                "refuted_ids": [39],
                "finite": True,
                "name": "Equation23_not_implies_Equation39",
            }
        ],
    )
    write_jsonl(
        countermodels,
        [
            {
                "id": "p-search",
                "subset": "hard3",
                "eq1_id": 40,
                "eq2_id": 3,
                "order": 2,
                "table": [[0, 0], [1, 1]],
            }
        ],
    )

    result = create_public_eval_run(
        problem_index_path=problems,
        implications_path=implications,
        facts_path=facts,
        output_root=output_root,
        countermodels_path=countermodels,
        run_id="2026-04-29-000001-public-eval-with-countermodels-test",
        created_at_utc="2026-04-29T00:00:01Z",
    )

    run_dir = Path(result["run_dir"])
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    errors = read_jsonl(run_dir / "errors.jsonl")
    uncovered_negatives = read_jsonl(run_dir / "uncovered_negatives.jsonl")

    assert manifest["backend"] == "etp_entries+countermodels"
    assert manifest["inputs"]["countermodels"]["path"] == str(countermodels)
    assert metrics["negative_total"] == 2
    assert metrics["negative_finite_fact_covered"] == 1
    assert metrics["negative_countermodel_covered"] == 1
    assert metrics["negative_total_covered"] == 2
    assert metrics["uncovered_negative_count"] == 0
    assert metrics["subsets"]["hard3"]["negative_countermodel_covered"] == 1
    assert errors == []
    assert uncovered_negatives == []


def test_run_public_eval_script_help_runs_when_invoked_by_path():
    root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [sys.executable, "scripts/public_eval/run_public_eval.py", "--help"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
