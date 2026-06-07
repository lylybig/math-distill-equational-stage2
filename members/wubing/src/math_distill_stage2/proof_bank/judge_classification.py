from __future__ import annotations

from typing import Any


def classify_official_result(raw: dict[str, Any]) -> dict[str, str | None]:
    status = str(raw.get("status") or "")
    text = " ".join(
        str(raw.get(key) or "") for key in ("stderr", "stdout", "message", "error_code")
    ).lower()
    if status == "accepted":
        return {
            "official_judge_status": "accepted",
            "judge_status": "accepted",
            "judge_error_kind": "none",
            "judge_error_subkind": None,
            "judge_error_summary": None,
        }
    if "unknown identifier" in text:
        kind = "lean_unknown_identifier"
    elif "unexpected token" in text or "expected command" in text:
        kind = "lean_parse_error"
    elif "application type mismatch" in text or "type mismatch" in text:
        kind = "lean_type_error"
    elif "unsolved goals" in text or "goals unsolved" in text:
        kind = "lean_unsolved_goals"
    elif "tactic" in text and "failed" in text:
        kind = "lean_tactic_failure"
    elif "timeout" in text or "timed out" in text:
        kind = "lean_timeout"
    elif status in {"unparsed", "malformed"}:
        kind = "invalid_json_or_payload" if status == "malformed" else "lean_parse_error"
    else:
        kind = "unknown"
    return {
        "official_judge_status": status,
        "judge_status": "rejected",
        "judge_error_kind": kind,
        "judge_error_subkind": None,
        "judge_error_summary": f"Official judge returned {status}.",
    }
