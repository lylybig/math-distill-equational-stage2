from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from math_distill_stage2.counterexample.verified_index import file_sha256
from math_distill_stage2.dataset_io import write_jsonl


def build_counterexample_evidence_bank(
    *,
    asset_root: Path,
    output_path: Path,
    summary_output_path: Path | None = None,
    verified_only: bool = True,
    limit: int | None = None,
    max_certificate_chars: int = 0,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    summary = {
        "schema_version": 1,
        "created_at_utc": utc_timestamp(),
        "asset_root": str(asset_root),
        "output_path": str(output_path),
        "verified_only": verified_only,
        "max_certificate_chars": max_certificate_chars,
        "seen_assets": 0,
        "written": 0,
        "skipped_unverified": 0,
        "skipped_non_negative": 0,
        "skipped_missing_files": 0,
    }

    for problem_dir in iter_problem_asset_dirs(asset_root):
        if limit is not None and len(rows) >= limit:
            break
        summary["seen_assets"] += 1
        try:
            row = build_counterexample_evidence_row(
                asset_root=asset_root,
                problem_dir=problem_dir,
                verified_only=verified_only,
                max_certificate_chars=max_certificate_chars,
            )
        except MissingCounterexampleAsset:
            summary["skipped_missing_files"] += 1
            continue
        except UnverifiedCounterexampleAsset:
            summary["skipped_unverified"] += 1
            continue
        except NonNegativeCounterexampleAsset:
            summary["skipped_non_negative"] += 1
            continue
        rows.append(row)

    write_jsonl(output_path, rows)
    summary["written"] = len(rows)
    if summary_output_path is not None:
        write_json(summary_output_path, summary)
    return summary


def build_counterexample_evidence_row(
    *,
    asset_root: Path,
    problem_dir: Path,
    verified_only: bool,
    max_certificate_chars: int,
) -> dict[str, Any]:
    problem_path = problem_dir / "problem.json"
    latest_path = problem_dir / "latest.json"
    if not problem_path.exists() or not latest_path.exists():
        raise MissingCounterexampleAsset

    problem = read_json(problem_path)
    latest = read_json(latest_path)
    if problem.get("answer") is not False:
        raise NonNegativeCounterexampleAsset
    if verified_only and latest.get("verified") is not True:
        raise UnverifiedCounterexampleAsset

    countermodel_path = resolve_asset_path(
        latest.get("countermodel_path"),
        asset_root=asset_root,
        problem_dir=problem_dir,
    )
    certificate_path = resolve_asset_path(
        latest.get("certificate_path"),
        asset_root=asset_root,
        problem_dir=problem_dir,
    )
    verification_path = resolve_asset_path(
        latest.get("verification_path"),
        asset_root=asset_root,
        problem_dir=problem_dir,
    )
    if not countermodel_path.exists() or not certificate_path.exists():
        raise MissingCounterexampleAsset

    countermodel = read_json(countermodel_path)
    verification = read_json(verification_path) if verification_path.exists() else {}
    certificate_excerpt = read_certificate_excerpt(certificate_path, max_certificate_chars)
    eq1_id = int(problem["eq1_id"])
    eq2_id = int(problem["eq2_id"])
    prompt_evidence = render_prompt_evidence(
        problem=problem,
        countermodel=countermodel,
        certificate_path=display_path(certificate_path),
        certificate_excerpt=certificate_excerpt,
    )

    row: dict[str, Any] = {
        "schema_version": 1,
        "id": str(problem["id"]),
        "problem_id": str(problem["id"]),
        "problem_key": str(problem.get("problem_key") or problem_dir.name),
        "subset": problem.get("subset"),
        "eq1_id": eq1_id,
        "eq2_id": eq2_id,
        "equation1": problem["equation1"],
        "equation2": problem["equation2"],
        "eq1_signature": problem.get("eq1_signature"),
        "eq2_signature": problem.get("eq2_signature"),
        "answer": False,
        "verdict": "false",
        "evidence_type": "finite_magma_counterexample",
        "run_id": latest.get("run_id"),
        "verified": latest.get("verified") is True,
        "countermodel": normalize_countermodel(countermodel),
        "certificate_path": display_path(certificate_path),
        "countermodel_path": display_path(countermodel_path),
        "verification_path": display_path(verification_path),
        "certificate_sha256": verification.get("certificate_sha256") or file_sha256(certificate_path),
        "evidence": prompt_evidence,
        "prompt_evidence": prompt_evidence,
    }
    if certificate_excerpt:
        row["certificate_excerpt"] = certificate_excerpt
    return row


def iter_problem_asset_dirs(asset_root: Path) -> list[Path]:
    if not asset_root.exists():
        return []
    return sorted(
        path
        for path in asset_root.iterdir()
        if path.is_dir() and (path / "problem.json").exists() and (path / "latest.json").exists()
    )


def render_prompt_evidence(
    *,
    problem: dict[str, Any],
    countermodel: dict[str, Any],
    certificate_path: str,
    certificate_excerpt: str,
) -> str:
    eq1_id = int(problem["eq1_id"])
    eq2_id = int(problem["eq2_id"])
    table = countermodel["table"]
    lines = [
        "Verified finite magma counterexample.",
        "Required verdict: false.",
        f"Problem id: {problem['id']}.",
        f"Equation {eq1_id}: {problem['equation1']}",
        f"Equation {eq2_id}: {problem['equation2']}",
        f"Carrier: {countermodel.get('carrier') or list(range(int(countermodel['order'])))}",
        "Operation table for `op`; rows are left operand, columns are right operand:",
    ]
    lines.extend(f"row {index}: {row}" for index, row in enumerate(table))
    lines.extend(
        [
            f"This magma satisfies Equation {eq1_id} and refutes Equation {eq2_id}.",
            f"Lean asset path: {certificate_path}",
            'Return exactly one judge JSON object with verdict "false" and Lean 4 code.',
        ]
    )
    if certificate_excerpt:
        lines.extend(["Lean certificate excerpt:", certificate_excerpt])
    return "\n".join(lines)


def normalize_countermodel(countermodel: dict[str, Any]) -> dict[str, Any]:
    order = int(countermodel["order"])
    return {
        "order": order,
        "carrier": countermodel.get("carrier") or list(range(order)),
        "table": countermodel["table"],
        "source_path": countermodel.get("source_path"),
    }


def read_certificate_excerpt(certificate_path: Path, max_certificate_chars: int) -> str:
    if max_certificate_chars <= 0:
        return ""
    text = certificate_path.read_text(encoding="utf-8")
    return text[:max_certificate_chars]


def resolve_asset_path(raw_path: Any, *, asset_root: Path, problem_dir: Path) -> Path:
    if raw_path is None:
        return problem_dir / "__missing__"
    path = Path(str(raw_path))
    if path.is_absolute():
        return path
    for base in (Path.cwd(), problem_dir, asset_root):
        candidate = base / path
        if candidate.exists():
            return candidate
    return Path.cwd() / path


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class MissingCounterexampleAsset(ValueError):
    pass


class UnverifiedCounterexampleAsset(ValueError):
    pass


class NonNegativeCounterexampleAsset(ValueError):
    pass
