from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


INCREMENT_KEYS = {
    "candidate_verdict_deterministic_increment",
    "cumulative_exact_current_false_union_increment",
    "current_union_increment",
    "estimated_union_increment",
    "exact_union_increment",
    "increment",
    "marginal_increment",
    "rank_best_increment",
    "best_increment",
    "total_exact_union_increment",
    "union_increment",
}

TEXT_STATUS_KEYS = {
    "affine_mod17_batch_status",
    "candidate_family",
    "candidate_key",
    "candidate_layer_decision",
    "candidate_status",
    "controller_action",
    "controller_decision",
    "decision",
    "formal_registry_merge",
    "interpretation",
    "next_highest_roi",
    "reason",
    "register_decision",
    "registry_status",
    "registry_status_recommendation",
    "remote_smoke_status",
    "soundness_status",
    "status",
}

PREFERRED_KEY_FIELDS = (
    "candidate_key",
    "candidate_family",
    "register_strategy_key",
    "controller_action",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rows.append(json.loads(line))
    return rows


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_info(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "path": str(path),
        "size_bytes": stat.st_size,
        "mtime_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
        "sha256": file_sha256(path),
    }


def walk_summary_values(
    value: Any,
    *,
    path: tuple[str, ...] = (),
    list_limit: int = 500,
) -> Iterable[tuple[tuple[str, ...], str | None, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = path + (str(key),)
            yield child_path, str(key), child
            yield from walk_summary_values(child, path=child_path, list_limit=list_limit)
    elif isinstance(value, list):
        for index, child in enumerate(value[:list_limit]):
            if isinstance(child, (dict, list)):
                yield from walk_summary_values(
                    child,
                    path=path + (str(index),),
                    list_limit=list_limit,
                )


def _first_string_for_keys(data: Any, keys: tuple[str, ...]) -> str | None:
    for _, key, value in walk_summary_values(data):
        if key in keys and isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _collect_status_text(data: Any) -> str:
    chunks: list[str] = []
    for _, key, value in walk_summary_values(data):
        if key in TEXT_STATUS_KEYS and isinstance(value, str):
            chunks.append(value)
        elif key == "notes" and isinstance(value, list):
            chunks.extend(str(item) for item in value[:20])
    return " ".join(chunks).lower()


def _collect_increment_metrics(data: Any) -> list[dict[str, Any]]:
    metrics: list[dict[str, Any]] = []
    for path, key, value in walk_summary_values(data):
        if key not in INCREMENT_KEYS:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        metrics.append(
            {
                "key": key,
                "path": ".".join(path),
                "value": int(value),
            }
        )
    metrics.sort(key=lambda item: item["value"], reverse=True)
    return metrics


def _collect_absorbed_candidate_summary_paths(data: Any) -> list[str]:
    if not isinstance(data, dict):
        return []
    absorbed_paths: set[str] = set()
    explicit_paths = data.get("absorbed_candidate_summary_paths") or data.get(
        "absorbed_summary_paths"
    )
    if isinstance(explicit_paths, list):
        for path in explicit_paths:
            if isinstance(path, str) and path.strip():
                absorbed_paths.add(path.strip())
    top_level_status = str(
        data.get("status")
        or data.get("current_review_status")
        or data.get("registry_status_recommendation")
        or ""
    )
    top_level_delta = (
        data.get("current_v26_delta")
        or data.get("current_delta")
        or data.get("delta_current_v26")
        or data.get("current_delta_against_v25")
        or data.get("current_delta_against_v24")
        or {}
    )
    if (
        _is_absorbing_rescore_status(top_level_status)
        and isinstance(top_level_delta, dict)
        and _delta_is_zero_conflict_noop(top_level_delta)
    ):
        source_summary_path = data.get("source_summary_path")
        if isinstance(source_summary_path, str) and source_summary_path.strip():
            absorbed_paths.add(source_summary_path.strip())

    rows = data.get("rows") or data.get("results")
    if not isinstance(rows, list):
        return sorted(absorbed_paths)

    for row in rows:
        if not isinstance(row, dict):
            continue
        status = str(row.get("status") or row.get("current_review_status") or "")
        if not _is_absorbing_rescore_status(status):
            continue
        summary_path = row.get("summary_path")
        if not isinstance(summary_path, str) or not summary_path.strip():
            continue
        delta = (
            row.get("current_v26_delta")
            or row.get("current_delta")
            or row.get("current_delta_against_v25")
            or row.get("current_delta_against_v24")
            or {}
        )
        if not isinstance(delta, dict):
            continue
        if _delta_is_zero_conflict_noop(delta):
            absorbed_paths.add(summary_path.strip())
    return sorted(absorbed_paths)


def _is_absorbing_rescore_status(status: str) -> bool:
    text = status.lower()
    return (
        "demoted_after_current_rescore" in text
        or "closed_fresh_subsumed" in text
        or "stale_or_subsumed_by_current_registry" in text
    )


def _delta_is_zero_conflict_noop(delta: dict[str, Any]) -> bool:
    increment = delta.get(
        "candidate_verdict_deterministic_increment",
        delta.get("total_deterministic_increment"),
    )
    return increment == 0 and delta.get("conflict_increment") == 0


def _is_controller_review_artifact(data: Any, path: Path) -> bool:
    if not isinstance(data, dict):
        return False
    if not path.name.startswith("controller_"):
        return False
    if not isinstance(data.get("controller_action"), str):
        return False
    if isinstance(data.get("candidate_key"), str):
        return False
    return (
        data.get("candidate_layer_only") is True
        or data.get("formal_registry_modified") is False
        or isinstance(data.get("output_paths"), dict)
        or isinstance(data.get("recommended_route_counts"), dict)
    )


def _is_selection_summary_artifact(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    return isinstance(data.get("selected_path"), str) and (
        isinstance(data.get("rank_path"), str)
        or isinstance(data.get("top_candidates"), list)
        or isinstance(data.get("positive_count"), int)
    )


def _collect_smoke_summary(data: Any) -> dict[str, Any]:
    observed: list[dict[str, Any]] = []
    dict_values: list[tuple[tuple[str, ...], dict[str, Any]]] = []
    if isinstance(data, dict):
        dict_values.append(((), data))
    for path, _, value in walk_summary_values(data):
        if not isinstance(value, dict):
            continue
        dict_values.append((path, value))
    for path, value in dict_values:
        for prefix in (
            "remote_smoke",
            "postmerge_remote_smoke",
            "summary_remote_smoke",
        ):
            accepted = value.get(f"{prefix}_accepted_count")
            total = value.get(f"{prefix}_total_count")
            if (
                isinstance(accepted, (int, float))
                and not isinstance(accepted, bool)
                and isinstance(total, (int, float))
                and not isinstance(total, bool)
            ):
                observed.append(
                    {
                        "path": ".".join(path + (prefix,)),
                        "accepted_count": int(accepted),
                        "total_count": int(total),
                        "all_accepted": int(total) > 0
                        and int(accepted) == int(total),
                        "rejected": int(accepted) < int(total),
                        "status_counts": {},
                        "error_code_counts": {},
                    }
                )
        if "total_count" not in value:
            continue
        accepted = value.get("accepted_count", value.get("accepted_count_total"))
        total = value.get("total_count")
        if isinstance(accepted, bool) or isinstance(total, bool):
            continue
        if not isinstance(accepted, (int, float)) or not isinstance(total, (int, float)):
            continue
        status_counts = value.get("status_counts") or {}
        error_code_counts = value.get("error_code_counts") or {}
        status_counts_lower = {
            str(key).lower(): int(count)
            for key, count in status_counts.items()
            if isinstance(count, int)
        }
        error_counts_lower = {
            str(key).lower(): int(count)
            for key, count in error_code_counts.items()
            if isinstance(count, int)
        }
        rejected_statuses = {
            key: count
            for key, count in status_counts_lower.items()
            if key not in {"accepted", "ok", "success"} and count > 0
        }
        rejected_errors = {
            key: count
            for key, count in error_counts_lower.items()
            if key and count > 0
        }
        observed.append(
            {
                "path": ".".join(path),
                "accepted_count": int(accepted),
                "total_count": int(total),
                "all_accepted": int(total) > 0 and int(accepted) == int(total),
                "rejected": int(accepted) < int(total)
                or bool(rejected_statuses)
                or bool(rejected_errors),
                "status_counts": status_counts,
                "error_code_counts": error_code_counts,
            }
        )

    accepted_runs = [item for item in observed if item["all_accepted"]]
    rejected_runs = [item for item in observed if item["rejected"]]
    return {
        "observed_run_count": len(observed),
        "all_accepted_observed": bool(accepted_runs),
        "rejection_observed": bool(rejected_runs),
        "max_accepted_count": max((item["accepted_count"] for item in observed), default=0),
        "max_total_count": max((item["total_count"] for item in observed), default=0),
        "accepted_runs": accepted_runs[:5],
        "rejected_runs": rejected_runs[:5],
    }


def classify_candidate(
    *,
    status_text: str,
    best_increment: int | None,
    smoke: dict[str, Any],
) -> str:
    text = status_text.lower()
    if (
        "subsumed" in text
        or "absorbed" in text
        or "already in register" in text
        or "closed_fresh_subsumed" in text
        or "formal_registry_merged" in text
        or "register_layer_merged" in text
    ):
        return "merged_or_subsumed"
    if (
        "partial scan" in text
        or "stopped_after_high_value_partial_scan" in text
        or "registry_support_review" in text
        or "requires registry support review" in text
    ):
        return "needs_review"
    if (
        "blocked" in text
        or "not_merge_ready" in text
        or "not accepted" in text
        or "not_accepted" in text
        or "incorrect" in text
        or "rejected" in text
        or "seedgate" in text
        or smoke["rejection_observed"]
    ) and ("certificate" in text or "smoke" in text or "direct_split" in text):
        return "certificate_blocked"
    if "affine_mod_probe.mod17" in text and not smoke["all_accepted_observed"]:
        return "certificate_blocked"
    if "parking" in text or "below_100k" in text:
        return "parking_lot"
    if "register_ready" in text or "register-ready" in text:
        return "register_ready"
    if best_increment is None:
        return "needs_review"
    if best_increment >= 1_000_000:
        if smoke["all_accepted_observed"]:
            return "register_ready"
        return "needs_smoke_or_merge_review"
    if best_increment >= 100_000:
        return "tail_candidate"
    return "parking_lot"


def summarize_candidate_file(path: Path) -> dict[str, Any]:
    try:
        data = read_json(path)
    except json.JSONDecodeError as exc:
        return {
            "path": str(path),
            "file_mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
            .replace(microsecond=0)
            .isoformat(),
            "parse_error": str(exc),
            "status": "parse_error",
        }

    metrics = _collect_increment_metrics(data)
    smoke = _collect_smoke_summary(data)
    absorbed_paths = _collect_absorbed_candidate_summary_paths(data)
    is_controller_review_artifact = _is_controller_review_artifact(data, path)
    is_selection_summary_artifact = _is_selection_summary_artifact(data)
    candidate_key = _first_string_for_keys(data, PREFERRED_KEY_FIELDS) or path.stem
    verdict = _first_string_for_keys(data, ("verdict",))
    status_text = _collect_status_text(data)
    best_increment = metrics[0]["value"] if metrics else None
    status = classify_candidate(
        status_text=status_text,
        best_increment=best_increment,
        smoke=smoke,
    )
    if absorbed_paths and "rescore" in status_text:
        status = "merged_or_subsumed"
    if (
        "demoted_after_current_rescore" in status_text
        and isinstance(data, dict)
        and isinstance(data.get("current_v26_delta"), dict)
        and data["current_v26_delta"].get("candidate_verdict_deterministic_increment")
        == 0
        and data["current_v26_delta"].get("conflict_increment") == 0
    ):
        status = "merged_or_subsumed"
    if is_controller_review_artifact:
        status = "merged_or_subsumed"
    if is_selection_summary_artifact and status not in {
        "certificate_blocked",
        "merged_or_subsumed",
    }:
        status = "needs_review"
    return {
        "path": str(path),
        "file_mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
        "candidate_key": candidate_key,
        "verdict": verdict,
        "status": status,
        "best_increment": best_increment,
        "top_increment_metrics": metrics[:5],
        "smoke": smoke,
        "status_text_sample": status_text[:500],
        "absorbed_candidate_summary_paths": absorbed_paths,
        "controller_review_artifact": is_controller_review_artifact,
        "selection_summary_artifact": is_selection_summary_artifact,
    }


def build_candidate_index(
    *,
    candidates_dir: Path,
    summary_glob: str = "*summary.json",
    limit: int | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    paths = sorted(
        candidates_dir.glob(summary_glob),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if limit is not None:
        paths = paths[:limit]
    rows = [summarize_candidate_file(path) for path in paths]
    rows.sort(
        key=lambda row: (
            row.get("best_increment") or -1,
            row.get("file_mtime_utc") or "",
        ),
        reverse=True,
    )
    status_counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("status"))
        status_counts[status] = status_counts.get(status, 0) + 1
    summary = {
        "schema_version": 1,
        "generated_at_utc": utc_now_iso(),
        "candidates_dir": str(candidates_dir),
        "summary_glob": summary_glob,
        "summary_file_count": len(rows),
        "status_counts": status_counts,
        "top_by_increment": [
            {
                "candidate_key": row.get("candidate_key"),
                "status": row.get("status"),
                "best_increment": row.get("best_increment"),
                "path": row.get("path"),
            }
            for row in rows[:20]
        ],
        "blocked_high_roi": [
            {
                "candidate_key": row.get("candidate_key"),
                "status": row.get("status"),
                "best_increment": row.get("best_increment"),
                "path": row.get("path"),
            }
            for row in rows
            if row.get("status") == "certificate_blocked"
            and (row.get("best_increment") or 0) >= 100_000
        ][:20],
    }
    return rows, summary


def _row_contains(row: dict[str, Any], needle: str) -> bool:
    haystack = " ".join(
        str(row.get(key) or "")
        for key in ("candidate_key", "path", "status", "status_text_sample")
    ).lower()
    return needle.lower() in haystack


def _is_stale_or_subsumed(row: dict[str, Any]) -> bool:
    text = " ".join(
        str(row.get(key) or "")
        for key in ("status", "status_text_sample", "candidate_key", "path")
    ).lower()
    stale_markers = (
        "already in register",
        "already_registered",
        "closed_fresh_subsumed",
        "duplicate",
        "formal_registry_merged",
        "merged_or_subsumed",
        "stale",
        "subsumed",
        "superseded",
    )
    return any(marker in text for marker in stale_markers)


def _canonical_strategy_key(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return re.sub(r"\.v\d+$", "", value.strip())


def _registered_strategy_key_set(mining_state: dict[str, Any]) -> set[str]:
    strategy_summary = mining_state.get("baseline", {}).get("strategies", {})
    keys = list(strategy_summary.get("active_strategy_keys", [])) + list(
        strategy_summary.get("absorbed_strategy_keys", [])
    )
    return {
        canonical
        for key in keys
        if (canonical := _canonical_strategy_key(key)) is not None
    }


def _is_registered_candidate(row: dict[str, Any], registered_keys: set[str]) -> bool:
    candidate_key = _canonical_strategy_key(row.get("candidate_key"))
    return candidate_key is not None and candidate_key in registered_keys


def _rescore_absorbed_path_set(rows: list[dict[str, Any]]) -> set[str]:
    absorbed_paths: set[str] = set()
    for row in rows:
        for path in row.get("absorbed_candidate_summary_paths") or []:
            if isinstance(path, str) and path.strip():
                absorbed_paths.add(path.strip())
    return absorbed_paths


def _queue_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_key": row.get("candidate_key"),
        "status": row.get("status"),
        "best_increment": row.get("best_increment"),
        "path": row.get("path"),
        "smoke": {
            "observed_run_count": (row.get("smoke") or {}).get("observed_run_count"),
            "all_accepted_observed": (row.get("smoke") or {}).get(
                "all_accepted_observed"
            ),
            "rejection_observed": (row.get("smoke") or {}).get("rejection_observed"),
            "max_accepted_count": (row.get("smoke") or {}).get("max_accepted_count"),
            "max_total_count": (row.get("smoke") or {}).get("max_total_count"),
        },
    }


def build_merge_review_queue(
    *,
    rows: list[dict[str, Any]],
    mining_state: dict[str, Any],
    main_gate: int = 1_000_000,
    tail_gate: int = 100_000,
) -> dict[str, Any]:
    sorted_rows = sorted(
        rows,
        key=lambda row: (
            row.get("best_increment") or -1,
            row.get("file_mtime_utc") or "",
        ),
        reverse=True,
    )
    registered_keys = _registered_strategy_key_set(mining_state)
    rescore_absorbed_paths = _rescore_absorbed_path_set(sorted_rows)
    stale_or_subsumed = [
        row
        for row in sorted_rows
        if _is_stale_or_subsumed(row)
        or _is_registered_candidate(row, registered_keys)
        or str(row.get("path") or "") in rescore_absorbed_paths
    ]
    active_rows = [
        row
        for row in sorted_rows
        if not _is_stale_or_subsumed(row)
        and not _is_registered_candidate(row, registered_keys)
        and str(row.get("path") or "") not in rescore_absorbed_paths
    ]
    postedge7_rows = [
        row
        for row in active_rows
        if _row_contains(row, "postedge7") and row.get("best_increment") is not None
    ]
    register_ready_main = [
        row
        for row in active_rows
        if row.get("status") == "register_ready"
        and (row.get("best_increment") or 0) >= main_gate
    ]
    needs_rescore_or_smoke_main = [
        row
        for row in active_rows
        if row.get("status") == "needs_smoke_or_merge_review"
        and (row.get("best_increment") or 0) >= main_gate
    ]
    certificate_blocked_high_roi = [
        row
        for row in active_rows
        if row.get("status") == "certificate_blocked"
        and (row.get("best_increment") or 0) >= tail_gate
    ]
    tail_candidates = [
        row
        for row in active_rows
        if row.get("status") == "tail_candidate"
        and tail_gate <= (row.get("best_increment") or 0) < main_gate
    ]
    parking_lot = [row for row in active_rows if row.get("status") == "parking_lot"]
    needs_metadata_review = [row for row in active_rows if row.get("status") == "needs_review"]
    baseline = mining_state.get("baseline", {}).get("coverage", {})
    active_goal_sessions = mining_state.get("active_goal_sessions", [])
    return {
        "schema_version": 1,
        "generated_at_utc": utc_now_iso(),
        "baseline": baseline,
        "active_goal_count": len(active_goal_sessions),
        "active_goal_sessions": [
            {
                "short_id": session.get("short_id"),
                "title": session.get("title"),
                "updated_at_utc": session.get("updated_at_utc"),
                "tokens_used": session.get("tokens_used"),
            }
            for session in active_goal_sessions
        ],
        "gates": {
            "main_gate": main_gate,
            "tail_gate": tail_gate,
        },
        "queue_counts": {
            "postedge7_controller_review": len(postedge7_rows),
            "register_ready_main": len(register_ready_main),
            "needs_rescore_or_smoke_main": len(needs_rescore_or_smoke_main),
            "certificate_blocked_high_roi": len(certificate_blocked_high_roi),
            "tail_candidates": len(tail_candidates),
            "parking_lot": len(parking_lot),
            "needs_metadata_review": len(needs_metadata_review),
            "stale_or_subsumed": len(stale_or_subsumed),
        },
        "queues": {
            "postedge7_controller_review": [_queue_row(row) for row in postedge7_rows[:20]],
            "register_ready_main": [_queue_row(row) for row in register_ready_main[:20]],
            "needs_rescore_or_smoke_main": [
                _queue_row(row) for row in needs_rescore_or_smoke_main[:20]
            ],
            "certificate_blocked_high_roi": [
                _queue_row(row) for row in certificate_blocked_high_roi[:20]
            ],
            "tail_candidates": [_queue_row(row) for row in tail_candidates[:20]],
            "parking_lot_top": [_queue_row(row) for row in parking_lot[:20]],
            "needs_metadata_review_recent": [
                _queue_row(row)
                for row in sorted(
                    needs_metadata_review,
                    key=lambda row: row.get("file_mtime_utc") or "",
                    reverse=True,
                )[:20]
            ],
            "stale_or_subsumed_top": [_queue_row(row) for row in stale_or_subsumed[:20]],
        },
        "recommendation": {
            "primary": (
                "review postedge7 first; do not start postedge8 or broad false mining until "
                "the full-summary baseline includes or rejects postedge7"
            ),
            "secondary": (
                "rescore register_ready/needs_smoke_or_merge_review rows against the current "
                "coverage profile before any registry merge"
            ),
            "blocked": (
                "treat affine_mod17 as a certificate/smoke debugging task, not as broad "
                "finite-model mining"
            ),
        },
    }


def render_merge_review_markdown(queue: dict[str, Any]) -> str:
    baseline = queue["baseline"]
    counts = queue["queue_counts"]
    if counts.get("postedge7_controller_review", 0):
        headline = (
            "当前不建议继续广撒网挖掘；先完成 `postedge7` 总控复核，"
            "再对 register-ready 与 needs-smoke 队列做 current baseline rescore。"
        )
        first_action = "先确认 `postedge7` full summary 是否已被正式 registry/coverage 吸收。"
    elif counts.get("register_ready_main", 0) == 0 and counts.get(
        "needs_rescore_or_smoke_main",
        0,
    ) == 0:
        headline = (
            "`postedge7` 已从待合并队列移除；当前没有 register-ready 或 "
            "needs-rescore/smoke 主线候选。"
        )
        first_action = (
            "主线 merge queue 已清空；下一步只处理 certificate-blocked、"
            "metadata review 或 tail batch，不直接合并 registry。"
        )
    elif counts.get("register_ready_main", 0) == 0 and counts.get(
        "needs_rescore_or_smoke_main",
        0,
    ):
        headline = (
            "`postedge7` 已从待合并队列移除；当前没有 register-ready 候选，"
            "下一步处理 needs-rescore/smoke 主线候选。"
        )
        first_action = (
            "`postedge7` 已被当前 registry/coverage 吸收；不要基于旧 "
            "postedge7 summary 重复合并。"
        )
    else:
        headline = (
            "`postedge7` 已从待合并队列移除；下一步应从 8 个主线 "
            "register-ready 候选开始做 current baseline rescore。"
        )
        first_action = (
            "`postedge7` 已被当前 registry/coverage 吸收；不要基于旧 "
            "postedge7 summary 重复合并。"
        )
    lines = [
        "# Order5 strategy merge review queue",
        "",
        "## 一句话结论",
        "",
        headline,
        "",
        "## 当前 baseline",
        "",
        f"- `total_pairs`: `{baseline.get('total_pairs')}`",
        f"- `deterministic_false_covered`: `{baseline.get('deterministic_false_covered')}`",
        f"- `deterministic_true_covered`: `{baseline.get('deterministic_true_covered')}`",
        f"- `unresolved_estimate`: `{baseline.get('unresolved_estimate')}`",
        f"- `conflict_count`: `{baseline.get('conflict_count')}`",
        f"- active goal sessions: `{queue['active_goal_count']}`",
        "",
        "## 队列计数",
        "",
    ]
    for key in (
        "postedge7_controller_review",
        "register_ready_main",
        "needs_rescore_or_smoke_main",
        "certificate_blocked_high_roi",
        "tail_candidates",
        "parking_lot",
        "needs_metadata_review",
        "stale_or_subsumed",
    ):
        lines.append(f"- `{key}`: `{counts.get(key, 0)}`")

    def add_table(title: str, rows: list[dict[str, Any]], limit: int = 10) -> None:
        lines.extend(["", f"## {title}", ""])
        if not rows:
            lines.append("无。")
            return
        lines.append("| candidate | status | increment | smoke | path |")
        lines.append("| --- | --- | ---: | --- | --- |")
        for row in rows[:limit]:
            smoke = row.get("smoke") or {}
            smoke_text = (
                f"{smoke.get('max_accepted_count')}/{smoke.get('max_total_count')}"
                if smoke.get("observed_run_count")
                else "none"
            )
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(row.get("candidate_key")),
                        str(row.get("status")),
                        f"`{row.get('best_increment')}`",
                        f"`{smoke_text}`",
                        f"`{row.get('path')}`",
                    ]
                )
                + " |"
            )

    queues = queue["queues"]
    add_table("postedge7 总控复核", queues["postedge7_controller_review"])
    add_table("主线 register-ready", queues["register_ready_main"])
    add_table("主线需 rescore/smoke", queues["needs_rescore_or_smoke_main"])
    add_table("高 ROI 但证书阻塞", queues["certificate_blocked_high_roi"])
    add_table("tail candidates", queues["tail_candidates"])

    lines.extend(
        [
            "",
            "## 建议动作",
            "",
            f"1. {first_action}",
            "2. 对主线候选只做 current profile delta rescore；不要直接相信旧 summary 的高分。",
            "3. `affine_mod17` 只进入 certificate/smoke debug，不再扩大 false finite-model 广搜。",
            "4. tail candidates 只在主线队列清空后批量处理，避免小增量频繁改 registry。",
            "",
        ]
    )
    return "\n".join(lines)


def summarize_strategies(strategies_path: Path) -> dict[str, Any]:
    strategies = read_json(strategies_path)
    counts_by_verdict: dict[str, int] = {}
    counts_by_mode: dict[str, int] = {}
    active_strategies = 0
    active_strategy_keys: list[str] = []
    absorbed_strategy_keys: list[str] = []
    max_priority = None
    for strategy in strategies:
        if strategy.get("deprecated"):
            continue
        active_strategies += 1
        if isinstance(strategy.get("strategy_key"), str):
            active_strategy_keys.append(strategy["strategy_key"])
        for key in (
            "absorbed_candidate_keys",
            "supersedes_strategy_ids",
            "template_component_candidate_keys",
        ):
            values = strategy.get(key)
            if not isinstance(values, list):
                continue
            absorbed_strategy_keys.extend(
                value for value in values if isinstance(value, str)
            )
        verdict = str(strategy.get("verdict"))
        mode = str(strategy.get("verification_mode") or strategy.get("coverage_kind"))
        counts_by_verdict[verdict] = counts_by_verdict.get(verdict, 0) + 1
        counts_by_mode[mode] = counts_by_mode.get(mode, 0) + 1
        priority = strategy.get("priority")
        if isinstance(priority, int):
            max_priority = priority if max_priority is None else max(max_priority, priority)
    return {
        "total_strategy_rows": len(strategies),
        "active_strategy_rows": active_strategies,
        "counts_by_verdict": counts_by_verdict,
        "counts_by_verification_mode": counts_by_mode,
        "max_priority": max_priority,
        "active_strategy_keys": sorted(active_strategy_keys),
        "absorbed_strategy_keys": sorted(
            {
                canonical
                for key in absorbed_strategy_keys
                if (canonical := _canonical_strategy_key(key)) is not None
            }
        ),
    }


def summarize_coverage(coverage_summary_path: Path) -> dict[str, Any]:
    data = read_json(coverage_summary_path)
    keys = (
        "coverage_scope",
        "includes_order4_source_to_order4_target",
        "source_target_excluded_block_count",
        "total_pairs",
        "deterministic_false_covered",
        "deterministic_true_covered",
        "unresolved_estimate",
        "conflict_count",
        "same_verdict_overlap",
        "raw_false_union_covered",
        "raw_true_union_covered",
    )
    return {key: data.get(key) for key in keys if key in data}


def read_active_goal_sessions(
    *,
    codex_state_sqlite: Path | None,
    cwd: Path | None,
) -> list[dict[str, Any]]:
    if codex_state_sqlite is None:
        return []
    sqlite_path = codex_state_sqlite.expanduser()
    if not sqlite_path.exists():
        return []
    try:
        connection = sqlite3.connect(str(sqlite_path))
    except sqlite3.Error:
        return []
    try:
        connection.row_factory = sqlite3.Row
        query = """
            SELECT
              g.thread_id,
              t.title,
              g.objective,
              g.status,
              g.token_budget,
              g.tokens_used,
              g.time_used_seconds,
              g.created_at_ms,
              g.updated_at_ms,
              t.cwd,
              t.rollout_path
            FROM thread_goals g
            JOIN threads t ON t.id = g.thread_id
            WHERE g.status = 'active'
        """
        params: list[Any] = []
        if cwd is not None:
            query += " AND t.cwd = ?"
            params.append(str(cwd))
        query += " ORDER BY g.updated_at_ms DESC"
        rows = connection.execute(query, params).fetchall()
    except sqlite3.Error:
        return []
    finally:
        connection.close()
    return [
        {
            "thread_id": row["thread_id"],
            "short_id": row["thread_id"][:8],
            "title": row["title"],
            "objective": row["objective"],
            "status": row["status"],
            "token_budget": row["token_budget"],
            "tokens_used": row["tokens_used"],
            "time_used_seconds": row["time_used_seconds"],
            "created_at_utc": datetime.fromtimestamp(
                row["created_at_ms"] / 1000,
                timezone.utc,
            )
            .replace(microsecond=0)
            .isoformat(),
            "updated_at_utc": datetime.fromtimestamp(
                row["updated_at_ms"] / 1000,
                timezone.utc,
            )
            .replace(microsecond=0)
            .isoformat(),
            "cwd": row["cwd"],
            "rollout_path": row["rollout_path"],
        }
        for row in rows
    ]


def build_mining_state(
    *,
    registry_dir: Path,
    candidate_index_summary: dict[str, Any],
    codex_state_sqlite: Path | None = None,
    cwd: Path | None = None,
) -> dict[str, Any]:
    coverage_summary_path = registry_dir / "coverage_summary.json"
    strategies_path = registry_dir / "strategies.json"
    active_goal_sessions = read_active_goal_sessions(
        codex_state_sqlite=codex_state_sqlite,
        cwd=cwd,
    )
    return {
        "schema_version": 1,
        "generated_at_utc": utc_now_iso(),
        "registry_dir": str(registry_dir),
        "baseline": {
            "coverage": summarize_coverage(coverage_summary_path),
            "coverage_file": file_info(coverage_summary_path),
            "strategies": summarize_strategies(strategies_path),
            "strategies_file": file_info(strategies_path),
        },
        "active_goal_sessions": active_goal_sessions,
        "candidate_index": {
            "summary_file_count": candidate_index_summary["summary_file_count"],
            "status_counts": candidate_index_summary["status_counts"],
            "top_by_increment": candidate_index_summary["top_by_increment"][:10],
            "blocked_high_roi": candidate_index_summary["blocked_high_roi"][:10],
        },
        "coordination": {
            "active_goal_count": len(active_goal_sessions),
            "merge_lock_recommended": len(active_goal_sessions) > 1,
            "recommended_controller_policy": (
                "keep_one_controller_session_for_registry_merge_and_full_summary"
            ),
            "candidate_sessions_should_write_only": (
                "data/processed/order5_strategy_registry/candidates"
            ),
            "full_summary_policy": (
                "use coverage-profile delta for quick gates; run full coverage summary at batch merge boundary"
            ),
            "next_focus": [
                "wait_for_or_import_postedge7_full_summary_before starting postedge8",
                "treat affine_mod17 as certificate/smoke debugging, not broad mining",
                "rescore old candidate summaries against the current baseline before merge decisions",
            ],
        },
    }


def default_registry_dir() -> Path:
    return Path("data/processed/order5_strategy_registry")


def default_codex_state_sqlite() -> Path:
    return Path(os.path.expanduser("~/.codex/state_5.sqlite"))
