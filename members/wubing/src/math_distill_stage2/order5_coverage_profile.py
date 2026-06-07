from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Iterable, Sequence

from math_distill_stage2.order5_pair_space import pair_index_to_ids
from math_distill_stage2.order5_strategy_registry import (
    CompilerPairIndexesRule,
    CoverageRule,
    ExplicitPairsRule,
    Order5StrategyRegistry,
    SourceTargetSetsRule,
    _decode_ids_bitset,
    _encode_ids_bitset,
    _targets_for_source_signature,
)


_SPARSE_ID_LIST_THRESHOLD = 1024


def build_coverage_profile(registry: Order5StrategyRegistry) -> dict:
    started_at = time.perf_counter()
    active_strategies = [
        strategy for strategy in registry.strategies if not strategy.deprecated
    ]
    verdict_profiles = {}
    for verdict in (False, True):
        rules = [
            strategy.coverage_rule
            for strategy in active_strategies
            if strategy.verdict is verdict
        ]
        verdict_profiles[str(verdict).lower()] = _build_verdict_profile(
            rules,
            law_count=registry.law_count,
        )
    return {
        "schema_version": 3,
        "profile_kind": "order5_union_source_target_groups",
        "law_count": registry.law_count,
        "verdict_profiles": verdict_profiles,
        "timings_seconds": {
            "build_profile": time.perf_counter() - started_at,
        },
    }


def write_coverage_profile(profile: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n")


def read_coverage_profile(path: Path) -> dict:
    return json.loads(path.read_text())


def covered_targets_by_source_from_profile(
    profile: dict,
    *,
    verdict: bool,
    source_ids: Iterable[int],
) -> dict[int, frozenset[int]]:
    law_count = int(profile["law_count"])
    verdict_profile = profile["verdict_profiles"][str(verdict).lower()]
    return _profile_targets_by_source(
        verdict_profile,
        frozenset(int(source_id) for source_id in source_ids),
        law_count=law_count,
    )


def coverage_delta_summary_from_profile(
    profile: dict,
    candidate_rule: CoverageRule,
    *,
    verdict: bool,
    exact_pair_threshold: int = 1_000_000,
) -> dict:
    law_count = int(profile["law_count"])
    raw_coverage = candidate_rule.coverage_count()
    if raw_coverage > exact_pair_threshold:
        raise ValueError(
            "candidate coverage "
            f"{raw_coverage} exceeds exact_pair_threshold {exact_pair_threshold}"
        )

    candidate_sources = _candidate_source_ids(candidate_rule, law_count=law_count)
    same_profile = profile["verdict_profiles"][str(verdict).lower()]
    opposite_profile = profile["verdict_profiles"][str(not verdict).lower()]
    same_targets_by_source = _profile_targets_by_source(
        same_profile,
        candidate_sources,
        law_count=law_count,
    )
    opposite_targets_by_source = _profile_targets_by_source(
        opposite_profile,
        candidate_sources,
        law_count=law_count,
    )

    same_verdict_overlap = 0
    opposite_verdict_overlap = 0
    conflict_increment = 0
    for eq1_id, eq2_id in candidate_rule.iter_covered_pairs():
        same_covered = eq2_id in same_targets_by_source.get(eq1_id, frozenset())
        opposite_covered = eq2_id in opposite_targets_by_source.get(
            eq1_id,
            frozenset(),
        )
        if same_covered:
            same_verdict_overlap += 1
        if opposite_covered:
            opposite_verdict_overlap += 1
        if opposite_covered and not same_covered:
            conflict_increment += 1

    union_increment = raw_coverage - same_verdict_overlap
    candidate_verdict_deterministic_increment = union_increment - conflict_increment
    total_deterministic_increment = union_increment - (2 * conflict_increment)
    return {
        "schema_version": 1,
        "verdict": verdict,
        "coverage_kind": candidate_rule.coverage_kind,
        "raw_coverage": raw_coverage,
        "same_verdict_overlap": same_verdict_overlap,
        "opposite_verdict_overlap": opposite_verdict_overlap,
        "conflict_increment": conflict_increment,
        "union_increment": union_increment,
        "candidate_verdict_deterministic_increment": (
            candidate_verdict_deterministic_increment
        ),
        "total_deterministic_increment": total_deterministic_increment,
        "unresolved_delta": -total_deterministic_increment,
    }


def source_target_delta_summary_from_profile(
    profile: dict,
    *,
    source_ids: Iterable[int],
    target_ids: Iterable[int],
    verdict: bool,
    excluded_blocks: Sequence[tuple[Iterable[int], Iterable[int]]] = (),
) -> dict:
    """Compute source/target-set delta without iterating every covered pair."""

    law_count = int(profile["law_count"])
    candidate_rule = SourceTargetSetsRule(
        source_ids=frozenset(int(source_id) for source_id in source_ids),
        target_ids=frozenset(int(target_id) for target_id in target_ids),
        excluded_blocks=tuple(
            (
                frozenset(int(source_id) for source_id in excluded_sources),
                frozenset(int(target_id) for target_id in excluded_targets),
            )
            for excluded_sources, excluded_targets in excluded_blocks
        ),
    )
    candidate_sources = candidate_rule.source_ids
    same_profile = profile["verdict_profiles"][str(verdict).lower()]
    opposite_profile = profile["verdict_profiles"][str(not verdict).lower()]
    same_targets_by_source = _profile_targets_by_source(
        same_profile,
        candidate_sources,
        law_count=law_count,
    )
    opposite_targets_by_source = _profile_targets_by_source(
        opposite_profile,
        candidate_sources,
        law_count=law_count,
    )

    same_verdict_overlap = 0
    opposite_verdict_overlap = 0
    conflict_increment = 0
    empty_targets: frozenset[int] = frozenset()
    base_target_ids = candidate_rule.target_ids
    overlap_cache: dict[tuple[int, int, int], tuple[int, int, int]] = {}
    for source_id in sorted(candidate_sources):
        effective_target_ids = _effective_targets_for_source(
            source_id,
            base_target_ids,
            candidate_rule.excluded_blocks,
        )
        same_targets = same_targets_by_source.get(source_id, empty_targets)
        opposite_targets = opposite_targets_by_source.get(source_id, empty_targets)
        cache_key = (
            (id(effective_target_ids), id(same_targets), id(opposite_targets))
            if effective_target_ids is base_target_ids
            else None
        )
        cached_counts = overlap_cache.get(cache_key) if cache_key is not None else None
        if cached_counts is None:
            same_overlap = len(effective_target_ids & same_targets)
            opposite_targets_in_candidate = effective_target_ids & opposite_targets
            opposite_overlap = len(opposite_targets_in_candidate)
            conflict_overlap = len(opposite_targets_in_candidate - same_targets)
            cached_counts = (same_overlap, opposite_overlap, conflict_overlap)
            if cache_key is not None:
                overlap_cache[cache_key] = cached_counts
        same_overlap, opposite_overlap, conflict_overlap = cached_counts
        same_verdict_overlap += same_overlap
        opposite_verdict_overlap += opposite_overlap
        conflict_increment += conflict_overlap

    raw_coverage = candidate_rule.coverage_count()
    union_increment = raw_coverage - same_verdict_overlap
    candidate_verdict_deterministic_increment = union_increment - conflict_increment
    total_deterministic_increment = union_increment - (2 * conflict_increment)
    return {
        "schema_version": 1,
        "verdict": verdict,
        "coverage_kind": candidate_rule.coverage_kind,
        "raw_coverage": raw_coverage,
        "same_verdict_overlap": same_verdict_overlap,
        "opposite_verdict_overlap": opposite_verdict_overlap,
        "conflict_increment": conflict_increment,
        "union_increment": union_increment,
        "candidate_verdict_deterministic_increment": (
            candidate_verdict_deterministic_increment
        ),
        "total_deterministic_increment": total_deterministic_increment,
        "unresolved_delta": -total_deterministic_increment,
    }


def _build_verdict_profile(
    rules: Sequence[CoverageRule],
    *,
    law_count: int,
) -> dict:
    source_target_rules = [
        rule for rule in rules if isinstance(rule, SourceTargetSetsRule)
    ]
    pair_index_rules = [
        rule
        for rule in rules
        if isinstance(rule, (ExplicitPairsRule, CompilerPairIndexesRule))
    ]
    source_target_groups = [
        {
            "source_count": len(source_ids),
            "target_count": len(target_ids),
            **_encode_ids_payload(
                "source",
                source_ids,
                law_count=law_count,
            ),
            **_encode_ids_payload(
                "target",
                target_ids,
                law_count=law_count,
            ),
        }
        for source_ids, target_ids in _source_target_union_groups(
            source_target_rules,
        )
    ]
    explicit_targets_by_source: dict[int, set[int]] = {}
    for rule in pair_index_rules:
        for pair_index in rule.pair_indexes:
            eq1_id, eq2_id = pair_index_to_ids(pair_index, law_count=law_count)
            explicit_targets_by_source.setdefault(eq1_id, set()).add(eq2_id)
    explicit_source_target_groups = [
        {
            "source_id": source_id,
            "target_count": len(target_ids),
            **_encode_ids_payload(
                "target",
                target_ids,
                law_count=law_count,
            ),
        }
        for source_id, target_ids in sorted(explicit_targets_by_source.items())
    ]
    explicit_pair_count = sum(
        len(target_ids) for target_ids in explicit_targets_by_source.values()
    )
    return {
        "source_target_group_count": len(source_target_groups),
        "source_target_groups": source_target_groups,
        "explicit_pair_count": explicit_pair_count,
        "explicit_source_count": len(explicit_source_target_groups),
        "explicit_source_target_groups": explicit_source_target_groups,
    }


def _source_target_union_groups(
    rules: Sequence[SourceTargetSetsRule],
) -> list[tuple[frozenset[int], frozenset[int]]]:
    if not rules:
        return []
    source_groups: dict[tuple[tuple[int, tuple[int, ...]], ...], set[int]] = {}
    all_sources = frozenset().union(*(rule.source_ids for rule in rules))
    for source_id in all_sources:
        signature: list[tuple[int, tuple[int, ...]]] = []
        for rule_index, rule in enumerate(rules):
            if source_id not in rule.source_ids:
                continue
            excluded_block_indexes = tuple(
                block_index
                for block_index, (block_sources, _) in enumerate(rule.excluded_blocks)
                if source_id in block_sources
            )
            signature.append((rule_index, excluded_block_indexes))
        if signature:
            source_groups.setdefault(tuple(signature), set()).add(source_id)
    return [
        (frozenset(source_ids), _targets_for_source_signature(signature, rules))
        for signature, source_ids in source_groups.items()
    ]


def _candidate_source_ids(
    candidate_rule: CoverageRule,
    *,
    law_count: int,
) -> frozenset[int]:
    if isinstance(candidate_rule, SourceTargetSetsRule):
        return candidate_rule.source_ids
    if isinstance(candidate_rule, (ExplicitPairsRule, CompilerPairIndexesRule)):
        return frozenset(
            pair_index_to_ids(pair_index, law_count=law_count)[0]
            for pair_index in candidate_rule.pair_indexes
        )
    return frozenset(
        source_id for source_id, _ in candidate_rule.iter_covered_pairs()
    )


def _effective_targets_for_source(
    source_id: int,
    target_ids: frozenset[int],
    excluded_blocks: Sequence[tuple[frozenset[int], frozenset[int]]],
) -> frozenset[int]:
    effective_target_ids = target_ids
    if source_id in effective_target_ids:
        effective_target_ids = effective_target_ids - {source_id}
    for excluded_sources, excluded_targets in excluded_blocks:
        if source_id in excluded_sources:
            effective_target_ids = effective_target_ids - excluded_targets
    return effective_target_ids


def _profile_targets_by_source(
    verdict_profile: dict,
    source_ids: frozenset[int],
    *,
    law_count: int,
) -> dict[int, frozenset[int]]:
    targets_by_source: dict[int, frozenset[int]] = {}
    for group in verdict_profile["source_target_groups"]:
        group_sources = _decode_ids_payload(group, "source", law_count=law_count)
        matched_sources = source_ids & group_sources
        if not matched_sources:
            continue
        group_targets = _decode_ids_payload(group, "target", law_count=law_count)
        for source_id in matched_sources:
            targets_by_source[source_id] = group_targets

    if "explicit_source_target_groups" in verdict_profile:
        explicit_groups = verdict_profile["explicit_source_target_groups"]
    else:
        explicit_groups = _legacy_explicit_source_target_groups(
            verdict_profile["explicit_pair_indexes"],
            law_count=law_count,
        )
    for group in explicit_groups:
        source_id = int(group["source_id"])
        if source_id not in source_ids:
            continue
        explicit_targets = _decode_ids_payload(group, "target", law_count=law_count)
        existing = targets_by_source.get(source_id, frozenset())
        targets_by_source[source_id] = existing | explicit_targets
    return targets_by_source


def _encode_ids_payload(
    prefix: str,
    ids: Iterable[int],
    *,
    law_count: int,
) -> dict:
    id_set = frozenset(ids)
    if len(id_set) <= _SPARSE_ID_LIST_THRESHOLD:
        return {f"{prefix}_ids": sorted(id_set)}
    return {
        f"{prefix}_bitset_base64": _encode_ids_bitset(
            id_set,
            law_count=law_count,
        )
    }


def _decode_ids_payload(
    payload: dict,
    prefix: str,
    *,
    law_count: int,
) -> frozenset[int]:
    ids_key = f"{prefix}_ids"
    if ids_key in payload:
        return frozenset(int(eq_id) for eq_id in payload[ids_key])
    return _decode_ids_bitset(
        str(payload[f"{prefix}_bitset_base64"]),
        law_count=law_count,
    )


def _legacy_explicit_source_target_groups(
    pair_indexes: Iterable[int],
    *,
    law_count: int,
) -> list[dict]:
    targets_by_source: dict[int, set[int]] = {}
    for pair_index in pair_indexes:
        eq1_id, eq2_id = pair_index_to_ids(int(pair_index), law_count=law_count)
        targets_by_source.setdefault(eq1_id, set()).add(eq2_id)
    return [
        {
            "source_id": source_id,
            **_encode_ids_payload(
                "target",
                target_ids,
                law_count=law_count,
            ),
        }
        for source_id, target_ids in sorted(targets_by_source.items())
    ]
