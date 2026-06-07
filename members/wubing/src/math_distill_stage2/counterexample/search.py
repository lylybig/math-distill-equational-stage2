from __future__ import annotations

import json
from pathlib import Path

from math_distill_stage2.counterexample.finite_magma import find_countermodel
from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.equations import parse_equation
from math_distill_stage2.public_eval import default_run_id, input_file_entry, utc_timestamp, write_json


def index_problem_rows(problem_index_path: Path) -> dict[str, dict]:
    return {str(row["id"]): row for row in read_jsonl(problem_index_path)}


def latest_public_eval_uncovered_negatives(output_root: Path) -> Path:
    candidates: list[Path] = []
    if not output_root.exists():
        raise FileNotFoundError(f"run output root does not exist: {output_root}")
    for run_dir in output_root.iterdir():
        if not run_dir.is_dir():
            continue
        manifest_path = run_dir / "manifest.json"
        uncovered_path = run_dir / "uncovered_negatives.jsonl"
        if not manifest_path.exists() or not uncovered_path.exists():
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if manifest.get("kind") == "public_eval":
            candidates.append(uncovered_path)
    if not candidates:
        raise FileNotFoundError(f"no public_eval run with uncovered_negatives.jsonl under {output_root}")
    return sorted(candidates, key=lambda path: path.parent.name)[-1]


def create_countermodel_search_run(
    problem_index_path: Path,
    uncovered_negatives_path: Path,
    output_root: Path,
    max_order: int,
    max_problems: int | None = None,
    run_id: str | None = None,
    created_at_utc: str | None = None,
) -> dict:
    run_id = run_id or default_run_id("countermodel-search")
    created_at_utc = created_at_utc or utc_timestamp()
    run_dir = output_root / run_id
    if run_dir.exists():
        raise FileExistsError(f"run directory already exists: {run_dir}")

    problems_by_id = index_problem_rows(problem_index_path)
    uncovered_rows = read_jsonl(uncovered_negatives_path)
    if max_problems is not None:
        uncovered_rows = uncovered_rows[:max_problems]

    countermodels: list[dict] = []
    unsolved: list[dict] = []
    for uncovered in uncovered_rows:
        problem = problems_by_id[str(uncovered["id"])]
        magma = find_countermodel(
            lhs_equation=parse_equation(problem["equation1"]),
            rhs_equation=parse_equation(problem["equation2"]),
            max_order=max_order,
        )
        common = {
            "id": problem["id"],
            "subset": problem.get("subset"),
            "eq1_id": int(problem["eq1_id"]),
            "eq2_id": int(problem["eq2_id"]),
        }
        if magma is None:
            unsolved.append({**common, "reason": "not_found_up_to_order"})
        else:
            countermodels.append(
                {
                    **common,
                    "order": magma.order,
                    "table": magma.to_json_table(),
                }
            )

    metrics = {
        "searched": len(uncovered_rows),
        "found": len(countermodels),
        "unsolved": len(unsolved),
        "max_order": max_order,
    }
    manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "created_at_utc": created_at_utc,
        "kind": "countermodel_search",
        "backend": "finite_magma_exhaustive",
        "parameters": {
            "max_order": max_order,
            "max_problems": max_problems,
        },
        "inputs": {
            "problem_index": input_file_entry(problem_index_path),
            "uncovered_negatives": input_file_entry(uncovered_negatives_path),
        },
        "artifacts": {
            "metrics": "metrics.json",
            "countermodels": "countermodels.jsonl",
            "unsolved": "unsolved.jsonl",
        },
    }

    run_dir.mkdir(parents=True)
    write_json(run_dir / "manifest.json", manifest)
    write_json(run_dir / "metrics.json", metrics)
    write_jsonl(run_dir / "countermodels.jsonl", countermodels)
    write_jsonl(run_dir / "unsolved.jsonl", unsolved)

    return {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "metrics": metrics,
    }
