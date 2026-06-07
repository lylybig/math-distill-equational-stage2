from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.implication_graph import FactIndex, ImplicationGraph


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def default_run_id(prefix: str = "public-eval") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
    return f"{stamp}-{prefix}"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def input_file_entry(path: Path) -> dict:
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
    }


def countermodel_key(row: dict) -> tuple[str, int, int]:
    return (str(row["id"]), int(row["eq1_id"]), int(row["eq2_id"]))


def load_countermodel_keys(path: Path | None) -> set[tuple[str, int, int]]:
    if path is None:
        return set()
    return {countermodel_key(row) for row in read_jsonl(path)}


def evaluate_public_coverage(
    problems: list[dict],
    graph: ImplicationGraph,
    facts: FactIndex,
    countermodel_keys: set[tuple[str, int, int]] | None = None,
) -> tuple[dict, list[dict], list[dict]]:
    countermodel_keys = countermodel_keys or set()
    positive_total = 0
    positive_path_covered = 0
    negative_total = 0
    negative_fact_covered = 0
    negative_finite_fact_covered = 0
    negative_countermodel_covered = 0
    negative_total_covered = 0
    by_subset: dict[str, dict[str, int]] = {}
    errors: list[dict] = []
    uncovered_negatives: list[dict] = []

    for row in problems:
        subset = row.get("subset", "unknown")
        subset_summary = by_subset.setdefault(
            subset,
            {
                "rows": 0,
                "positive_total": 0,
                "positive_path_covered": 0,
                "negative_total": 0,
                "negative_fact_covered": 0,
                "negative_finite_fact_covered": 0,
                "negative_countermodel_covered": 0,
                "negative_total_covered": 0,
                "uncovered_positive_count": 0,
                "uncovered_negative_count": 0,
            },
        )
        subset_summary["rows"] += 1
        lhs_id = int(row["eq1_id"])
        rhs_id = int(row["eq2_id"])

        if row["answer"] is True:
            positive_total += 1
            subset_summary["positive_total"] += 1
            if graph.find_path(lhs_id, rhs_id) is not None:
                positive_path_covered += 1
                subset_summary["positive_path_covered"] += 1
            else:
                subset_summary["uncovered_positive_count"] += 1
                errors.append(coverage_error(row, "missing_positive_path"))
        else:
            negative_total += 1
            subset_summary["negative_total"] += 1
            has_finite_fact = False
            if facts.find_refutation(lhs_id, rhs_id, finite_only=False) is not None:
                negative_fact_covered += 1
                subset_summary["negative_fact_covered"] += 1
            if facts.find_refutation(lhs_id, rhs_id, finite_only=True) is not None:
                negative_finite_fact_covered += 1
                subset_summary["negative_finite_fact_covered"] += 1
                has_finite_fact = True
            has_countermodel = countermodel_key(row) in countermodel_keys
            if has_countermodel:
                negative_countermodel_covered += 1
                subset_summary["negative_countermodel_covered"] += 1
            if has_finite_fact or has_countermodel:
                negative_total_covered += 1
                subset_summary["negative_total_covered"] += 1
            else:
                error = coverage_error(row, "missing_finite_refutation")
                errors.append(error)
                uncovered_negatives.append(error)
                subset_summary["uncovered_negative_count"] += 1

    return (
        {
            "total_rows": len(problems),
            "positive_total": positive_total,
            "positive_path_covered": positive_path_covered,
            "negative_total": negative_total,
            "negative_fact_covered": negative_fact_covered,
            "negative_finite_fact_covered": negative_finite_fact_covered,
            "negative_countermodel_covered": negative_countermodel_covered,
            "negative_total_covered": negative_total_covered,
            "uncovered_positive_count": positive_total - positive_path_covered,
            "uncovered_negative_count": negative_total - negative_total_covered,
            "subsets": by_subset,
        },
        errors,
        uncovered_negatives,
    )


def coverage_error(row: dict, coverage_status: str) -> dict:
    return {
        "id": row.get("id"),
        "subset": row.get("subset"),
        "eq1_id": int(row["eq1_id"]),
        "eq2_id": int(row["eq2_id"]),
        "answer": row.get("answer"),
        "coverage_status": coverage_status,
    }


def create_public_eval_run(
    problem_index_path: Path,
    implications_path: Path,
    facts_path: Path,
    output_root: Path,
    countermodels_path: Path | None = None,
    run_id: str | None = None,
    created_at_utc: str | None = None,
) -> dict:
    run_id = run_id or default_run_id()
    created_at_utc = created_at_utc or utc_timestamp()
    run_dir = output_root / run_id
    if run_dir.exists():
        raise FileExistsError(f"run directory already exists: {run_dir}")

    problems = read_jsonl(problem_index_path)
    graph = ImplicationGraph.from_rows(read_jsonl(implications_path))
    facts = FactIndex.from_rows(read_jsonl(facts_path))
    countermodel_keys = load_countermodel_keys(countermodels_path)
    metrics, errors, uncovered_negatives = evaluate_public_coverage(
        problems,
        graph,
        facts,
        countermodel_keys=countermodel_keys,
    )

    inputs = {
        "problem_index": input_file_entry(problem_index_path),
        "implications": input_file_entry(implications_path),
        "facts": input_file_entry(facts_path),
    }
    if countermodels_path is not None:
        inputs["countermodels"] = input_file_entry(countermodels_path)
    manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "created_at_utc": created_at_utc,
        "kind": "public_eval",
        "backend": "etp_entries+countermodels" if countermodels_path is not None else "etp_entries",
        "inputs": inputs,
        "artifacts": {
            "metrics": "metrics.json",
            "errors": "errors.jsonl",
            "uncovered_negatives": "uncovered_negatives.jsonl",
        },
    }

    run_dir.mkdir(parents=True)
    write_json(run_dir / "manifest.json", manifest)
    write_json(run_dir / "metrics.json", metrics)
    write_jsonl(run_dir / "errors.jsonl", errors)
    write_jsonl(run_dir / "uncovered_negatives.jsonl", uncovered_negatives)

    return {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "metrics": metrics,
    }
