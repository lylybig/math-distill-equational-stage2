from pathlib import Path
import json

import pytest

from math_distill_stage2.order5_pair_space import ids_to_pair_index
from math_distill_stage2.order5_strategy_registry import (
    DEFAULT_EQ_SIZE5_PATH,
    DEFAULT_SOURCE_TARGET_CACHE_PATH,
    build_default_order5_strategy_registry,
)


SELECTOR_TAIL_SETCHECKS = {
    "false.finmodel.setcheck.bank.enum_order3_58.v1": {
        "current_increment": 258_489,
        "independent_current_increment": 258_489,
        "raw_coverage": 271_272_540,
        "source_count": 4_686,
        "target_count": 57_890,
        "priority": 380,
        "table": [[0, 0, 0], [0, 0, 2], [0, 1, 0]],
        "representative_pairs": [
            (313, 61_039),
            (42_423, 3_462),
            (41_541, 60_825),
            (1, 54_740),
        ],
    },
    "false.finmodel.setcheck.bank.enum_order3_784.v1": {
        "current_increment": 138_815,
        "independent_current_increment": 156_929,
        "raw_coverage": 109_042_908,
        "source_count": 1_794,
        "target_count": 60_782,
        "priority": 381,
        "table": [[0, 0, 1], [0, 0, 2], [0, 0, 0]],
        "representative_pairs": [
            (310, 55_042),
            (41_541, 3_459),
            (41_541, 45_040),
            (1, 55_767),
        ],
    },
}
ROUND2_FRESH_MUTATION_SELECTION = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "false_controller_round2_fresh_setcheck_top100_current_merge_selection_"
    "20260522.jsonl"
)
ROUND2_FRESH_MUTATION_PREFIX = "false.finmodel.setcheck.round2_fresh_mutation_gen1."


@pytest.fixture(scope="module")
def registry():
    return build_default_order5_strategy_registry(
        include_true_strategies=False,
        source_target_cache_path=DEFAULT_SOURCE_TARGET_CACHE_PATH,
    )


@pytest.fixture(scope="module")
def summary(registry):
    return registry.coverage_summary()


@pytest.fixture(scope="module")
def law_count() -> int:
    return len(
        [
            line
            for line in Path(DEFAULT_EQ_SIZE5_PATH).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    )


def test_selector_tail_setcheck_bank_counts_and_evidence(registry, summary):
    for strategy_id, expected in SELECTOR_TAIL_SETCHECKS.items():
        strategy = next(
            strategy
            for strategy in registry.strategies
            if strategy.strategy_id == strategy_id
        )

        assert strategy.priority == expected["priority"]
        assert summary["strategy_counts"][strategy_id] == expected["raw_coverage"]
        assert strategy.evidence["model_table"] == expected["table"]
        assert strategy.evidence["model_source_count"] == expected["source_count"]
        assert strategy.evidence["model_target_count"] == expected["target_count"]
        assert strategy.evidence["current_increment"] == expected["current_increment"]
        assert strategy.evidence["independent_current_increment"] == expected[
            "independent_current_increment"
        ]
        assert strategy.evidence["raw_coverage"] == expected["raw_coverage"]
        assert strategy.evidence["selection_threshold"] == 100_000
        assert strategy.evidence["official_smoke"]["status"] == "accepted"
        assert strategy.evidence["official_smoke"]["accepted_count"] == 4
        assert strategy.evidence["official_smoke"]["combo_smoke_accepted_count"] == 8
        assert (
            strategy.evidence["official_smoke"]["base_url"]
            == "http://10.220.69.172:8890"
        )


def test_selector_tail_setcheck_bank_representative_pairs_are_covered(
    registry,
    law_count: int,
):
    for strategy_id, expected in SELECTOR_TAIL_SETCHECKS.items():
        for source_id, target_id in expected["representative_pairs"]:
            pair_index = ids_to_pair_index(source_id, target_id, law_count=law_count)
            strategy_ids = [
                match["strategy_id"]
                for match in registry.find_covering_strategies(pair_index)
            ]

            assert strategy_id in strategy_ids


def test_round2_fresh_mutation_gen1_setcheck_bank_counts_and_smoke(
    registry,
    summary,
):
    candidate_rows = _read_jsonl(ROUND2_FRESH_MUTATION_SELECTION)
    assert len(candidate_rows) == 40

    strategy_by_id = {
        strategy.strategy_id: strategy
        for strategy in registry.strategies
        if strategy.strategy_key.startswith(ROUND2_FRESH_MUTATION_PREFIX)
    }
    assert len(strategy_by_id) == 40

    priorities = sorted(strategy.priority for strategy in strategy_by_id.values())
    assert priorities == list(range(624, 664))
    assert sum(
        strategy.evidence["current_increment"]
        for strategy in strategy_by_id.values()
    ) == 186_883
    assert sum(
        strategy.evidence["current_true_overlap_count"]
        for strategy in strategy_by_id.values()
    ) == 0

    for row in candidate_rows:
        strategy_id = f"{row['candidate_key']}.v1"
        strategy = strategy_by_id[strategy_id]

        assert summary["strategy_counts"][strategy_id] == int(row["raw_coverage"])
        assert strategy.evidence["current_increment"] == int(
            row["exact_current_false_union_increment"]
        )
        assert strategy.evidence["independent_current_increment"] == int(row["increment"])
        assert strategy.evidence["raw_coverage"] == int(row["raw_coverage"])
        assert strategy.evidence["selection_threshold"] == 100_000
        assert strategy.evidence["current_true_overlap_count"] == 0
        assert strategy.evidence["official_smoke"]["status"] == "accepted"
        assert (
            strategy.evidence["official_smoke"]["combined_accepted_count"]
            == 103
        )
        assert strategy.evidence["official_smoke"]["combined_total_count"] == 103
        assert (
            strategy.evidence["official_smoke"]["base_url"]
            == "http://10.220.69.172:8890"
        )


def test_round2_fresh_mutation_gen1_representative_pairs_are_covered(
    registry,
    law_count: int,
):
    for row in _read_jsonl(ROUND2_FRESH_MUTATION_SELECTION):
        strategy_id = f"{row['candidate_key']}.v1"
        for pair in row["representative_pairs"].values():
            if pair is None:
                continue
            pair_index = ids_to_pair_index(*pair, law_count=law_count)
            strategy_ids = [
                match["strategy_id"]
                for match in registry.find_covering_strategies(pair_index)
            ]

            assert strategy_id in strategy_ids


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
