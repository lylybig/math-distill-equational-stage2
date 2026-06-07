from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from math_distill_stage2.dataset_io import read_jsonl
from math_distill_stage2.proof_bank.bank import check_bank
from math_distill_stage2.proof_bank.candidate_sampling import STRATA
from math_distill_stage2.proof_bank.storage import read_json, write_json


def audit_proof_bank_quality(
    *,
    bank: Path,
    run_summary_path: Path | None = None,
    sampled_manifest_path: Path | None = None,
    marathon_state_path: Path | None = None,
    output_path: Path | None = None,
    zero_accepted_pause_threshold: int = 3,
) -> dict[str, Any]:
    inspected_paths = [str(bank)]
    if run_summary_path is not None:
        inspected_paths.append(str(run_summary_path))
    if sampled_manifest_path is not None:
        inspected_paths.append(str(sampled_manifest_path))
    if marathon_state_path is not None:
        inspected_paths.append(str(marathon_state_path))

    bank_check = check_bank(bank)
    attempts = (
        read_jsonl(bank / "attempts.jsonl") if (bank / "attempts.jsonl").exists() else []
    )
    run_summary = _read_optional_json(run_summary_path)
    sampled_manifest = _read_optional_json(sampled_manifest_path)
    marathon_state = _read_optional_json(marathon_state_path)

    cycle = _cycle_summary(run_summary)
    recent = _attempt_summary(attempts)
    source_balance = _source_balance(sampled_manifest)
    error_mix = _error_mix(run_summary, attempts)
    exclusions = {
        "accepted": int(sampled_manifest.get("excluded_accepted_count") or 0),
        "attempt_ceiling": int(sampled_manifest.get("excluded_attempt_ceiling_count") or 0),
    }

    notes: list[str] = []
    decision = "continue"
    if not bank_check["ok"]:
        decision = "pause_for_debug"
        notes.append("bank integrity check failed")

    if cycle["missing_response_count"] > 0:
        decision = "pause_for_debug"
        notes.append("missing raw responses")

    current_zero = 1 if cycle["attempt_count"] > 0 and cycle["accepted_count"] == 0 else 0
    previous_zero = int(marathon_state.get("consecutive_zero_accepted_cycles") or 0)
    if previous_zero + current_zero >= zero_accepted_pause_threshold:
        decision = "pause_for_debug"
        notes.append("too many consecutive zero-accepted cycles")

    if cycle["attempt_count"] > 0:
        broken = cycle["skipped_count"] + cycle["error_count"] + cycle["timeout_count"]
        if broken / cycle["attempt_count"] >= 0.8:
            decision = "pause_for_debug"
            notes.append("skipped/error/timeout rate is too high")

    selected_count = int(sampled_manifest.get("selected_count") or 0)
    direct_count = source_balance["direct_order4_true_exploration"]["selected_count"]
    if selected_count > 0 and direct_count == 0 and decision == "continue":
        decision = "continue_with_adjusted_sampling"
        notes.append("missing direct_order4_true_exploration samples")

    audit = {
        "schema_version": 1,
        "bank": str(bank),
        "inspected_paths": inspected_paths,
        "bank_check": bank_check,
        "cycle": cycle,
        "recent": recent,
        "source_balance": source_balance,
        "error_mix": error_mix,
        "exclusions": exclusions,
        "decision": decision,
        "notes": notes,
    }
    if output_path is not None:
        write_json(output_path, audit)
    return audit


def _read_optional_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    return read_json(path)


def _cycle_summary(summary: dict[str, Any]) -> dict[str, Any]:
    attempt_count = int(summary.get("attempt_count") or 0)
    accepted_count = int(summary.get("accepted_count") or 0)
    return {
        "source_run_id": summary.get("source_run_id"),
        "attempt_count": attempt_count,
        "accepted_count": accepted_count,
        "rejected_count": int(summary.get("rejected_count") or 0),
        "skipped_count": int(summary.get("skipped_count") or 0),
        "error_count": int(summary.get("error_count") or 0),
        "timeout_count": int(summary.get("timeout_count") or 0),
        "missing_response_count": int(summary.get("missing_response_count") or 0),
        "accepted_yield": _ratio(accepted_count, attempt_count),
    }


def _attempt_summary(attempts: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = Counter(str(row.get("judge_status") or "unknown") for row in attempts)
    attempt_count = len(attempts)
    accepted_count = statuses["accepted"]
    return {
        "attempt_count": attempt_count,
        "accepted_count": accepted_count,
        "accepted_yield": _ratio(accepted_count, attempt_count),
        "judge_status_counts": dict(sorted(statuses.items())),
        "unique_problem_count": len(
            {str(row.get("problem_key")) for row in attempts if row.get("problem_key")}
        ),
    }


def _source_balance(sampled_manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    selected_by_stratum = sampled_manifest.get("selected_by_stratum") or {}
    total = int(
        sampled_manifest.get("selected_count") or sum(selected_by_stratum.values()) or 0
    )
    balance: dict[str, dict[str, Any]] = {}
    for stratum in STRATA:
        count = int(selected_by_stratum.get(stratum) or 0)
        balance[stratum] = {
            "selected_count": count,
            "share": _ratio(count, total),
        }
    return balance


def _error_mix(summary: dict[str, Any], attempts: list[dict[str, Any]]) -> dict[str, Any]:
    if summary:
        counts = {
            "rejected": int(summary.get("rejected_count") or 0),
            "skipped": int(summary.get("skipped_count") or 0),
            "error": int(summary.get("error_count") or 0),
            "timeout": int(summary.get("timeout_count") or 0),
            "missing_response": int(summary.get("missing_response_count") or 0),
        }
    else:
        status_counts = Counter(str(row.get("judge_status") or "unknown") for row in attempts)
        counts = {
            "rejected": status_counts["rejected"],
            "skipped": status_counts["skipped"],
            "error": status_counts["error"],
            "timeout": status_counts["timeout"],
            "missing_response": 0,
        }
    kinds = Counter(str(row.get("judge_error_kind") or "none") for row in attempts)
    return {
        "counts": counts,
        "top_error_kinds": dict(kinds.most_common(8)),
    }


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 6)
