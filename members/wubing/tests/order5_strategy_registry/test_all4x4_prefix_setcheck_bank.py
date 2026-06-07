from pathlib import Path

import pytest

from math_distill_stage2.order5_pair_space import ids_to_pair_index
from math_distill_stage2.order5_strategy_registry import (
    DEFAULT_EQ_SIZE5_PATH,
    DEFAULT_SOURCE_TARGET_CACHE_PATH,
    build_default_order5_strategy_registry,
)


ALL4X4_PREFIX_SETCHECKS = {
    "false.finmodel.setcheck.structured.all4x4.refutation5.all_equations.v1": {
        "current_increment": 2_394_048,
        "independent_current_increment": 2_394_048,
        "raw_coverage": 44_841_975,
        "source_count": 725,
        "target_count": 61_851,
        "priority": 382,
        "table": [
            [0, 2, 3, 4, 5, 6, 7, 1],
            [6, 1, 5, 7, 3, 0, 4, 2],
            [7, 3, 2, 6, 1, 4, 0, 5],
            [1, 6, 4, 3, 7, 2, 5, 0],
            [2, 0, 7, 5, 4, 1, 3, 6],
            [3, 7, 0, 1, 6, 5, 2, 4],
            [4, 5, 1, 0, 2, 7, 6, 3],
            [5, 4, 6, 2, 0, 3, 1, 7],
        ],
        "representative_pairs": [
            (640, 32_815),
            (4_899, 4_273),
            (4_899, 44_178),
            (1, 54_897),
        ],
    },
    "false.finmodel.setcheck.structured.all4x4.refutation834.all_equations.v1": {
        "current_increment": 691_320,
        "independent_current_increment": 691_320,
        "raw_coverage": 358_630_108,
        "source_count": 6_382,
        "target_count": 56_194,
        "priority": 383,
        "table": [
            [3, 2, 3, 3, 2],
            [2, 4, 3, 3, 3],
            [3, 3, 3, 3, 3],
            [3, 3, 3, 3, 3],
            [3, 3, 3, 3, 3],
        ],
        "representative_pairs": [
            (4_381, 55_052),
            (53_814, 4_270),
            (53_814, 55_052),
            (1, 55_052),
        ],
    },
    "false.finmodel.setcheck.structured.all4x4.refutation833.all_equations.v1": {
        "current_increment": 204_553,
        "independent_current_increment": 481_896,
        "raw_coverage": 358_630_108,
        "source_count": 6_382,
        "target_count": 56_194,
        "priority": 384,
        "table": [
            [3, 2, 3, 3, 2],
            [4, 2, 3, 3, 3],
            [3, 3, 3, 3, 3],
            [3, 3, 3, 3, 3],
            [3, 3, 3, 3, 3],
        ],
        "representative_pairs": [
            (4_384, 54_900),
            (54_695, 4_269),
            (54_688, 54_897),
            (1, 54_900),
        ],
    },
    "false.finmodel.setcheck.structured.all4x4.refutation837.all_equations.v1": {
        "current_increment": 399_267,
        "independent_current_increment": 402_184,
        "raw_coverage": 284_616_444,
        "source_count": 4_938,
        "target_count": 57_638,
        "priority": 385,
        "table": [
            [4, 2, 3, 3, 3],
            [4, 3, 3, 3, 3],
            [4, 3, 3, 3, 3],
            [3, 3, 3, 3, 3],
            [3, 2, 3, 3, 3],
        ],
        "representative_pairs": [
            (4_393, 60_889),
            (54_052, 4_606),
            (56_447, 61_753),
            (1, 60_876),
        ],
    },
}


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


def test_all4x4_prefix_setcheck_bank_counts_and_evidence(registry, summary):
    assert summary["raw_false_union_covered"] == 2_384_904_817
    assert summary["conflict_count"] == 0

    for strategy_id, expected in ALL4X4_PREFIX_SETCHECKS.items():
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
        assert strategy.evidence["official_smoke"]["combo_smoke_accepted_count"] == 16
        assert (
            strategy.evidence["official_smoke"]["base_url"]
            == "http://10.220.69.172:8890"
        )


def test_all4x4_prefix_setcheck_bank_representative_pairs_are_covered(
    registry,
    law_count: int,
):
    for strategy_id, expected in ALL4X4_PREFIX_SETCHECKS.items():
        for source_id, target_id in expected["representative_pairs"]:
            pair_index = ids_to_pair_index(source_id, target_id, law_count=law_count)
            strategy_ids = [
                match["strategy_id"]
                for match in registry.find_covering_strategies(pair_index)
            ]

            assert strategy_id in strategy_ids
