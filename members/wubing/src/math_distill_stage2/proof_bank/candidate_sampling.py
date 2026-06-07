from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import gzip
import json
import math
from pathlib import Path
import random
from typing import Any, Iterable

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.proof_bank.keying import problem_key_from_equations
from math_distill_stage2.proof_bank.storage import content_addressed_path, write_json


STRATA = (
    "rejected_attempt_repair",
    "high_signal_failed_attempts",
    "unsolved_trace_or_timeout",
    "direct_order4_true_exploration",
)
DEFAULT_WEIGHTS = {
    "rejected_attempt_repair": 0.35,
    "high_signal_failed_attempts": 0.65,
    "unsolved_trace_or_timeout": 0.20,
    "direct_order4_true_exploration": 0.15,
}
RECOVERY_AFTER_ZERO_YIELD_WEIGHTS = {
    "rejected_attempt_repair": 0.25,
    "high_signal_failed_attempts": 0.35,
    "unsolved_trace_or_timeout": 0.15,
    "direct_order4_true_exploration": 0.25,
}
SAMPLING_STRATEGY_WEIGHTS = {
    "default": DEFAULT_WEIGHTS,
    "recovery-after-zero-yield": RECOVERY_AFTER_ZERO_YIELD_WEIGHTS,
}
SELECTOR_VERSION = "proof_bank_candidate_sampler_v1"


def sample_candidate_pool(
    *,
    bank: Path,
    output_pool: Path,
    output_manifest: Path,
    pool_id: str,
    seed: int,
    limit: int,
    high_signal_pools: list[Path],
    unsolved_pools: list[Path],
    order4_source: Path | None,
    repair_from_bank: bool = False,
    max_attempts_per_problem: int = 3,
    allow_existing_accepted: bool = False,
    sampling_strategy: str = "default",
    overwrite: bool = False,
) -> dict[str, Any]:
    if limit <= 0:
        raise ValueError("limit must be positive")
    if sampling_strategy not in SAMPLING_STRATEGY_WEIGHTS:
        options = ", ".join(sorted(SAMPLING_STRATEGY_WEIGHTS))
        raise ValueError(f"unknown sampling_strategy {sampling_strategy!r}; expected one of: {options}")
    if not overwrite and (output_pool.exists() or output_manifest.exists()):
        raise FileExistsError(f"refusing to overwrite existing pool artifacts: {output_pool}")

    stratum_weights = SAMPLING_STRATEGY_WEIGHTS[sampling_strategy]
    accepted_problem_keys = _accepted_problem_keys(bank) if not allow_existing_accepted else set()
    attempt_counts = _attempt_counts(bank)
    quotas = _allocate_quotas(
        limit,
        {
            "rejected_attempt_repair": repair_from_bank,
            "high_signal_failed_attempts": bool(high_signal_pools),
            "unsolved_trace_or_timeout": bool(unsolved_pools),
            "direct_order4_true_exploration": order4_source is not None,
        },
        stratum_weights=stratum_weights,
    )

    excluded = Counter()
    source_counts: dict[str, Any] = {}
    selected_by_stratum: dict[str, list[dict[str, Any]]] = {}
    remaining_by_stratum: dict[str, list[dict[str, Any]]] = {}

    if repair_from_bank:
        candidates = _load_repair_candidates(bank)
        source_counts["rejected_attempt_repair"] = {
            "input_rows": len(candidates),
            "paths": [str(bank / "attempts.jsonl"), str(bank / "problems.jsonl")],
        }
        eligible, counts = _filter_and_dedupe(
            candidates,
            accepted_problem_keys=accepted_problem_keys,
            attempt_counts=attempt_counts,
            max_attempts_per_problem=max_attempts_per_problem,
        )
        excluded.update(counts)
        selected, remaining = _weighted_pick(
            eligible,
            quotas.get("rejected_attempt_repair", 0),
            seed=f"{seed}:{pool_id}:rejected_attempt_repair",
        )
        selected_by_stratum["rejected_attempt_repair"] = selected
        remaining_by_stratum["rejected_attempt_repair"] = remaining

    for stratum, paths in (
        ("high_signal_failed_attempts", high_signal_pools),
        ("unsolved_trace_or_timeout", unsolved_pools),
    ):
        candidates = _load_process_candidates(paths, stratum)
        source_counts[stratum] = {"input_rows": len(candidates), "paths": [str(p) for p in paths]}
        eligible, counts = _filter_and_dedupe(
            candidates,
            accepted_problem_keys=accepted_problem_keys,
            attempt_counts=attempt_counts,
            max_attempts_per_problem=max_attempts_per_problem,
        )
        excluded.update(counts)
        selected, remaining = _weighted_pick(
            eligible,
            quotas.get(stratum, 0),
            seed=f"{seed}:{pool_id}:{stratum}",
        )
        selected_by_stratum[stratum] = selected
        remaining_by_stratum[stratum] = remaining

    direct_candidates: list[dict[str, Any]] = []
    if order4_source is not None:
        direct_quota = quotas.get("direct_order4_true_exploration", 0)
        direct_candidates, direct_source_counts = _sample_direct_order4_candidates(
            order4_source,
            pool_id=pool_id,
            seed=seed,
            sample_size=max(direct_quota * 8, direct_quota + 20),
        )
        source_counts["direct_order4_true_exploration"] = direct_source_counts
        eligible, counts = _filter_and_dedupe(
            direct_candidates,
            accepted_problem_keys=accepted_problem_keys,
            attempt_counts=attempt_counts,
            max_attempts_per_problem=max_attempts_per_problem,
        )
        excluded.update(counts)
        selected, remaining = _weighted_pick(
            eligible,
            direct_quota,
            seed=f"{seed}:{pool_id}:direct_order4_true_exploration",
        )
        selected_by_stratum["direct_order4_true_exploration"] = selected
        remaining_by_stratum["direct_order4_true_exploration"] = remaining

    selected_rows = _dedupe_preserving_order(_interleave_by_stratum(selected_by_stratum))
    if len(selected_rows) < limit:
        selected_keys = {_problem_key(row) for row in selected_rows}
        backfill_pool = [
            row
            for row in _flatten_by_stratum(remaining_by_stratum)
            if _problem_key(row) not in selected_keys
        ]
        backfill, _ = _weighted_pick(
            backfill_pool,
            limit - len(selected_rows),
            seed=f"{seed}:{pool_id}:backfill",
        )
        selected_rows.extend(backfill)

    selected_rows = selected_rows[:limit]
    selected_counts = Counter(str(row["source_candidate_stratum"]) for row in selected_rows)
    write_jsonl(output_pool, selected_rows)
    manifest = {
        "schema_version": 1,
        "selector_version": SELECTOR_VERSION,
        "pool_id": pool_id,
        "sampling_strategy": sampling_strategy,
        "seed": seed,
        "limit": limit,
        "selected_count": len(selected_rows),
        "selected_by_stratum": dict(sorted(selected_counts.items())),
        "stratum_weights": dict(stratum_weights),
        "bank": str(bank),
        "output_pool": str(output_pool),
        "source_counts": source_counts,
        "exclusion_rules": {
            "allow_existing_accepted": allow_existing_accepted,
            "max_attempts_per_problem": max_attempts_per_problem,
        },
        "excluded_accepted_count": excluded["accepted"],
        "excluded_attempt_ceiling_count": excluded["attempt_ceiling"],
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    write_json(output_manifest, manifest)
    return manifest


def _load_repair_candidates(bank: Path) -> list[dict[str, Any]]:
    problems_path = bank / "problems.jsonl"
    attempts_path = bank / "attempts.jsonl"
    if not problems_path.exists() or not attempts_path.exists():
        return []
    problems = {
        str(row["problem_key"]): row
        for row in read_jsonl(problems_path)
        if row.get("problem_key")
    }
    candidates: list[dict[str, Any]] = []
    for attempt in read_jsonl(attempts_path):
        if attempt.get("judge_status") not in {"rejected", "error", "timeout"}:
            continue
        problem_key = str(attempt.get("problem_key") or "")
        problem = problems.get(problem_key)
        if problem is None:
            continue
        candidate = _candidate_from_row(
            {
                "source_problem_id": problem.get("source_problem_id")
                or f"true_{problem.get('eq1_id')}_{problem.get('eq2_id')}",
                "source_dataset": problem.get("first_seen_dataset")
                or _first_source_dataset(problem)
                or "proof_bank",
                "source_datasets": problem.get("source_datasets"),
                "eq1_id": problem.get("eq1_id"),
                "eq2_id": problem.get("eq2_id"),
                "equation1": problem["equation1"],
                "equation2": problem["equation2"],
                "problem_key": problem_key,
                "priority_score": _repair_priority(attempt),
                "external_trace_available": True,
                "external_trace_family": "previous_rejected_certificate_attempt",
            },
            stratum="rejected_attempt_repair",
            source_path=attempts_path,
        )
        candidate.update(
            {
                "source_attempt_id": attempt.get("attempt_id"),
                "previous_judge_status": attempt.get("judge_status"),
                "previous_official_judge_status": attempt.get("official_judge_status"),
                "previous_judge_error_kind": attempt.get("judge_error_kind"),
                "previous_judge_error_subkind": attempt.get("judge_error_subkind"),
                "previous_judge_error_summary": attempt.get("judge_error_summary"),
                "previous_proof_body_sha256": attempt.get("proof_body_sha256"),
                "previous_certificate_sha256": attempt.get("certificate_sha256"),
            }
        )
        excerpt = _proof_body_excerpt(bank, attempt.get("proof_body_sha256"))
        if excerpt:
            candidate["previous_proof_body_excerpt"] = excerpt
        candidates.append(candidate)
    return candidates


def _first_source_dataset(problem: dict[str, Any]) -> str | None:
    sources = problem.get("source_datasets")
    if isinstance(sources, list) and sources:
        return str(sources[0])
    return None


def _repair_priority(attempt: dict[str, Any]) -> int:
    kind = str(attempt.get("judge_error_kind") or "unknown")
    kind_bonus = {
        "lean_parse_error": 160,
        "lean_type_error": 140,
        "lean_tactic_failure": 130,
        "unknown": 90,
        "lean_timeout": 40,
    }.get(kind, 70)
    proof_bonus = 20 if attempt.get("proof_body_sha256") else 0
    return 500 + kind_bonus + proof_bonus


def _proof_body_excerpt(bank: Path, sha256: Any, *, max_chars: int = 1800) -> str | None:
    if not isinstance(sha256, str) or len(sha256) != 64:
        return None
    path = content_addressed_path(bank, "proof_bodies", sha256, ".lean")
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n-- excerpt truncated"


def _load_process_candidates(paths: list[Path], stratum: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        for row in read_jsonl(path):
            if row.get("expected_verdict") is not True:
                continue
            rows.append(_candidate_from_row(row, stratum=stratum, source_path=path))
    return rows


def _candidate_from_row(row: dict[str, Any], *, stratum: str, source_path: Path | None) -> dict[str, Any]:
    candidate = dict(row)
    candidate["expected_verdict"] = True
    candidate["source_candidate_stratum"] = stratum
    if source_path is not None:
        candidate["source_candidate_pool"] = str(source_path)
    candidate.setdefault("priority_score", 0)
    candidate.setdefault("external_trace_available", False)
    return candidate


def _sample_direct_order4_candidates(
    source: Path,
    *,
    pool_id: str,
    seed: int,
    sample_size: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rng = random.Random(f"{seed}:{pool_id}:direct-order4-reservoir")
    reservoir: list[dict[str, Any]] = []
    true_seen = 0
    scanned_rows = 0
    shard_paths = _order4_shard_paths(source)
    for shard_path in shard_paths:
        for row in _iter_jsonl(shard_path):
            scanned_rows += 1
            if row.get("answer") is not True:
                continue
            true_seen += 1
            if len(reservoir) < sample_size:
                reservoir.append(row)
                continue
            replace_index = rng.randrange(true_seen)
            if replace_index < sample_size:
                reservoir[replace_index] = row

    candidates = [
        _candidate_from_row(
            {
                "source_problem_id": str(row.get("id") or f"true_{row.get('eq1_id')}_{row.get('eq2_id')}"),
                "source_dataset": "order4_implication_problems",
                "eq1_id": row.get("eq1_id"),
                "eq2_id": row.get("eq2_id"),
                "equation1": row["equation1"],
                "equation2": row["equation2"],
                "priority_score": 0,
                "external_trace_available": False,
            },
            stratum="direct_order4_true_exploration",
            source_path=None,
        )
        for row in reservoir
    ]
    return candidates, {
        "source": str(source),
        "shards": [str(path) for path in shard_paths],
        "scanned_rows": scanned_rows,
        "true_seen": true_seen,
        "reservoir_size": len(reservoir),
    }


def _filter_and_dedupe(
    rows: list[dict[str, Any]],
    *,
    accepted_problem_keys: set[str],
    attempt_counts: Counter[str],
    max_attempts_per_problem: int,
) -> tuple[list[dict[str, Any]], Counter[str]]:
    excluded: Counter[str] = Counter()
    by_problem_key: dict[str, dict[str, Any]] = {}
    for row in rows:
        problem_key = _problem_key(row)
        if problem_key in accepted_problem_keys:
            excluded["accepted"] += 1
            continue
        if attempt_counts[problem_key] >= max_attempts_per_problem:
            excluded["attempt_ceiling"] += 1
            continue
        current = by_problem_key.get(problem_key)
        if current is None or _priority(row) > _priority(current):
            row = dict(row)
            row["problem_key"] = problem_key
            by_problem_key[problem_key] = row
    return sorted(by_problem_key.values(), key=_problem_key), excluded


def _weighted_pick(
    rows: list[dict[str, Any]],
    count: int,
    *,
    seed: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if count <= 0 or not rows:
        return [], rows
    rng = random.Random(seed)
    scored: list[tuple[float, str, dict[str, Any]]] = []
    for row in rows:
        weight = max(_priority(row), 0.0) + 1.0
        # Efraimidis-Spirakis weighted sample key.
        key = math.log(max(rng.random(), 1e-12)) / weight
        scored.append((key, _problem_key(row), row))
    scored.sort(reverse=True)
    selected_keys = {problem_key for _, problem_key, _ in scored[:count]}
    selected = [row for _, _, row in scored[:count]]
    remaining = [row for _, problem_key, row in scored[count:] if problem_key not in selected_keys]
    return selected, remaining


def _allocate_quotas(
    limit: int,
    available: dict[str, bool],
    *,
    stratum_weights: dict[str, float],
) -> dict[str, int]:
    active_weights = {name: stratum_weights[name] for name in STRATA if available.get(name)}
    if not active_weights:
        return {}
    weight_total = sum(active_weights.values())
    raw = {name: limit * weight / weight_total for name, weight in active_weights.items()}
    quotas = {name: int(round(value)) for name, value in raw.items()}
    while sum(quotas.values()) > limit:
        name = max(quotas, key=lambda key: (quotas[key], -raw[key]))
        quotas[name] -= 1
    while sum(quotas.values()) < limit:
        name = max(raw, key=lambda key: (raw[key] - quotas[key], active_weights[key]))
        quotas[name] += 1
    return quotas


def _flatten_by_stratum(rows_by_stratum: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for stratum in STRATA:
        rows.extend(rows_by_stratum.get(stratum, []))
    return rows


def _dedupe_preserving_order(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for row in rows:
        problem_key = _problem_key(row)
        if problem_key in seen:
            continue
        seen.add(problem_key)
        deduped.append(row)
    return deduped


def _interleave_by_stratum(rows_by_stratum: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    queues = {stratum: list(rows_by_stratum.get(stratum, [])) for stratum in STRATA}
    while any(queues.values()):
        for stratum in STRATA:
            if queues[stratum]:
                rows.append(queues[stratum].pop(0))
    return rows


def _accepted_problem_keys(bank: Path) -> set[str]:
    path = bank / "accepted.jsonl"
    if not path.exists():
        return set()
    return {
        str(row["problem_key"])
        for row in read_jsonl(path)
        if row.get("certificate_kind") == "true_proof" and row.get("problem_key")
    }


def _attempt_counts(bank: Path) -> Counter[str]:
    path = bank / "attempts.jsonl"
    counts: Counter[str] = Counter()
    if not path.exists():
        return counts
    for row in read_jsonl(path):
        if row.get("problem_key"):
            counts[str(row["problem_key"])] += 1
    return counts


def _problem_key(row: dict[str, Any]) -> str:
    if row.get("problem_key"):
        return str(row["problem_key"])
    return problem_key_from_equations(str(row["equation1"]), str(row["equation2"]))


def _priority(row: dict[str, Any]) -> float:
    try:
        return float(row.get("priority_score") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _order4_shard_paths(source: Path) -> list[Path]:
    if source.is_file():
        return [source]
    manifest = source / "manifest.json"
    if manifest.exists():
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        shards = payload.get("shards") or []
        paths = [source / str(row["path"]) for row in shards if row.get("path")]
        if paths:
            return paths
    return sorted(source.glob("*.jsonl")) + sorted(source.glob("*.jsonl.gz"))


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                yield json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON at {path}:{line_number}") from exc
