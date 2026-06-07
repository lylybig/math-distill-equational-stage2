from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.lean_executor import DockerLeanExecutor, LeanTask
from math_distill_stage2.lean_certificates import pure_finite_magma_counterexample_certificate
from math_distill_stage2.counterexample.verified_index import file_sha256


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def problem_key(row: dict) -> str:
    return f"eq1-{int(row['eq1_id'])}-eq2-{int(row['eq2_id'])}"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")


def export_counterexample_assets(
    verified_counterexamples_path: Path,
    output_root: Path,
    run_id: str,
    created_at_utc: str | None = None,
    verify: bool = False,
    verify_workers: int = 4,
) -> dict:
    created_at_utc = created_at_utc or utc_timestamp()
    output_root.mkdir(parents=True, exist_ok=True)
    rows = read_jsonl(verified_counterexamples_path)
    index_rows: list[dict] = []
    pending_verifications: list[tuple[Path, Path]] = []

    for row in rows:
        key = problem_key(row)
        problem_dir = output_root / key
        run_dir = problem_dir / "runs" / run_id
        theorem_name = row.get("lean", {}).get("theorem_name") or f"stage2_negative_cert_{key.replace('-', '_')}"
        certificate_code = pure_finite_magma_counterexample_certificate(
            lhs_id=int(row["eq1_id"]),
            lhs_equation=row["equation1"],
            rhs_id=int(row["eq2_id"]),
            rhs_equation=row["equation2"],
            table=row["countermodel"]["table"],
            theorem_name=theorem_name,
        )

        problem_payload = {
            "problem_key": key,
            "id": row["id"],
            "subset": row.get("subset"),
            "eq1_id": int(row["eq1_id"]),
            "eq2_id": int(row["eq2_id"]),
            "equation1": row["equation1"],
            "equation2": row["equation2"],
            "eq1_signature": row.get("eq1_signature"),
            "eq2_signature": row.get("eq2_signature"),
            "answer": row.get("answer"),
        }
        countermodel_payload = {
            "order": int(row["countermodel"]["order"]),
            "carrier": list(range(int(row["countermodel"]["order"]))),
            "table": row["countermodel"]["table"],
            "source_path": row["countermodel"].get("source_path"),
        }
        metadata_payload = {
            "created_at_utc": created_at_utc,
            "run_id": run_id,
            "source_verified_counterexamples": str(verified_counterexamples_path),
            "generator": "pure_finite_magma_counterexample_certificate",
            "pure_lean": True,
            "imports": [],
            "theorem_name": theorem_name,
        }

        certificate_path = run_dir / "certificate.lean"
        write_json(problem_dir / "problem.json", problem_payload)
        write_json(run_dir / "countermodel.json", countermodel_payload)
        write_json(run_dir / "metadata.json", metadata_payload)
        certificate_path.parent.mkdir(parents=True, exist_ok=True)
        certificate_path.write_text(certificate_code, encoding="utf-8")

        verification_path = run_dir / "verification.json"
        if verify:
            pending_verifications.append((certificate_path, verification_path))
            verification_result = "pending"
        else:
            write_json(
                verification_path,
                {
                    "checked_at_utc": created_at_utc,
                    "command": None,
                    "result": "not_run",
                    "certificate_sha256": file_sha256(certificate_path),
                },
            )
            verification_result = "not_run"

        verified = verification_result == "passed"
        latest_payload = {
            "run_id": run_id,
            "certificate_path": str(certificate_path),
            "countermodel_path": str(run_dir / "countermodel.json"),
            "verification_path": str(verification_path),
            "verified": verified,
            "reason": "latest pure Lean counterexample asset",
        }
        write_json(problem_dir / "latest.json", latest_payload)
        index_rows.append(
            {
                "problem_key": key,
                "eq1_id": int(row["eq1_id"]),
                "eq2_id": int(row["eq2_id"]),
                "latest_run_id": run_id,
                "certificate_path": str(certificate_path),
                "verified": verified,
            }
        )

    if pending_verifications:
        verify_all(pending_verifications, workers=verify_workers)
        index_rows = refresh_index_verification_status(index_rows, output_root, run_id)

    write_jsonl(output_root / "index.jsonl", index_rows)
    summary = {
        "schema_version": 1,
        "run_id": run_id,
        "created_at_utc": created_at_utc,
        "exported": len(rows),
        "verified": sum(1 for row in index_rows if row["verified"]),
        "verification_workers": verify_workers if verify else 0,
        "output_root": str(output_root),
    }
    write_json(output_root / "summary.json", summary)
    return summary


def verify_certificate(certificate_path: Path) -> dict:
    return DockerLeanExecutor().execute(LeanTask(certificate_path=certificate_path)).to_json()


def verify_all(items: list[tuple[Path, Path]], workers: int) -> None:
    worker_count = max(1, workers)
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        for verification_path, payload in executor.map(verify_one_item, items):
            write_json(verification_path, payload)


def verify_one_item(item: tuple[Path, Path]) -> tuple[Path, dict]:
    certificate_path, verification_path = item
    return verification_path, verify_certificate(certificate_path)


def refresh_index_verification_status(index_rows: list[dict], output_root: Path, run_id: str) -> list[dict]:
    refreshed: list[dict] = []
    for row in index_rows:
        verification_path = (
            output_root
            / row["problem_key"]
            / "runs"
            / run_id
            / "verification.json"
        )
        latest_path = output_root / row["problem_key"] / "latest.json"
        verification = json.loads(verification_path.read_text(encoding="utf-8"))
        updated = {**row, "verified": verification.get("result") == "passed"}
        latest = json.loads(latest_path.read_text(encoding="utf-8"))
        latest["verified"] = updated["verified"]
        write_json(latest_path, latest)
        refreshed.append(updated)
    return refreshed
