from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.lean_executor import LeanExecutor, LeanTask, utc_timestamp


@dataclass(frozen=True)
class CounterexampleCertificate:
    problem_key: str
    certificate_path: Path
    verification_path: Path


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")


def discover_counterexample_certificates(root: Path, run_id: str) -> list[CounterexampleCertificate]:
    certificates: list[CounterexampleCertificate] = []
    for certificate_path in sorted(root.glob(f"*/runs/{run_id}/certificate.lean")):
        problem_key = certificate_path.parent.parent.parent.name
        certificates.append(
            CounterexampleCertificate(
                problem_key=problem_key,
                certificate_path=certificate_path,
                verification_path=certificate_path.parent / "verification.json",
            )
        )
    return certificates


def verify_counterexample_assets(
    root: Path,
    run_id: str,
    executor: LeanExecutor,
    workers: int = 4,
    timeout_seconds: int = 60,
) -> dict:
    certificates = discover_counterexample_certificates(root, run_id)
    worker_count = max(1, workers)
    result_by_problem: dict[str, dict] = {}

    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        tasks = [
            (certificate, executor, timeout_seconds)
            for certificate in certificates
        ]
        for certificate, payload in pool.map(verify_one_certificate, tasks):
            write_json(certificate.verification_path, payload)
            result_by_problem[certificate.problem_key] = payload

    refresh_latest_files(root, run_id, result_by_problem)
    refresh_index(root, run_id, result_by_problem)
    summary = refresh_summary(root, run_id, executor.backend, worker_count, result_by_problem)
    return summary


def verify_one_certificate(
    item: tuple[CounterexampleCertificate, LeanExecutor, int]
) -> tuple[CounterexampleCertificate, dict]:
    certificate, executor, timeout_seconds = item
    result = executor.execute(
        LeanTask(certificate_path=certificate.certificate_path, timeout_seconds=timeout_seconds)
    )
    return certificate, result.to_json()


def refresh_latest_files(root: Path, run_id: str, result_by_problem: dict[str, dict]) -> None:
    for problem_key, verification in result_by_problem.items():
        latest_path = root / problem_key / "latest.json"
        if not latest_path.exists():
            continue
        latest = json.loads(latest_path.read_text(encoding="utf-8"))
        if latest.get("run_id") != run_id:
            continue
        latest["verified"] = verification.get("result") == "passed"
        latest["verification_path"] = str(root / problem_key / "runs" / run_id / "verification.json")
        write_json(latest_path, latest)


def refresh_index(root: Path, run_id: str, result_by_problem: dict[str, dict]) -> None:
    index_path = root / "index.jsonl"
    if not index_path.exists():
        return
    rows = read_jsonl(index_path)
    refreshed = []
    for row in rows:
        problem_key = row.get("problem_key")
        if problem_key in result_by_problem and row.get("latest_run_id") == run_id:
            row = {
                **row,
                "verified": result_by_problem[problem_key].get("result") == "passed",
            }
        refreshed.append(row)
    write_jsonl(index_path, refreshed)


def refresh_summary(
    root: Path,
    run_id: str,
    backend: str,
    workers: int,
    result_by_problem: dict[str, dict],
) -> dict:
    summary_path = root / "summary.json"
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    else:
        summary = {"schema_version": 1, "run_id": run_id, "output_root": str(root)}

    checked = len(result_by_problem)
    passed = sum(1 for result in result_by_problem.values() if result.get("result") == "passed")
    failed = sum(1 for result in result_by_problem.values() if result.get("result") == "failed")
    timed_out = sum(1 for result in result_by_problem.values() if result.get("result") == "timeout")
    summary.update(
        {
            "run_id": run_id,
            "output_root": str(root),
            "verified": passed,
            "checked": checked,
            "passed": passed,
            "failed": failed,
            "timeout": timed_out,
            "verification_backend": backend,
            "verification_workers": workers,
            "verified_at_utc": utc_timestamp(),
        }
    )
    write_json(summary_path, summary)
    return summary
