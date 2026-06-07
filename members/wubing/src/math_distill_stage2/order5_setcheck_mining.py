from __future__ import annotations

import ast
import base64
import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from math_distill_stage2.counterexample.finite_magma import FiniteMagma, enumerate_magmas
from math_distill_stage2.equations import Equation, parse_equation
from math_distill_stage2.order5_spine_smoke import (
    DEFAULT_EQ_SIZE5_PATH,
    DEFAULT_ORDER4_MAX_ID,
    load_equation_spine_features,
)
from math_distill_stage2.order5_pair_space import ids_to_pair_index
from math_distill_stage2.order5_strategy_registry import ExplicitPairsRule
from math_distill_stage2.order5_strategy_registry import Order5StrategyRegistry
from math_distill_stage2.order5_strategy_registry import SourceTargetSetsRule
from math_distill_stage2.order5_strategy_registry import _union_count_for_rules


DEFAULT_SOURCE_TARGET_CACHE_PATH = Path(
    "data/processed/order5_strategy_registry/setcheck_source_target_cache.jsonl"
)


@dataclass(frozen=True)
class MagmaCandidate:
    label: str
    table: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class SetcheckCandidateRanking:
    label: str
    table: tuple[tuple[int, ...], ...]
    source_count: int
    target_count: int
    coverage_count: int
    increment: int
    representative_pairs: dict[str, tuple[int, int] | None]

    @property
    def order(self) -> int:
        return len(self.table)

    def to_json(self) -> dict:
        return {
            "label": self.label,
            "order": self.order,
            "table": [list(row) for row in self.table],
            "source_count": self.source_count,
            "target_count": self.target_count,
            "coverage_count": self.coverage_count,
            "increment": self.increment,
            "representative_pairs": {
                key: list(value) if value is not None else None
                for key, value in self.representative_pairs.items()
            },
        }


@dataclass(frozen=True)
class _SetcheckCandidateScore:
    label: str
    table: tuple[tuple[int, ...], ...]
    source_count: int
    target_count: int
    coverage_count: int
    increment: int

    @property
    def order(self) -> int:
        return len(self.table)


@dataclass
class _SourceTargetCache:
    path: Path
    equations_sha256: str
    law_count: int
    rows: dict[tuple[tuple[int, ...], ...], frozenset[int]]
    pending_rows: list[tuple[tuple[tuple[int, ...], ...], frozenset[int]]]

    @classmethod
    def load(cls, path: Path, equations_path: Path, law_count: int) -> "_SourceTargetCache":
        equations_sha256 = _sha256_file(equations_path)
        rows: dict[tuple[tuple[int, ...], ...], frozenset[int]] = {}
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                payload = json.loads(line)
                if payload.get("schema_version") != 1:
                    continue
                if payload.get("equations_sha256") != equations_sha256:
                    continue
                if payload.get("law_count") != law_count:
                    continue
                table = _normalize_table(payload["table"])
                source_ids = _decode_ids_bitset(
                    str(payload["source_bitset_base64"]),
                    law_count=law_count,
                )
                rows[table] = source_ids
        return cls(
            path=path,
            equations_sha256=equations_sha256,
            law_count=law_count,
            rows=rows,
            pending_rows=[],
        )

    def get(
        self,
        candidate: MagmaCandidate,
        parsed_equations: Sequence[tuple[int, Equation]],
        *,
        update: bool,
    ) -> tuple[frozenset[int], frozenset[int]]:
        source_ids = self.rows.get(candidate.table)
        if source_ids is None:
            source_ids, target_ids = _finmodel_source_target_sets(
                candidate.table,
                parsed_equations,
            )
            if update:
                self.rows[candidate.table] = source_ids
                self.pending_rows.append((candidate.table, source_ids))
                self.flush()
            return source_ids, target_ids
        return source_ids, _target_ids_from_sources(source_ids, law_count=self.law_count)

    def flush(self) -> None:
        if not self.pending_rows:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            for table, source_ids in self.pending_rows:
                payload = {
                    "schema_version": 1,
                    "equations_sha256": self.equations_sha256,
                    "law_count": self.law_count,
                    "table": [list(row) for row in table],
                    "source_bitset_base64": _encode_ids_bitset(
                        source_ids,
                        law_count=self.law_count,
                    ),
                }
                handle.write(json.dumps(payload, sort_keys=True) + "\n")
        self.pending_rows.clear()


def parse_magma_candidate_file(
    path: Path,
    *,
    order: int | None = None,
) -> list[MagmaCandidate]:
    seen: set[tuple[tuple[int, ...], ...]] = set()
    candidates: list[MagmaCandidate] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        parsed = _parse_candidate_line(line, line_number=line_number)
        if parsed is None:
            continue
        if order is not None and len(parsed.table) != order:
            continue
        if parsed.table in seen:
            continue
        seen.add(parsed.table)
        candidates.append(parsed)
    return candidates


def enumerate_magma_candidates(order: int) -> list[MagmaCandidate]:
    return [
        MagmaCandidate(label=f"enum_{index}", table=magma.table)
        for index, magma in enumerate(enumerate_magmas(order), start=1)
    ]


def rank_setcheck_candidates(
    *,
    equations_path: Path = DEFAULT_EQ_SIZE5_PATH,
    candidates: Sequence[MagmaCandidate],
    registry: Order5StrategyRegistry,
    order4_max_id: int = DEFAULT_ORDER4_MAX_ID,
    top_k: int | None = None,
    source_target_cache_path: Path | None = None,
    update_source_target_cache: bool = False,
) -> list[SetcheckCandidateRanking]:
    parsed_equations = _load_parsed_equations(equations_path)
    source_target_cache = (
        _SourceTargetCache.load(
            source_target_cache_path,
            equations_path,
            law_count=len(parsed_equations),
        )
        if source_target_cache_path is not None
        else None
    )
    source_masks, target_masks, explicit_pair_indexes = _strategy_membership_masks(registry)
    scores = [
        _score_candidate(
            candidate,
            parsed_equations,
            source_masks=source_masks,
            target_masks=target_masks,
            explicit_pair_indexes=explicit_pair_indexes,
            order4_max_id=order4_max_id,
            source_target_cache=source_target_cache,
            update_source_target_cache=update_source_target_cache,
        )
        for candidate in candidates
    ]
    if source_target_cache is not None:
        source_target_cache.flush()
    scores.sort(
        key=lambda row: (
            -row.increment,
            -row.coverage_count,
            row.order,
            str([list(item) for item in row.table]),
            row.label,
        )
    )
    if top_k is not None:
        scores = scores[:top_k]
    return [
        _ranking_with_representatives(
            score,
            parsed_equations,
            source_masks=source_masks,
            target_masks=target_masks,
            explicit_pair_indexes=explicit_pair_indexes,
            order4_max_id=order4_max_id,
            source_target_cache=source_target_cache,
            update_source_target_cache=update_source_target_cache,
        )
        for score in scores
    ]


def exact_increment_for_candidate(
    *,
    equations_path: Path = DEFAULT_EQ_SIZE5_PATH,
    candidate: MagmaCandidate,
    registry: Order5StrategyRegistry,
    order4_max_id: int = DEFAULT_ORDER4_MAX_ID,
    source_target_cache_path: Path | None = None,
    update_source_target_cache: bool = False,
) -> int:
    parsed_equations = _load_parsed_equations(equations_path)
    source_target_cache = (
        _SourceTargetCache.load(
            source_target_cache_path,
            equations_path,
            law_count=len(parsed_equations),
        )
        if source_target_cache_path is not None
        else None
    )
    source_ids, target_ids = _source_target_sets_for_candidate(
        candidate,
        parsed_equations,
        source_target_cache=source_target_cache,
        update_source_target_cache=update_source_target_cache,
    )
    if source_target_cache is not None:
        source_target_cache.flush()
    rule = SourceTargetSetsRule(
        source_ids=source_ids,
        target_ids=target_ids,
    )
    current_rules = [
        strategy.coverage_rule
        for strategy in registry.strategies
        if not strategy.deprecated and strategy.verdict is False
    ]
    current_union = _union_count_for_rules(current_rules)
    return _union_count_for_rules([*current_rules, rule]) - current_union


def _parse_candidate_line(line: str, *, line_number: int) -> MagmaCandidate | None:
    match = re.search(r"(\[\[.*\]\])", line)
    if match is None:
        return None
    table = _normalize_table(ast.literal_eval(match.group(1)))
    prefix = line[: match.start()].strip()
    label = prefix if prefix and prefix != "Table" else f"line_{line_number}"
    return MagmaCandidate(label=label, table=table)


def _normalize_table(raw_table: object) -> tuple[tuple[int, ...], ...]:
    if not isinstance(raw_table, list) or not raw_table:
        raise ValueError("magma table must be a non-empty nested list")
    table: list[tuple[int, ...]] = []
    order = len(raw_table)
    for row in raw_table:
        if not isinstance(row, list) or len(row) != order:
            raise ValueError("magma table must be square")
        normalized_row: list[int] = []
        for value in row:
            if not isinstance(value, int) or value < 0 or value >= order:
                raise ValueError("magma table entries must be integers in [0, order)")
            normalized_row.append(value)
        table.append(tuple(normalized_row))
    return tuple(table)


def _load_parsed_equations(equations_path: Path) -> list[tuple[int, Equation]]:
    return [
        (feature.equation_id, parse_equation(feature.equation))
        for feature in load_equation_spine_features(equations_path)
    ]


def _strategy_membership_masks(
    registry: Order5StrategyRegistry,
) -> tuple[list[int], list[int], frozenset[int]]:
    source_masks = [0] * (registry.law_count + 1)
    target_masks = [0] * (registry.law_count + 1)
    explicit_pair_indexes: set[int] = set()
    active_false_strategies = [
        strategy
        for strategy in registry.strategies
        if not strategy.deprecated and strategy.verdict is False
    ]
    source_target_strategies = [
        strategy
        for strategy in active_false_strategies
        if isinstance(strategy.coverage_rule, SourceTargetSetsRule)
    ]
    for strategy in active_false_strategies:
        if isinstance(strategy.coverage_rule, ExplicitPairsRule):
            explicit_pair_indexes.update(strategy.coverage_rule.pair_indexes)
    for bit, strategy in enumerate(source_target_strategies):
        mask = 1 << bit
        for eq_id in strategy.coverage_rule.source_ids:
            source_masks[eq_id] |= mask
        for eq_id in strategy.coverage_rule.target_ids:
            target_masks[eq_id] |= mask
    return source_masks, target_masks, frozenset(explicit_pair_indexes)


def _score_candidate(
    candidate: MagmaCandidate,
    parsed_equations: Sequence[tuple[int, Equation]],
    *,
    source_masks: Sequence[int],
    target_masks: Sequence[int],
    explicit_pair_indexes: frozenset[int],
    order4_max_id: int,
    source_target_cache: _SourceTargetCache | None = None,
    update_source_target_cache: bool = False,
) -> _SetcheckCandidateScore:
    source_ids, target_ids = _source_target_sets_for_candidate(
        candidate,
        parsed_equations,
        source_target_cache=source_target_cache,
        update_source_target_cache=update_source_target_cache,
    )
    return _SetcheckCandidateScore(
        label=candidate.label,
        table=candidate.table,
        source_count=len(source_ids),
        target_count=len(target_ids),
        coverage_count=_coverage_count(source_ids, target_ids, order4_max_id=order4_max_id),
        increment=_increment_count(
            source_ids,
            target_ids,
            source_masks=source_masks,
            target_masks=target_masks,
            explicit_pair_indexes=explicit_pair_indexes,
            order4_max_id=order4_max_id,
        ),
    )


def _ranking_with_representatives(
    score: _SetcheckCandidateScore,
    parsed_equations: Sequence[tuple[int, Equation]],
    *,
    source_masks: Sequence[int],
    target_masks: Sequence[int],
    explicit_pair_indexes: frozenset[int],
    order4_max_id: int,
    source_target_cache: _SourceTargetCache | None = None,
    update_source_target_cache: bool = False,
) -> SetcheckCandidateRanking:
    source_ids, target_ids = _source_target_sets_for_candidate(
        MagmaCandidate(label=score.label, table=score.table),
        parsed_equations,
        source_target_cache=source_target_cache,
        update_source_target_cache=update_source_target_cache,
    )
    return SetcheckCandidateRanking(
        label=score.label,
        table=score.table,
        source_count=score.source_count,
        target_count=score.target_count,
        coverage_count=score.coverage_count,
        increment=score.increment,
        representative_pairs=_representative_pairs(
            score.increment,
            source_ids,
            target_ids,
            source_masks=source_masks,
            target_masks=target_masks,
            explicit_pair_indexes=explicit_pair_indexes,
            order4_max_id=order4_max_id,
        ),
    )


def _finmodel_source_target_sets(
    table: tuple[tuple[int, ...], ...],
    parsed_equations: Sequence[tuple[int, Equation]],
) -> tuple[frozenset[int], frozenset[int]]:
    magma = FiniteMagma(order=len(table), table=table)
    sources: set[int] = set()
    targets: set[int] = set()
    for eq_id, equation in parsed_equations:
        if magma.satisfies(equation):
            sources.add(eq_id)
        else:
            targets.add(eq_id)
    return frozenset(sources), frozenset(targets)


def _source_target_sets_for_candidate(
    candidate: MagmaCandidate,
    parsed_equations: Sequence[tuple[int, Equation]],
    *,
    source_target_cache: _SourceTargetCache | None,
    update_source_target_cache: bool,
) -> tuple[frozenset[int], frozenset[int]]:
    if source_target_cache is None:
        return _finmodel_source_target_sets(candidate.table, parsed_equations)
    return source_target_cache.get(
        candidate,
        parsed_equations,
        update=update_source_target_cache,
    )


def _target_ids_from_sources(
    source_ids: frozenset[int],
    *,
    law_count: int,
) -> frozenset[int]:
    return frozenset(eq_id for eq_id in range(1, law_count + 1) if eq_id not in source_ids)


def _encode_ids_bitset(ids: Iterable[int], *, law_count: int) -> str:
    raw = bytearray((law_count + 7) // 8)
    for eq_id in ids:
        if eq_id < 1 or eq_id > law_count:
            raise ValueError(f"eq_id must be in [1, {law_count}]; got {eq_id}")
        bit_index = eq_id - 1
        raw[bit_index // 8] |= 1 << (bit_index % 8)
    return base64.b64encode(bytes(raw)).decode("ascii")


def _decode_ids_bitset(payload: str, *, law_count: int) -> frozenset[int]:
    raw = base64.b64decode(payload.encode("ascii"))
    expected_length = (law_count + 7) // 8
    if len(raw) != expected_length:
        raise ValueError(
            f"source bitset must have {expected_length} bytes; got {len(raw)}"
        )
    return frozenset(
        eq_id
        for eq_id in range(1, law_count + 1)
        if raw[(eq_id - 1) // 8] & (1 << ((eq_id - 1) % 8))
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _coverage_count(
    source_ids: frozenset[int],
    target_ids: frozenset[int],
    *,
    order4_max_id: int,
) -> int:
    return (
        len(source_ids) * len(target_ids)
        - len(source_ids & target_ids)
    )


def _increment_count(
    source_ids: frozenset[int],
    target_ids: frozenset[int],
    *,
    source_masks: Sequence[int],
    target_masks: Sequence[int],
    explicit_pair_indexes: frozenset[int],
    order4_max_id: int,
) -> int:
    all_target_counts = _mask_counts(target_ids, target_masks=target_masks)
    all_source_counts = _mask_counts(source_ids, target_masks=source_masks)
    total = _disjoint_mask_product_count(all_source_counts, all_target_counts)
    for source_id in source_ids:
        source_mask = source_masks[source_id]
        if (
            source_id in target_ids
            and not (source_mask & target_masks[source_id])
        ):
            total -= 1
    law_count = len(source_masks) - 1
    for pair_index in explicit_pair_indexes:
        source_id = pair_index // (law_count - 1) + 1
        target_slot = pair_index % (law_count - 1) + 1
        target_id = target_slot + 1 if target_slot >= source_id else target_slot
        if source_id not in source_ids or target_id not in target_ids:
            continue
        if source_id == target_id:
            continue
        if source_masks[source_id] & target_masks[target_id]:
            continue
        total -= 1
    return total


def _representative_pairs(
    increment: int,
    source_ids: frozenset[int],
    target_ids: frozenset[int],
    *,
    source_masks: Sequence[int],
    target_masks: Sequence[int],
    explicit_pair_indexes: frozenset[int],
    order4_max_id: int,
) -> dict[str, tuple[int, int] | None]:
    if increment == 0:
        return {
            "new_order4_source_to_order4_target": None,
            "new_order4_source_to_order5_target": None,
            "new_order5_source_to_order4_target": None,
            "new_order5_source_to_order5_target": None,
            "overlap_existing": None,
        }
    return {
        "new_order4_source_to_order4_target": _find_representative_pair(
            source_ids,
            target_ids,
            source_masks=source_masks,
            target_masks=target_masks,
            explicit_pair_indexes=explicit_pair_indexes,
            order4_max_id=order4_max_id,
            source_order5=False,
            target_order5=False,
            want_existing=False,
        ),
        "new_order4_source_to_order5_target": _find_representative_pair(
            source_ids,
            target_ids,
            source_masks=source_masks,
            target_masks=target_masks,
            explicit_pair_indexes=explicit_pair_indexes,
            order4_max_id=order4_max_id,
            source_order5=False,
            target_order5=True,
            want_existing=False,
        ),
        "new_order5_source_to_order4_target": _find_representative_pair(
            source_ids,
            target_ids,
            source_masks=source_masks,
            target_masks=target_masks,
            explicit_pair_indexes=explicit_pair_indexes,
            order4_max_id=order4_max_id,
            source_order5=True,
            target_order5=False,
            want_existing=False,
        ),
        "new_order5_source_to_order5_target": _find_representative_pair(
            source_ids,
            target_ids,
            source_masks=source_masks,
            target_masks=target_masks,
            explicit_pair_indexes=explicit_pair_indexes,
            order4_max_id=order4_max_id,
            source_order5=True,
            target_order5=True,
            want_existing=False,
        ),
        "overlap_existing": _find_representative_pair(
            source_ids,
            target_ids,
            source_masks=source_masks,
            target_masks=target_masks,
            explicit_pair_indexes=explicit_pair_indexes,
            order4_max_id=order4_max_id,
            source_order5=None,
            target_order5=None,
            want_existing=True,
        ),
    }


def _find_representative_pair(
    source_ids: frozenset[int],
    target_ids: frozenset[int],
    *,
    source_masks: Sequence[int],
    target_masks: Sequence[int],
    explicit_pair_indexes: frozenset[int],
    order4_max_id: int,
    source_order5: bool | None,
    target_order5: bool | None,
    want_existing: bool,
) -> tuple[int, int] | None:
    candidate_sources = _filter_order(sorted(source_ids), source_order5, order4_max_id)
    candidate_targets = _filter_order(sorted(target_ids), target_order5, order4_max_id)
    targets_by_mask: dict[int, list[int]] = {}
    for target_id in candidate_targets:
        targets_by_mask.setdefault(target_masks[target_id], []).append(target_id)
    law_count = len(source_masks) - 1
    if want_existing:
        for source_id in candidate_sources:
            source_mask = source_masks[source_id]
            for target_mask, targets in sorted(targets_by_mask.items()):
                if not (source_mask & target_mask):
                    continue
                target_id = _first_valid_representative_target(
                    source_id,
                    targets,
                    explicit_pair_indexes=explicit_pair_indexes,
                    law_count=law_count,
                    order4_max_id=order4_max_id,
                    want_existing=True,
                    block_covered=True,
                )
                if target_id is not None:
                    return source_id, target_id
        candidate_source_set = frozenset(candidate_sources)
        candidate_target_set = frozenset(candidate_targets)
        for pair_index in sorted(explicit_pair_indexes):
            source_id = pair_index // (law_count - 1) + 1
            target_slot = pair_index % (law_count - 1) + 1
            target_id = target_slot + 1 if target_slot >= source_id else target_slot
            if source_id not in candidate_source_set or target_id not in candidate_target_set:
                continue
            if source_id == target_id:
                continue
            return source_id, target_id
        return None
    for source_id in candidate_sources:
        source_mask = source_masks[source_id]
        for target_mask, targets in sorted(targets_by_mask.items()):
            block_covered = bool(source_mask & target_mask)
            if block_covered:
                continue
            target_id = _first_valid_representative_target(
                source_id,
                targets,
                explicit_pair_indexes=explicit_pair_indexes,
                law_count=law_count,
                order4_max_id=order4_max_id,
                want_existing=want_existing,
                block_covered=block_covered,
            )
            if target_id is not None:
                return source_id, target_id
    return None


def _first_valid_representative_target(
    source_id: int,
    target_ids: Sequence[int],
    *,
    explicit_pair_indexes: frozenset[int],
    law_count: int,
    order4_max_id: int,
    want_existing: bool,
    block_covered: bool,
) -> int | None:
    for target_id in target_ids:
        if source_id == target_id:
            continue
        explicit_covered = (
            ids_to_pair_index(source_id, target_id, law_count=law_count)
            in explicit_pair_indexes
        )
        covered = block_covered or explicit_covered
        if covered is not want_existing:
            continue
        return target_id
    return None


def _filter_order(
    ids: Iterable[int],
    order5: bool | None,
    order4_max_id: int,
) -> list[int]:
    if order5 is None:
        return list(ids)
    return [eq_id for eq_id in ids if (eq_id > order4_max_id) is order5]


def _covered_by_current(
    source_id: int,
    target_id: int,
    *,
    source_masks: Sequence[int],
    target_masks: Sequence[int],
    explicit_pair_indexes: frozenset[int],
    order4_max_id: int,
) -> bool:
    law_count = len(source_masks) - 1
    return (
        source_id != target_id
        and (
            bool(source_masks[source_id] & target_masks[target_id])
            or ids_to_pair_index(source_id, target_id, law_count=law_count)
            in explicit_pair_indexes
        )
    )


def _mask_counts(
    ids: Iterable[int],
    *,
    target_masks: Sequence[int],
) -> Counter[int]:
    return Counter(target_masks[eq_id] for eq_id in ids)


def _disjoint_mask_product_count(
    source_counts: Counter[int],
    target_counts: Counter[int],
) -> int:
    return sum(
        source_count * target_count
        for source_mask, source_count in source_counts.items()
        for target_mask, target_count in target_counts.items()
        if not (source_mask & target_mask)
    )
