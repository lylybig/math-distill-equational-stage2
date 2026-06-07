from __future__ import annotations

import hashlib
import json
from pathlib import Path

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.public_eval import input_file_entry, write_json


def row_key(row: dict) -> tuple[str, int, int]:
    return (str(row["id"]), int(row["eq1_id"]), int(row["eq2_id"]))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_verification(certificate_run_dir: Path) -> dict:
    path = certificate_run_dir / "verification.json"
    if not path.exists():
        return {"result": "unknown"}
    return json.loads(path.read_text(encoding="utf-8"))


def build_verified_counterexample_index(
    problem_index_path: Path,
    countermodels_path: Path,
    certificate_run_dir: Path,
    output_path: Path,
    summary_output_path: Path | None = None,
) -> dict:
    problems = {row_key(row): row for row in read_jsonl(problem_index_path)}
    countermodels = {row_key(row): row for row in read_jsonl(countermodels_path)}
    certificate_rows = read_jsonl(certificate_run_dir / "certificate_index.jsonl")
    verification = load_verification(certificate_run_dir)
    verification_result = verification.get("result", "unknown")

    linked_rows: list[dict] = []
    for certificate in certificate_rows:
        key = row_key(certificate)
        problem = problems[key]
        countermodel = countermodels[key]
        certificate_path = certificate_run_dir / certificate["path"]
        linked_rows.append(
            {
                "id": problem["id"],
                "subset": problem.get("subset"),
                "eq1_id": int(problem["eq1_id"]),
                "eq2_id": int(problem["eq2_id"]),
                "equation1": problem.get("equation1"),
                "equation2": problem.get("equation2"),
                "eq1_signature": problem.get("eq1_signature"),
                "eq2_signature": problem.get("eq2_signature"),
                "answer": problem.get("answer"),
                "countermodel": {
                    "order": int(countermodel["order"]),
                    "table": countermodel["table"],
                    "source_path": str(countermodels_path),
                },
                "lean": {
                    "theorem_name": certificate["theorem_name"],
                    "certificate_path": str(certificate_path),
                    "certificate_sha256": file_sha256(certificate_path),
                    "batch_verification_result": verification_result,
                    "verified": verification_result == "passed",
                },
            }
        )

    write_jsonl(output_path, linked_rows)
    summary = {
        "schema_version": 1,
        "verified_counterexamples": len(linked_rows),
        "verification_result": verification_result,
        "inputs": {
            "problem_index": input_file_entry(problem_index_path),
            "countermodels": input_file_entry(countermodels_path),
            "certificate_index": input_file_entry(certificate_run_dir / "certificate_index.jsonl"),
            "verification": input_file_entry(certificate_run_dir / "verification.json")
            if (certificate_run_dir / "verification.json").exists()
            else None,
        },
        "output": str(output_path),
    }
    write_json(summary_output_path or output_path.with_suffix(".summary.json"), summary)
    return summary
