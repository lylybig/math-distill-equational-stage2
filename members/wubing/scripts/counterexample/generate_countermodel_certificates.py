from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))
    sys.path.insert(0, str(repo_root))

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.lean_certificates import finite_magma_counterexample_certificate
from math_distill_stage2.public_eval import default_run_id, input_file_entry, utc_timestamp, write_json


def lean_identifier(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", value)
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"cert_{cleaned}"
    return cleaned


def certificate_filename(row: dict) -> str:
    return f"{row['id']}_eq{int(row['eq1_id'])}_not_eq{int(row['eq2_id'])}.lean"


def create_countermodel_certificate_run(
    countermodels_path: Path,
    output_root: Path,
    run_id: str | None = None,
    created_at_utc: str | None = None,
    max_certificates: int | None = None,
) -> dict:
    run_id = run_id or default_run_id("countermodel-certificates")
    created_at_utc = created_at_utc or utc_timestamp()
    run_dir = output_root / run_id
    if run_dir.exists():
        raise FileExistsError(f"run directory already exists: {run_dir}")

    rows = read_jsonl(countermodels_path)
    if max_certificates is not None:
        rows = rows[:max_certificates]

    certificates_dir = run_dir / "certificates"
    records: list[dict] = []
    batch_parts = ["import Mathlib.Tactic", "import equational_theories.Equations.All", ""]
    for row in rows:
        theorem_name = f"stage2_negative_cert_{lean_identifier(str(row['id']))}"
        code = finite_magma_counterexample_certificate(
            lhs_id=int(row["eq1_id"]),
            rhs_id=int(row["eq2_id"]),
            table=row["table"],
            theorem_name=theorem_name,
        )
        path = certificates_dir / certificate_filename(row)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(code, encoding="utf-8")
        batch_parts.append(strip_imports(code).strip())
        batch_parts.append("")
        records.append(
            {
                "id": row["id"],
                "subset": row.get("subset"),
                "eq1_id": int(row["eq1_id"]),
                "eq2_id": int(row["eq2_id"]),
                "order": int(row["order"]),
                "theorem_name": theorem_name,
                "path": str(path.relative_to(run_dir)),
            }
        )

    manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "created_at_utc": created_at_utc,
        "kind": "countermodel_certificates",
        "backend": "lean_fin_table_by_decide",
        "parameters": {
            "max_certificates": max_certificates,
        },
        "inputs": {
            "countermodels": input_file_entry(countermodels_path),
        },
        "artifacts": {
            "metrics": "metrics.json",
            "certificates": "certificates/",
            "batch": "batch.lean",
            "certificate_index": "certificate_index.jsonl",
        },
    }
    metrics = {
        "certificates": len(records),
        "unique_orders": sorted({record["order"] for record in records}),
    }

    run_dir.mkdir(parents=True, exist_ok=True)
    write_json(run_dir / "manifest.json", manifest)
    write_json(run_dir / "metrics.json", metrics)
    write_jsonl(run_dir / "certificate_index.jsonl", records)
    (run_dir / "batch.lean").write_text("\n".join(batch_parts), encoding="utf-8")

    return {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "metrics": metrics,
    }


def strip_imports(code: str) -> str:
    return "\n".join(line for line in code.splitlines() if not line.startswith("import "))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--countermodels",
        type=Path,
        required=True,
        help="countermodels.jsonl from scripts/counterexample/search_countermodels.py.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("artifacts/runs"),
    )
    parser.add_argument("--run-id")
    parser.add_argument("--created-at-utc")
    parser.add_argument("--max-certificates", type=int)
    args = parser.parse_args()

    result = create_countermodel_certificate_run(
        countermodels_path=args.countermodels,
        output_root=args.output_root,
        run_id=args.run_id,
        created_at_utc=args.created_at_utc,
        max_certificates=args.max_certificates,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
