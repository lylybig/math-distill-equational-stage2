from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import re
import shutil
from typing import Any

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.proof_bank.storage import (
    content_addressed_path,
    text_sha256,
    write_json,
)


CONTENT_DIRS = (
    "certificates",
    "proof_bodies",
    "prompts",
    "raw_responses",
    "judge_results",
    "by_problem",
)

BLOB_FIELDS = (
    ("certificate_sha256", "certificates", ".lean", ("certificates",)),
    ("proof_body_sha256", "proof_bodies", ".lean", ("proof_bodies",)),
    ("judge_result_sha256", "judge_results", ".json", ("judge_results",)),
    ("raw_response_sha256", "raw_responses", ".txt", ("raw_responses_by_hash", "raw_responses")),
)

ACCEPTED_REQUIRED_BLOBS = (
    ("certificate_sha256", "certificates", ".lean"),
    ("proof_body_sha256", "proof_bodies", ".lean"),
    ("judge_result_sha256", "judge_results", ".json"),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def init_bank(bank: Path) -> dict[str, Any]:
    bank.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1,
        "bank_id": "gpt_true_certificates",
        "certificate_kind": "true_proof",
        "created_at_utc": utc_now(),
        "problem_key_scheme": {
            "version": 1,
            "format": "implication:sig:<eq1_hash16>:<eq2_hash16>",
            "hash": "sha256",
            "hash_prefix_length": 16,
            "oriented": True,
        },
    }
    if not (bank / "bank_manifest.json").exists():
        write_json(bank / "bank_manifest.json", manifest)
    for filename in (
        "problems.jsonl",
        "attempts.jsonl",
        "accepted.jsonl",
        "latest_by_problem.jsonl",
    ):
        path = bank / filename
        if not path.exists():
            path.write_text("", encoding="utf-8")
    for dirname in CONTENT_DIRS:
        (bank / dirname).mkdir(parents=True, exist_ok=True)
    summary = rebuild_indexes(bank)
    summary["bank"] = str(bank)
    return summary


def rebuild_indexes(bank: Path) -> dict[str, Any]:
    attempts = read_jsonl(bank / "attempts.jsonl") if (bank / "attempts.jsonl").exists() else []
    problems = read_jsonl(bank / "problems.jsonl") if (bank / "problems.jsonl").exists() else []
    accepted = [
        {
            "schema_version": 1,
            "problem_key": row["problem_key"],
            "attempt_id": row["attempt_id"],
            "certificate_sha256": row.get("certificate_sha256"),
            "certificate_kind": row.get("certificate_kind"),
            "judge_commit": row.get("judge_commit"),
            "accepted_at": row.get("created_at"),
        }
        for row in attempts
        if row.get("judge_status") == "accepted"
        and row.get("official_judge_status") == "accepted"
        and row.get("certificate_kind") == "true_proof"
    ]

    by_problem: dict[str, list[dict]] = defaultdict(list)
    for row in attempts:
        by_problem[str(row.get("problem_key"))].append(row)

    latest_rows = []
    for problem_key, rows in sorted(by_problem.items()):
        latest = rows[-1]
        accepted_rows = [row for row in rows if row.get("judge_status") == "accepted"]
        rejected_rows = [row for row in rows if row.get("judge_status") == "rejected"]
        latest_rows.append(
            {
                "schema_version": 1,
                "problem_key": problem_key,
                "latest_attempt_id": latest.get("attempt_id"),
                "latest_status": latest.get("judge_status"),
                "accepted_attempt_count": len(accepted_rows),
                "rejected_attempt_count": len(rejected_rows),
                "best_known_certificate_sha256": (
                    accepted_rows[0].get("certificate_sha256") if accepted_rows else None
                ),
                "updated_at": latest.get("created_at"),
            }
        )

    write_jsonl(bank / "accepted.jsonl", accepted)
    write_jsonl(bank / "latest_by_problem.jsonl", latest_rows)
    problem_view_count = rebuild_problem_views(bank, problems, by_problem)
    summary = {
        "schema_version": 1,
        "problem_count": len(problems),
        "attempt_count": len(attempts),
        "accepted_count": len(accepted),
        "latest_problem_count": len(latest_rows),
        "problem_view_count": problem_view_count,
    }
    write_json(bank / "bank_summary.json", summary)
    return summary


def check_bank(bank: Path) -> dict[str, Any]:
    errors: list[str] = []
    if not (bank / "bank_manifest.json").exists():
        errors.append("missing bank_manifest.json")
    attempts = read_jsonl(bank / "attempts.jsonl") if (bank / "attempts.jsonl").exists() else []
    seen_attempts: set[str] = set()
    for row in attempts:
        attempt_id = str(row.get("attempt_id"))
        if attempt_id in seen_attempts:
            errors.append(f"duplicate attempt_id: {attempt_id}")
        seen_attempts.add(attempt_id)
        if row.get("judge_status") == "accepted" and row.get("official_judge_status") != "accepted":
            errors.append(f"accepted attempt without official accepted judge result: {attempt_id}")
        if row.get("judge_status") == "accepted" and row.get("official_judge_status") == "accepted":
            for field, kind, suffix in ACCEPTED_REQUIRED_BLOBS:
                digest = row.get(field)
                if not isinstance(digest, str) or not digest:
                    errors.append(f"missing {field} for {attempt_id}")
                    continue
                path = content_addressed_path(bank, kind, digest, suffix)
                if not path.exists():
                    errors.append(f"missing {kind} blob for {attempt_id}")
                    continue
                if text_sha256(path.read_text(encoding="utf-8")) != digest:
                    errors.append(f"sha mismatch for {kind} blob for {attempt_id}")
    return {
        "bank": str(bank),
        "ok": not errors,
        "errors": errors,
        "attempt_count": len(attempts),
    }


def merge_run(bank: Path, run_dir: Path) -> dict[str, Any]:
    init_bank(bank)
    existing_problems = read_jsonl(bank / "problems.jsonl")
    existing_attempts = read_jsonl(bank / "attempts.jsonl")
    problem_by_key = {row["problem_key"]: row for row in existing_problems}
    attempt_by_id = {row["attempt_id"]: row for row in existing_attempts}

    new_problems = 0
    for row in read_jsonl(run_dir / "input_problems.jsonl"):
        key = row["problem_key"]
        if key not in problem_by_key:
            problem_by_key[key] = {
                "schema_version": 1,
                "problem_key": key,
                "problem_aliases": row.get("problem_aliases", []),
                "eq1_id": row.get("eq1_id"),
                "eq2_id": row.get("eq2_id"),
                "equation1": row.get("equation1"),
                "equation2": row.get("equation2"),
                "eq1_signature": row.get("eq1_signature"),
                "eq2_signature": row.get("eq2_signature"),
                "expected_verdict": row.get("expected_verdict"),
                "first_seen_dataset": row.get("source_dataset"),
                "source_datasets": row.get("source_datasets") or [row.get("source_dataset")],
                "created_at": utc_now(),
            }
            new_problems += 1

    new_attempts = 0
    copied_blobs = 0
    for row in read_jsonl(run_dir / "generated_attempts.jsonl"):
        attempt_id = row["attempt_id"]
        if attempt_id in attempt_by_id:
            if attempt_by_id[attempt_id] != row:
                raise ValueError(f"same attempt_id with different payload: {attempt_id}")
            copied_blobs += copy_attempt_blobs(bank, run_dir, row)
            continue
        copied_blobs += copy_attempt_blobs(bank, run_dir, row)
        attempt_by_id[attempt_id] = row
        new_attempts += 1

    write_jsonl(bank / "problems.jsonl", [problem_by_key[key] for key in sorted(problem_by_key)])
    write_jsonl(bank / "attempts.jsonl", [attempt_by_id[key] for key in sorted(attempt_by_id)])
    summary = rebuild_indexes(bank)
    return {
        "bank": str(bank),
        "run_dir": str(run_dir),
        "new_problems": new_problems,
        "new_attempts": new_attempts,
        "copied_blobs": copied_blobs,
        "accepted_count": summary["accepted_count"],
    }


def preview_merge_run(bank: Path, run_dir: Path) -> dict[str, Any]:
    existing_problems = read_jsonl(bank / "problems.jsonl") if (bank / "problems.jsonl").exists() else []
    existing_attempts = read_jsonl(bank / "attempts.jsonl") if (bank / "attempts.jsonl").exists() else []
    problem_by_key = {row["problem_key"]: row for row in existing_problems}
    attempt_by_id = {row["attempt_id"]: row for row in existing_attempts}

    new_problems = 0
    for row in read_jsonl(run_dir / "input_problems.jsonl"):
        if row["problem_key"] not in problem_by_key:
            new_problems += 1

    new_attempts = 0
    copied_blobs = 0
    for row in read_jsonl(run_dir / "generated_attempts.jsonl"):
        attempt_id = row["attempt_id"]
        if attempt_id in attempt_by_id:
            if attempt_by_id[attempt_id] != row:
                raise ValueError(f"same attempt_id with different payload: {attempt_id}")
        else:
            new_attempts += 1
        copied_blobs += count_validated_attempt_blobs(bank, run_dir, row)

    return {
        "dry_run": True,
        "bank": str(bank),
        "run_dir": str(run_dir),
        "new_problems": new_problems,
        "new_attempts": new_attempts,
        "copied_blobs": copied_blobs,
    }


def rebuild_problem_views(
    bank: Path,
    problems: list[dict[str, Any]],
    attempts_by_problem: dict[str, list[dict]],
) -> int:
    view_root = bank / "by_problem"
    if view_root.exists():
        shutil.rmtree(view_root)
    view_root.mkdir(parents=True, exist_ok=True)

    problem_by_key = {row["problem_key"]: row for row in problems}
    written = 0
    for problem_key, attempts in sorted(attempts_by_problem.items()):
        problem = problem_by_key.get(problem_key)
        if problem is None:
            continue
        accepted_attempts = [
            row
            for row in attempts
            if row.get("judge_status") == "accepted"
            and row.get("official_judge_status") == "accepted"
            and row.get("certificate_kind") == "true_proof"
            and isinstance(row.get("certificate_sha256"), str)
        ]
        if not accepted_attempts:
            continue
        certificate_entries = []
        for index, candidate in enumerate(accepted_attempts, start=1):
            certificate_sha = str(candidate["certificate_sha256"])
            certificate_path = content_addressed_path(bank, "certificates", certificate_sha, ".lean")
            if not certificate_path.exists():
                continue
            relative_view_path = (
                Path("certificates")
                / certificate_view_name(index, str(candidate.get("attempt_id")))
                / "certificate.lean"
            )
            certificate_entries.append(
                {
                    "attempt_id": candidate.get("attempt_id"),
                    "certificate_sha256": certificate_sha,
                    "proof_body_sha256": candidate.get("proof_body_sha256"),
                    "judge_result_sha256": candidate.get("judge_result_sha256"),
                    "source_run_id": candidate.get("source_run_id"),
                    "created_at": candidate.get("created_at"),
                    "certificate_store_path": str(certificate_path.relative_to(bank)),
                    "certificate_path": relative_view_path.as_posix(),
                }
            )
        if not certificate_entries:
            continue

        best_certificate = certificate_entries[0]
        best_certificate_path = bank / best_certificate["certificate_store_path"]
        view_dir = view_root / problem_view_name(problem)
        view_dir.mkdir(parents=True, exist_ok=True)
        (view_dir / "certificate.lean").write_text(
            best_certificate_path.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        for entry in certificate_entries:
            source = bank / entry["certificate_store_path"]
            target = view_dir / entry["certificate_path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        metadata = {
            "schema_version": 1,
            "problem_key": problem_key,
            "attempt_id": best_certificate["attempt_id"],
            "best_attempt_id": best_certificate["attempt_id"],
            "accepted_attempt_count": len(certificate_entries),
            "eq1_id": problem.get("eq1_id"),
            "eq2_id": problem.get("eq2_id"),
            "equation1": problem.get("equation1"),
            "equation2": problem.get("equation2"),
            "eq1_signature": problem.get("eq1_signature"),
            "eq2_signature": problem.get("eq2_signature"),
            "certificate_sha256": best_certificate["certificate_sha256"],
            "proof_body_sha256": best_certificate["proof_body_sha256"],
            "judge_result_sha256": best_certificate["judge_result_sha256"],
            "source_run_id": best_certificate["source_run_id"],
            "certificate_store_path": best_certificate["certificate_store_path"],
            "certificates": certificate_entries,
        }
        write_json(view_dir / "metadata.json", metadata)
        written += 1
    return written


def problem_view_name(problem: dict[str, Any]) -> str:
    return f"eq1-{problem.get('eq1_id')}-eq2-{problem.get('eq2_id')}"


def certificate_view_name(index: int, attempt_id: str) -> str:
    safe_attempt_id = re.sub(r"[^A-Za-z0-9_.-]+", "-", attempt_id).strip("-")
    return f"{index:06d}_{safe_attempt_id}"


def copy_attempt_blobs(bank: Path, run_dir: Path, attempt: dict[str, Any]) -> int:
    copied = 0
    attempt_id = str(attempt.get("attempt_id"))
    for field, dest_kind, suffix, source_kinds in BLOB_FIELDS:
        digest = attempt.get(field)
        if not isinstance(digest, str) or not digest:
            continue
        source = next(
            (
                content_addressed_path(run_dir, source_kind, digest, suffix)
                for source_kind in source_kinds
                if content_addressed_path(run_dir, source_kind, digest, suffix).exists()
            ),
            None,
        )
        if source is None:
            raise ValueError(f"missing {dest_kind} source blob for {attempt_id}: {digest}")
        target = content_addressed_path(bank, dest_kind, digest, suffix)
        copied += copy_verified_text_blob(source, target, digest)
    return copied


def count_validated_attempt_blobs(bank: Path, run_dir: Path, attempt: dict[str, Any]) -> int:
    copied = 0
    attempt_id = str(attempt.get("attempt_id"))
    for field, dest_kind, suffix, source_kinds in BLOB_FIELDS:
        digest = attempt.get(field)
        if not isinstance(digest, str) or not digest:
            continue
        source = next(
            (
                content_addressed_path(run_dir, source_kind, digest, suffix)
                for source_kind in source_kinds
                if content_addressed_path(run_dir, source_kind, digest, suffix).exists()
            ),
            None,
        )
        if source is None:
            raise ValueError(f"missing {dest_kind} source blob for {attempt_id}: {digest}")
        if text_sha256(source.read_text(encoding="utf-8")) != digest:
            raise ValueError(f"sha mismatch for source blob: {source}")
        target = content_addressed_path(bank, dest_kind, digest, suffix)
        if not target.exists():
            copied += 1
    return copied


def copy_verified_text_blob(source: Path, target: Path, digest: str) -> int:
    source_text = source.read_text(encoding="utf-8")
    if text_sha256(source_text) != digest:
        raise ValueError(f"sha mismatch for source blob: {source}")
    if target.exists():
        target_text = target.read_text(encoding="utf-8")
        if text_sha256(target_text) != digest:
            raise ValueError(f"sha mismatch for target blob: {target}")
        return 0
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source_text, encoding="utf-8")
    return 1
