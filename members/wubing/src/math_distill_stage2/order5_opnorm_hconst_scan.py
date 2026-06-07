from __future__ import annotations

import base64
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from math_distill_stage2.order5_opnorm_match_collapse import (
    has_mul_roots,
    has_source_constancy_variable,
    render_first_hconst_match_collapse_certificate,
)
from math_distill_stage2.order5_pair_space import ids_to_pair_index


CANDIDATE_KEY = "true.proof.templatecheck.opnorm.hconst_match_collapse.compiler_probe.v1"


def load_equations(path: Path) -> dict[int, str]:
    return {
        index + 1: line.strip()
        for index, line in enumerate(path.read_text(encoding="utf-8").splitlines())
        if line.strip()
    }


def iter_jsonl(path: Path):
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            yield json.loads(line)


def scan_sample(
    sample: Path,
    *,
    equations: dict[int, str],
    require_mul_roots: bool,
    max_candidates_per_pair: int,
    include_code: bool = False,
    max_records: int = 0,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    stats: Counter[str] = Counter()
    hit_buckets: Counter[str] = Counter()
    hit_strata: Counter[str] = Counter()
    hits: list[dict[str, Any]] = []
    for row in iter_jsonl(sample):
        stats["sample_total_count"] += 1
        if max_records and stats["sample_total_count"] > max_records:
            break

        eq1_id, eq2_id = pair_ids(row)
        source_equation = equation_text(row, "source", eq1_id, equations)
        target_equation = equation_text(row, "target", eq2_id, equations)
        if source_equation is None or target_equation is None:
            stats["missing_equation_text_count"] += 1
            continue
        if not has_source_constancy_variable(source_equation):
            stats["source_constancy_prefilter_rejected_count"] += 1
            continue
        if require_mul_roots and not (
            has_mul_roots(source_equation) and has_mul_roots(target_equation)
        ):
            stats["mul_roots_prefilter_rejected_count"] += 1
            continue

        stats["compiler_scan_count"] += 1
        code = render_first_hconst_match_collapse_certificate(
            source_equation,
            target_equation,
            max_candidates=max_candidates_per_pair,
        )
        if code is None:
            continue

        stats["compiler_hit_count"] += 1
        bucket = str(row.get("shape_bucket") or "")
        stratum = str(row.get("stratum") or "")
        hit_buckets[bucket] += 1
        hit_strata[stratum] += 1
        record = {
            "schema_version": 1,
            "candidate_key": CANDIDATE_KEY,
            "eq1_id": eq1_id,
            "eq2_id": eq2_id,
            "pair_index": row.get("pair_index"),
            "shape_bucket": bucket,
            "stratum": stratum,
            "equation1": source_equation,
            "equation2": target_equation,
            "code_sha256": hashlib.sha256(code.encode("utf-8")).hexdigest(),
        }
        if include_code:
            record["code"] = code
        hits.append(record)

    summary_bits = summarize_hits(hits)
    summary_bits["stats"] = dict(stats)
    return hits, summary_bits


def summarize_hits(hits: list[dict[str, Any]]) -> dict[str, Any]:
    hit_buckets: Counter[str] = Counter()
    hit_strata: Counter[str] = Counter()
    for hit in hits:
        hit_buckets[str(hit.get("shape_bucket") or "")] += 1
        hit_strata[str(hit.get("stratum") or "")] += 1
    return {
        "hit_stratum_counts": dict(hit_strata),
        "top_hit_shape_buckets": [
            {"shape_bucket": bucket, "hit_count": count}
            for bucket, count in hit_buckets.most_common(30)
        ],
    }


def explicit_hits_delta_from_profile(
    profile: dict[str, Any],
    hits: list[dict[str, Any]],
    *,
    verdict: bool,
) -> dict[str, Any]:
    law_count = int(profile["law_count"])
    pairs = {
        (
            int(hit["eq1_id"]),
            int(hit["eq2_id"]),
            int(hit["pair_index"])
            if hit.get("pair_index") is not None
            else ids_to_pair_index(
                int(hit["eq1_id"]),
                int(hit["eq2_id"]),
                law_count=law_count,
            ),
        )
        for hit in hits
    }
    same_profile = profile["verdict_profiles"][str(verdict).lower()]
    opposite_profile = profile["verdict_profiles"][str(not verdict).lower()]
    same_covered = covered_pairs_from_profile(same_profile, pairs, law_count=law_count)
    opposite_covered = covered_pairs_from_profile(
        opposite_profile,
        pairs,
        law_count=law_count,
    )
    raw_coverage = len(pairs)
    same_verdict_overlap = len(same_covered)
    opposite_verdict_overlap = len(opposite_covered)
    conflict_increment = len(opposite_covered - same_covered)
    union_increment = raw_coverage - same_verdict_overlap
    deterministic_increment = union_increment - conflict_increment
    total_deterministic_increment = union_increment - (2 * conflict_increment)
    return {
        "schema_version": 1,
        "verdict": verdict,
        "coverage_kind": "explicit_pairs",
        "raw_coverage": raw_coverage,
        "same_verdict_overlap": same_verdict_overlap,
        "opposite_verdict_overlap": opposite_verdict_overlap,
        "conflict_increment": conflict_increment,
        "union_increment": union_increment,
        "candidate_verdict_deterministic_increment": deterministic_increment,
        "total_deterministic_increment": total_deterministic_increment,
        "unresolved_delta": -total_deterministic_increment,
    }


def covered_pairs_from_profile(
    verdict_profile: dict[str, Any],
    pairs: set[tuple[int, int, int]],
    *,
    law_count: int,
) -> set[tuple[int, int, int]]:
    remaining = set(pairs)
    covered: set[tuple[int, int, int]] = set()
    pairs_by_source: dict[int, list[tuple[int, int, int]]] = {}
    bitset_cache: dict[tuple[int, str], bytes] = {}
    for pair in pairs:
        pairs_by_source.setdefault(pair[0], []).append(pair)

    for group in verdict_profile.get("source_target_groups", []):
        matched_source_ids = _matched_sources(
            group,
            pairs_by_source,
            law_count=law_count,
            bitset_cache=bitset_cache,
        )
        if not matched_source_ids:
            continue
        for source_id in matched_source_ids:
            for pair in pairs_by_source[source_id]:
                if pair in remaining and payload_contains(
                    group,
                    "target",
                    pair[1],
                    law_count=law_count,
                    bitset_cache=bitset_cache,
                ):
                    covered.add(pair)
                    remaining.discard(pair)
        if not remaining:
            return covered

    explicit_groups = verdict_profile.get("explicit_source_target_groups", [])
    for group in explicit_groups:
        source_id = int(group["source_id"])
        if source_id not in pairs_by_source:
            continue
        for pair in pairs_by_source[source_id]:
            if pair in remaining and payload_contains(
                group,
                "target",
                pair[1],
                law_count=law_count,
                bitset_cache=bitset_cache,
            ):
                covered.add(pair)
                remaining.discard(pair)
        if not remaining:
            break
    return covered


def _matched_sources(
    group: dict[str, Any],
    pairs_by_source: dict[int, list[tuple[int, int, int]]],
    *,
    law_count: int,
    bitset_cache: dict[tuple[int, str], bytes],
) -> list[int]:
    if "source_ids" in group:
        return [
            int(source_id)
            for source_id in group["source_ids"]
            if int(source_id) in pairs_by_source
        ]
    return [
        source_id
        for source_id in pairs_by_source
        if payload_contains(
            group,
            "source",
            source_id,
            law_count=law_count,
            bitset_cache=bitset_cache,
        )
    ]


def payload_contains(
    payload: dict[str, Any],
    prefix: str,
    eq_id: int,
    *,
    law_count: int,
    bitset_cache: dict[tuple[int, str], bytes] | None = None,
) -> bool:
    ids_key = f"{prefix}_ids"
    if ids_key in payload:
        return int(eq_id) in {int(value) for value in payload[ids_key]}
    cache_key = (id(payload), prefix)
    raw: bytes
    if bitset_cache is not None and cache_key in bitset_cache:
        raw = bitset_cache[cache_key]
    else:
        raw = base64.b64decode(str(payload[f"{prefix}_bitset_base64"]).encode("ascii"))
        if bitset_cache is not None:
            bitset_cache[cache_key] = raw
    expected_length = (law_count + 7) // 8
    if len(raw) != expected_length:
        raise ValueError(f"{prefix} bitset must have {expected_length} bytes")
    bit_index = int(eq_id) - 1
    return bool(raw[bit_index // 8] & (1 << (bit_index % 8)))


def pair_ids(row: dict[str, Any]) -> tuple[int, int]:
    eq1_id = row.get("source_id", row.get("eq1_id"))
    eq2_id = row.get("target_id", row.get("eq2_id"))
    if eq1_id is None or eq2_id is None:
        raise ValueError(f"record is missing pair ids: {row}")
    return int(eq1_id), int(eq2_id)


def equation_text(
    row: dict[str, Any],
    side: str,
    eq_id: int,
    equations: dict[int, str],
) -> str | None:
    if side == "source":
        value = row.get("source_equation", row.get("equation1"))
    else:
        value = row.get("target_equation", row.get("equation2"))
    if isinstance(value, str) and value.strip():
        return value
    return equations.get(eq_id)
