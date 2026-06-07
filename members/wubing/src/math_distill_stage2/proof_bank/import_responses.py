from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Callable

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.proof_bank.judge_classification import classify_official_result
from math_distill_stage2.proof_bank.storage import (
    write_content_addressed_text,
    write_json,
)


JudgeFunction = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]
JudgeRequest = tuple[dict[str, Any], dict[str, Any]]
BatchJudgeFunction = Callable[[list[JudgeRequest]], list[dict[str, Any]]]


@dataclass(frozen=True)
class ExtractedResponse:
    verdict: str | None
    proof: str
    error_kind: str | None
    error_summary: str | None = None


@dataclass(frozen=True)
class NormalizedProof:
    proof: str
    actions: list[str]


@dataclass(frozen=True)
class PendingJudgeAttempt:
    base: dict[str, Any]
    proof_body_sha256: str
    certificate_sha256: str
    normalization_actions: list[str]
    problem: dict[str, Any]
    answer: dict[str, Any]


RAW_RESPONSE_FORBIDDEN_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("sorry", re.compile(r"\bsorry\b")),
    ("admit", re.compile(r"\badmit\b")),
    ("axiom", re.compile(r"\baxiom\b")),
    ("unsafe", re.compile(r"\bunsafe\b")),
    ("import", re.compile(r"\bimport\b")),
    ("def submission", re.compile(r"\bdef\s+submission\b")),
    ("theorem", re.compile(r"\btheorem\b")),
    ("congr_arg", re.compile(r"\bcongr_arg\b")),
    ("*", re.compile(r"\*")),
)


def extract_response(text: str) -> ExtractedResponse:
    stripped = text.strip()
    for candidate in _json_candidates(stripped):
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        payload = _response_payload(payload)
        proof = _proof_field(payload)
        verdict = payload.get("verdict")
        if verdict != "true":
            return ExtractedResponse(None, "", "invalid_json_or_payload", "verdict must be true")
        if not isinstance(proof, str) or not proof.strip():
            return ExtractedResponse("true", "", "no_certificate_extracted", "proof is empty")
        return ExtractedResponse("true", proof.strip(), None)

    lean_match = re.search(r"```lean\s*(.*?)```", stripped, flags=re.DOTALL)
    if lean_match:
        proof = lean_match.group(1).strip()
        return (
            ExtractedResponse("true", proof, None)
            if proof
            else ExtractedResponse("true", "", "no_certificate_extracted")
        )

    if _looks_like_bare_lean(stripped):
        return ExtractedResponse("true", stripped, None)

    return ExtractedResponse(
        None,
        "",
        "no_certificate_extracted",
        "no JSON proof field or Lean code block found",
    )


def preflight_raw_responses(run_dir: Path) -> dict[str, Any]:
    """Strict nightly-loop gate before importing and judging Codex raw responses."""
    problems = read_jsonl(run_dir / "input_problems.jsonl")
    issues: list[dict[str, Any]] = []
    checked_count = 0
    for problem in problems:
        item_id = str(problem["item_id"])
        raw_path = run_dir / "raw_responses" / f"{item_id}.txt"
        raw_path_text = str(raw_path)
        if not raw_path.exists():
            issues.append(
                {
                    "item_id": item_id,
                    "raw_response_path": raw_path_text,
                    "error_kind": "missing_raw_response",
                    "error_summary": "raw response file is missing",
                }
            )
            continue
        raw_text = raw_path.read_text(encoding="utf-8")
        if not raw_text.strip():
            issues.append(
                {
                    "item_id": item_id,
                    "raw_response_path": raw_path_text,
                    "error_kind": "empty_raw_response",
                    "error_summary": "raw response file is empty",
                }
            )
            continue

        checked_count += 1
        forbidden = _forbidden_raw_response_token(raw_text)
        if forbidden is not None:
            issues.append(
                {
                    "item_id": item_id,
                    "raw_response_path": raw_path_text,
                    "error_kind": "forbidden_raw_response_text",
                    "error_subkind": forbidden,
                    "error_summary": f"forbidden raw response token: {forbidden}",
                }
            )

        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            issues.append(
                {
                    "item_id": item_id,
                    "raw_response_path": raw_path_text,
                    "error_kind": "invalid_raw_response_json",
                    "error_summary": f"expected exactly one JSON object: {exc.msg}",
                }
            )
            continue
        if not isinstance(payload, dict):
            issues.append(
                {
                    "item_id": item_id,
                    "raw_response_path": raw_path_text,
                    "error_kind": "invalid_raw_response_payload",
                    "error_summary": "top-level raw response must be a JSON object",
                }
            )
            continue

        if payload.get("verdict") != "true":
            issues.append(
                {
                    "item_id": item_id,
                    "raw_response_path": raw_path_text,
                    "error_kind": "invalid_raw_response_payload",
                    "error_summary": "verdict must be true",
                }
            )
        proof = payload.get("proof")
        if proof is None:
            issues.append(
                {
                    "item_id": item_id,
                    "raw_response_path": raw_path_text,
                    "error_kind": "invalid_raw_response_payload",
                    "error_summary": "proof field is required, even when empty",
                }
            )
        elif not isinstance(proof, str):
            issues.append(
                {
                    "item_id": item_id,
                    "raw_response_path": raw_path_text,
                    "error_kind": "invalid_raw_response_payload",
                    "error_summary": "proof field must be a string when present",
                }
            )

    return {
        "ok": not issues,
        "checked_count": checked_count,
        "issue_count": len(issues),
        "issues": issues,
    }


def _response_payload(payload: dict[str, Any]) -> dict[str, Any]:
    nested = payload.get("answer")
    if isinstance(nested, dict):
        return nested
    nested = payload.get("response")
    if isinstance(nested, dict):
        return nested
    return payload


def _proof_field(payload: dict[str, Any]) -> Any:
    for key in ("proof", "proof_body", "code", "lean", "certificate"):
        if key in payload:
            return payload.get(key)
    return None


def _json_candidates(text: str) -> list[str]:
    candidates = [text]
    fenced = re.findall(r"```json\s*(.*?)```", text, flags=re.DOTALL)
    candidates.extend(match.strip() for match in fenced)
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        candidates.append(match.group(0))
    return candidates


def _looks_like_bare_lean(text: str) -> bool:
    if "\n" not in text:
        return False
    lean_starts = ("intro ", "let ", "have ", "calc", "exact ")
    return any(text.lstrip().startswith(prefix) for prefix in lean_starts)


def _forbidden_raw_response_token(text: str) -> str | None:
    for token, pattern in RAW_RESPONSE_FORBIDDEN_PATTERNS:
        if pattern.search(text):
            return token
    return None


def normalize_proof_body(proof: str) -> NormalizedProof:
    actions: list[str] = []
    normalized = proof.strip()
    if normalized.startswith("```"):
        normalized = re.sub(r"^```(?:lean)?\s*", "", normalized)
        normalized = re.sub(r"\s*```$", "", normalized)
        actions.append("strip_markdown_fence")
    if "def submission" in normalized or "intro G _ h" in normalized:
        lines = normalized.splitlines()
        for index, line in enumerate(lines):
            if line.strip() == "intro G _ h":
                normalized = "\n".join(lines[index + 1 :]).strip()
                actions.append("strip_submission_wrapper")
                break
    if "*" in normalized:
        normalized = normalized.replace("*", "◇")
        actions.append("replace_star_with_diamond")
    if "congr_arg" in normalized:
        normalized = normalized.replace("congr_arg", "congrArg")
        actions.append("replace_congr_arg_with_congrArg")
    return NormalizedProof(proof=normalized, actions=actions)


def has_forbidden_construct(proof: str) -> str | None:
    forbidden = ("sorry", "admit", "axiom", "unsafe", "import ", "def submission", "theorem ")
    for token in forbidden:
        if token in proof:
            return token.strip()
    return None


def wrap_true_certificate(proof_body: str) -> str:
    lines = proof_body.strip().splitlines()
    non_empty = [line for line in lines if line.strip()]
    if non_empty:
        min_indent = min(len(line) - len(line.lstrip()) for line in non_empty)
        lines = [line[min_indent:] if len(line) >= min_indent else line for line in lines]
    indented = "\n".join("  " + line if line.strip() else "" for line in lines)
    return "import JudgeProblem\n\n" "def submission : Goal := by\n" "  intro G _ h\n" f"{indented}\n"


def official_problem_for_judge(problem: dict[str, Any]) -> dict[str, Any]:
    official = {
        "id": problem.get("id") or problem.get("source_problem_id"),
        "eq1_id": problem["eq1_id"],
        "eq2_id": problem["eq2_id"],
        "equation1": problem["equation1"],
        "equation2": problem["equation2"],
    }
    if "answer" in problem:
        official["answer"] = problem["answer"]
    elif "expected_verdict" in problem:
        official["answer"] = problem["expected_verdict"]
    for optional_key in ("proof_policy", "index", "difficulty"):
        if optional_key in problem:
            official[optional_key] = problem[optional_key]
    return official


def import_responses(
    run_dir: Path,
    judge: JudgeFunction | None = None,
    batch_judge: BatchJudgeFunction | None = None,
) -> dict[str, Any]:
    if (judge is None) == (batch_judge is None):
        raise ValueError("provide exactly one of judge or batch_judge")
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    source_run_id = str(manifest["source_run_id"])
    problems = read_jsonl(run_dir / "input_problems.jsonl")
    attempt_entries: list[dict[str, Any] | PendingJudgeAttempt] = []
    errors: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    for problem in problems:
        item_id = str(problem["item_id"])
        raw_path = run_dir / "raw_responses" / f"{item_id}.txt"
        if not raw_path.exists():
            errors.append({"item_id": item_id, "error": "missing_raw_response"})
            counts["missing_response"] += 1
            continue
        raw_text = raw_path.read_text(encoding="utf-8")
        raw_store = write_content_addressed_text(run_dir, "raw_responses_by_hash", raw_text, ".txt")
        extracted = extract_response(raw_text)
        attempt_id = f"attempt:{source_run_id}:{item_id}"
        base = {
            "schema_version": 1,
            "attempt_id": attempt_id,
            "problem_key": problem["problem_key"],
            "certificate_kind": "true_proof",
            "generator_mode": "codex_task",
            "generator_tool": "VSCode Codex",
            "generator_model": manifest.get("generator", {}).get("model"),
            "raw_response_sha256": raw_store.sha256,
            "source_run_id": source_run_id,
            "created_at": manifest.get("created_at_utc"),
        }
        if extracted.error_kind:
            attempt_entries.append(
                {
                    **base,
                    "judge_status": "skipped",
                    "official_judge_status": None,
                    "judge_error_kind": extracted.error_kind,
                    "judge_error_subkind": None,
                    "judge_error_summary": extracted.error_summary,
                }
            )
            counts["skipped"] += 1
            continue
        normalized = normalize_proof_body(extracted.proof)
        forbidden = has_forbidden_construct(normalized.proof)
        proof_store = write_content_addressed_text(
            run_dir, "proof_bodies", normalized.proof + "\n", ".lean"
        )
        if forbidden:
            attempt_entries.append(
                {
                    **base,
                    "proof_body_sha256": proof_store.sha256,
                    "normalization_actions": normalized.actions,
                    "judge_status": "skipped",
                    "official_judge_status": None,
                    "judge_error_kind": "forbidden_construct",
                    "judge_error_subkind": forbidden,
                    "judge_error_summary": f"Forbidden construct: {forbidden}",
                }
            )
            counts["skipped"] += 1
            continue
        code = wrap_true_certificate(normalized.proof)
        cert_store = write_content_addressed_text(run_dir, "certificates", code, ".lean")
        attempt_entries.append(
            PendingJudgeAttempt(
                base=base,
                proof_body_sha256=proof_store.sha256,
                certificate_sha256=cert_store.sha256,
                normalization_actions=normalized.actions,
                problem=official_problem_for_judge(problem),
                answer={"call": "judge", "verdict": "true", "code": code},
            )
        )

    pending = [entry for entry in attempt_entries if isinstance(entry, PendingJudgeAttempt)]
    if not pending:
        raw_results = []
    elif batch_judge is not None:
        raw_results = batch_judge([(entry.problem, entry.answer) for entry in pending])
    else:
        assert judge is not None
        raw_results = [judge(entry.problem, entry.answer) for entry in pending]
    if len(raw_results) != len(pending):
        raise ValueError(
            f"judge returned {len(raw_results)} result(s) for {len(pending)} pending attempt(s)"
        )

    attempts: list[dict[str, Any]] = []
    pending_results = iter(raw_results)
    for entry in attempt_entries:
        if not isinstance(entry, PendingJudgeAttempt):
            attempts.append(entry)
            continue
        raw_result = next(pending_results)
        result_store = write_content_addressed_text(
            run_dir,
            "judge_results",
            json.dumps(raw_result, ensure_ascii=False, sort_keys=True) + "\n",
            ".json",
        )
        classification = classify_official_result(raw_result)
        attempts.append(
            {
                **entry.base,
                "proof_body_sha256": entry.proof_body_sha256,
                "certificate_sha256": entry.certificate_sha256,
                "normalization_actions": entry.normalization_actions,
                "judge_result_sha256": result_store.sha256,
                **classification,
            }
        )
        counts[str(classification["judge_status"])] += 1

    write_jsonl(run_dir / "generated_attempts.jsonl", attempts)
    write_jsonl(run_dir / "extraction_errors.jsonl", errors)
    summary = {
        "source_run_id": source_run_id,
        "problem_count": len(problems),
        "attempt_count": len(attempts),
        "accepted_count": counts["accepted"],
        "rejected_count": counts["rejected"],
        "skipped_count": counts["skipped"],
        "error_count": counts["error"],
        "timeout_count": counts["timeout"],
        "missing_response_count": counts["missing_response"],
    }
    write_json(run_dir / "summary.json", summary)
    return summary
