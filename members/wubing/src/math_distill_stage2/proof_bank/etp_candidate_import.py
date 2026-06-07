from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from math_distill_stage2 import order5_strategy_registry as registry
from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.proof_bank.judge_classification import classify_official_result
from math_distill_stage2.proof_bank.keying import problem_key_from_signatures
from math_distill_stage2.proof_bank.storage import write_content_addressed_text, write_json


DEFAULT_ETP_EQ2_SOURCE_RUN_ID = (
    "full-eq1-to-equation2-seedgate-etp-native-explicit-20260520"
)


@dataclass(frozen=True)
class CandidateCode:
    path: Path
    payload: dict[str, Any]
    code: str

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.code.encode("utf-8")).hexdigest()

    @property
    def byte_length(self) -> int:
        return len(self.code.encode("utf-8"))


def extract_submission_proof_body(code: str) -> str:
    """Extract the body after `intro G _ h` from a self-contained certificate."""

    lines = code.splitlines()
    intro_index = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("intro G _ h") or stripped.startswith("intro G _ h0"):
            intro_index = index
            break
    if intro_index is None:
        raise ValueError("certificate does not contain `intro G _ h`")

    body_lines = [
        line[2:] if line.startswith("  ") else line
        for line in lines[intro_index + 1 :]
    ]
    proof_body = "\n".join(body_lines).rstrip() + "\n"
    registry._singleton_prefix_from_source_level_proof_body(
        proof_body,
        allow_bare=True,
    )
    return proof_body


def build_etp_eq2_candidate_run(
    *,
    accepted_sources_path: Path,
    candidates_dir: Path,
    run_dir: Path,
    source_run_id: str = DEFAULT_ETP_EQ2_SOURCE_RUN_ID,
) -> dict[str, Any]:
    if run_dir.exists():
        raise FileExistsError(f"run directory already exists: {run_dir}")
    run_dir.mkdir(parents=True)

    accepted_rows = read_jsonl(accepted_sources_path)
    if not accepted_rows:
        raise ValueError(f"no accepted source rows found: {accepted_sources_path}")

    created_at = (
        datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )
    code_index = _load_code_index(candidates_dir)
    result_index = _load_result_index(candidates_dir)

    input_rows: list[dict[str, Any]] = []
    attempt_rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    family_counts: Counter[str] = Counter()

    for item_index, row in enumerate(
        sorted(accepted_rows, key=lambda item: int(item["eq1_id"])),
        start=1,
    ):
        item_id = f"{item_index:06d}"
        problem_id = str(row["problem_id"])
        family_counts[_candidate_family(str(row.get("candidate_key") or ""))] += 1

        code_record = _select_code(problem_id, row, code_index)
        result_record = _select_result(problem_id, row, result_index)
        code = code_record.code
        proof_body = extract_submission_proof_body(code)
        problem = _problem_payload(code_record.payload, row)
        eq1_signature = _signature(problem["equation1"])
        eq2_signature = _signature(problem["equation2"])
        problem_key = problem_key_from_signatures(eq1_signature, eq2_signature)

        input_rows.append(
            {
                "schema_version": 1,
                "item_id": item_id,
                "problem_key": problem_key,
                "source_problem_id": problem_id,
                "source_dataset": "order5_strategy_registry.etp_eq2_candidate_import",
                "source_candidate_stratum": _candidate_family(
                    str(row.get("candidate_key") or "")
                ),
                "eq1_id": int(row["eq1_id"]),
                "eq2_id": int(row["eq2_id"]),
                "eq1_signature": eq1_signature,
                "eq2_signature": eq2_signature,
                "equation1": problem["equation1"],
                "equation2": problem["equation2"],
                "expected_verdict": True,
            }
        )

        raw_response_text = json.dumps(
            {"verdict": "true", "proof": proof_body},
            ensure_ascii=False,
            separators=(",", ":"),
        ) + "\n"
        judge_result_text = json.dumps(
            result_record,
            ensure_ascii=False,
            sort_keys=True,
        ) + "\n"
        raw_store = write_content_addressed_text(
            run_dir,
            "raw_responses_by_hash",
            raw_response_text,
            ".txt",
        )
        proof_store = write_content_addressed_text(
            run_dir,
            "proof_bodies",
            proof_body,
            ".lean",
        )
        cert_store = write_content_addressed_text(
            run_dir,
            "certificates",
            code,
            ".lean",
        )
        judge_store = write_content_addressed_text(
            run_dir,
            "judge_results",
            judge_result_text,
            ".json",
        )
        classification = classify_official_result(result_record)
        if classification["judge_status"] != "accepted":
            errors.append(
                {
                    "item_id": item_id,
                    "problem_id": problem_id,
                    "error": "accepted_source_row_without_accepted_result",
                    "classification": classification,
                }
            )
            continue

        attempt_rows.append(
            {
                "schema_version": 1,
                "attempt_id": f"attempt:{source_run_id}:{item_id}",
                "problem_key": problem_key,
                "certificate_kind": "true_proof",
                "certificate_sha256": cert_store.sha256,
                "created_at": created_at,
                "generator_mode": "deterministic_etp_eq2_candidate_import",
                "generator_model": None,
                "generator_tool": "Stage2 ETP Eq2 candidate importer",
                "judge_error_kind": "none",
                "judge_error_subkind": None,
                "judge_error_summary": None,
                "judge_result_sha256": judge_store.sha256,
                "judge_status": "accepted",
                "normalization_actions": [],
                "official_judge_status": "accepted",
                "proof_body_sha256": proof_store.sha256,
                "raw_response_sha256": raw_store.sha256,
                "source_run_id": source_run_id,
            }
        )

    manifest = {
        "schema_version": 1,
        "source_run_id": source_run_id,
        "created_at_utc": created_at,
        "run_dir": str(run_dir),
        "accepted_sources_path": str(accepted_sources_path),
        "candidates_dir": str(candidates_dir),
        "problem_count": len(input_rows),
        "generator": {
            "mode": "deterministic_etp_eq2_candidate_import",
            "model": None,
        },
        "candidate_family_counts": dict(sorted(family_counts.items())),
    }
    write_json(run_dir / "manifest.json", manifest)
    write_jsonl(run_dir / "input_problems.jsonl", input_rows)
    write_jsonl(run_dir / "generated_attempts.jsonl", attempt_rows)
    write_jsonl(run_dir / "extraction_errors.jsonl", errors)
    summary = {
        "schema_version": 1,
        "source_run_id": source_run_id,
        "problem_count": len(input_rows),
        "attempt_count": len(attempt_rows),
        "accepted_count": sum(
            1 for row in attempt_rows if row.get("judge_status") == "accepted"
        ),
        "error_count": len(errors),
        "candidate_family_counts": dict(sorted(family_counts.items())),
    }
    write_json(run_dir / "summary.json", summary)
    if errors:
        raise ValueError(f"candidate import produced {len(errors)} error(s)")
    return summary


def _load_code_index(candidates_dir: Path) -> dict[str, list[CandidateCode]]:
    index: dict[str, list[CandidateCode]] = defaultdict(list)
    for path in sorted(candidates_dir.glob("*.jsonl")):
        if "input" not in path.name and "results" not in path.name:
            continue
        for payload in read_jsonl(path):
            problem_id = _problem_id(payload)
            answer = payload.get("answer")
            code = answer.get("code") if isinstance(answer, dict) else None
            if problem_id and isinstance(code, str):
                index[problem_id].append(CandidateCode(path, payload, code))
    return index


def _load_result_index(candidates_dir: Path) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in sorted(candidates_dir.glob("*results*.jsonl")):
        for payload in read_jsonl(path):
            problem_id = _problem_id(payload)
            if not problem_id:
                continue
            result = payload.get("raw_result") or payload.get("remote_result") or payload
            if isinstance(result, dict) and str(result.get("status") or "") == "accepted":
                index[problem_id].append(result)
    return index


def _select_code(
    problem_id: str,
    accepted_row: dict[str, Any],
    code_index: dict[str, list[CandidateCode]],
) -> CandidateCode:
    candidates = code_index.get(problem_id, [])
    if not candidates:
        raise ValueError(f"missing candidate code for {problem_id}")
    expected_sha = accepted_row.get("code_sha256")
    if isinstance(expected_sha, str) and expected_sha:
        matches = [candidate for candidate in candidates if candidate.sha256 == expected_sha]
        if not matches:
            raise ValueError(f"no code candidate matches sha for {problem_id}")
        return sorted(matches, key=lambda candidate: str(candidate.path))[0]
    expected_bytes = accepted_row.get("code_bytes")
    matches = [
        candidate
        for candidate in candidates
        if isinstance(expected_bytes, int) and candidate.byte_length == expected_bytes
    ]
    return sorted(matches or candidates, key=lambda candidate: (candidate.sha256, str(candidate.path)))[0]


def _select_result(
    problem_id: str,
    accepted_row: dict[str, Any],
    result_index: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    candidates = result_index.get(problem_id, [])
    if not candidates:
        raise ValueError(f"missing accepted judge result for {problem_id}")
    artifact_path = accepted_row.get("artifact_path")
    if isinstance(artifact_path, str) and artifact_path:
        matches = [
            candidate
            for candidate in candidates
            if candidate.get("artifact_path") == artifact_path
            or candidate.get("remote_judge_v2", {}).get("url") == artifact_path
        ]
        if matches:
            return sorted(matches, key=lambda item: json.dumps(item, sort_keys=True))[0]
    return sorted(candidates, key=lambda item: json.dumps(item, sort_keys=True))[0]


def _problem_payload(payload: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    problem = payload.get("problem")
    if not isinstance(problem, dict):
        raise ValueError(f"candidate code row has no problem payload: {row.get('problem_id')}")
    if int(problem["eq1_id"]) != int(row["eq1_id"]):
        raise ValueError(f"eq1_id mismatch for {row.get('problem_id')}")
    if int(problem["eq2_id"]) != int(row["eq2_id"]):
        raise ValueError(f"eq2_id mismatch for {row.get('problem_id')}")
    return problem


def _problem_id(payload: dict[str, Any]) -> str:
    for key in ("id", "problem_id"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    problem = payload.get("problem")
    if isinstance(problem, dict):
        value = problem.get("id")
        if isinstance(value, str) and value:
            return value
    return ""


def _signature(equation: str) -> str:
    return registry._canonical_signature_from_equation(
        registry._parse_stage2_equation(equation)
    )


def _candidate_family(candidate_key: str) -> str:
    if ".native_explicit_ge5m." in candidate_key:
        return "native_explicit_ge5m"
    if ".context_rw." in candidate_key:
        return "context_rw"
    if "low_cost_combo20" in candidate_key:
        return "low_cost_combo20"
    if "compilable_combo" in candidate_key:
        return "compilable_combo"
    return "other"
