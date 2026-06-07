from pathlib import Path

import pytest

from math_distill_stage2.order5_pair_space import ids_to_pair_index
from math_distill_stage2.order5_strategy_registry import (
    DEFAULT_EQ_SIZE5_PATH,
    DEFAULT_SOURCE_TARGET_CACHE_PATH,
    build_default_order5_strategy_registry,
)


ALL4X4_TAIL_SETCHECKS = {
    "false.finmodel.setcheck.structured.all4x4.refutation838.all_equations.v1": {
        "current_increment": 194_945,
        "independent_current_increment": 194_945,
        "raw_coverage": 214_305_840,
        "source_count": 3_636,
        "target_count": 58_940,
        "priority": 386,
        "representative_pairs": [
            (4_280, 53_860),
            (53_811, 4_268),
            (53_808, 53_863),
            (1, 61_191),
        ],
    },
    "false.finmodel.setcheck.structured.all4x4.refutation421.all_equations.v1": {
        "current_increment": 184_366,
        "independent_current_increment": 184_568,
        "raw_coverage": 83_313_615,
        "source_count": 1_361,
        "target_count": 61_215,
        "priority": 387,
        "representative_pairs": [
            (312, 54_692),
            (41_581, 4_590),
            (41_534, 41_537),
            (1, 54_710),
        ],
    },
    "false.finmodel.setcheck.structured.all4x4.refutation372.all_equations.v1": {
        "current_increment": 134_294,
        "independent_current_increment": 169_764,
        "raw_coverage": 190_789_468,
        "source_count": 3_214,
        "target_count": 59_362,
        "priority": 388,
        "representative_pairs": [
            (310, 53_860),
            (41_552, 3_261),
            (41_542, 53_860),
            (1, 60_828),
        ],
    },
    "false.finmodel.setcheck.structured.all4x4.refutation457.all_equations.v1": {
        "current_increment": 142_749,
        "independent_current_increment": 163_272,
        "raw_coverage": 85_825_719,
        "source_count": 1_403,
        "target_count": 61_173,
        "priority": 389,
        "representative_pairs": [
            (310, 54_684),
            (41_530, 3_456),
            (41_530, 54_684),
            (1, 54_684),
        ],
    },
    "false.finmodel.setcheck.structured.all4x4.refutation385.all_equations.v1": {
        "current_increment": 145_500,
        "independent_current_increment": 145_770,
        "raw_coverage": 83_313_615,
        "source_count": 1_361,
        "target_count": 61_215,
        "priority": 390,
        "representative_pairs": [
            (377, 56_796),
            (46_156, 3_918),
            (46_156, 49_629),
            (1, 53_822),
        ],
    },
    "false.finmodel.setcheck.structured.all4x4.refutation171.all_equations.v1": {
        "current_increment": 115_605,
        "independent_current_increment": 128_476,
        "raw_coverage": 62_242_215,
        "source_count": 1_011,
        "target_count": 61_565,
        "priority": 391,
        "representative_pairs": [
            (310, 45_037),
            (12_590, 4_065),
            (12_590, 52_053),
            (1, 57_315),
        ],
    },
    "false.finmodel.setcheck.structured.all4x4.refutation418.all_equations.v1": {
        "current_increment": 125_195,
        "independent_current_increment": 128_425,
        "raw_coverage": 284_721_840,
        "source_count": 4_940,
        "target_count": 57_636,
        "priority": 392,
        "representative_pairs": [
            (4_392, 60_889),
            (57_337, 4_590),
            (57_317, 60_876),
            (1, 60_876),
        ],
    },
    "false.finmodel.setcheck.structured.all4x4.refutation243.all_equations.v1": {
        "current_increment": 126_737,
        "independent_current_increment": 128_021,
        "raw_coverage": 62_423_868,
        "source_count": 1_014,
        "target_count": 61_562,
        "priority": 393,
        "representative_pairs": [
            (208, 53_807),
            (19_632, 3_258),
            (19_609, 43_283),
            (1, 55_561),
        ],
    },
    "false.finmodel.setcheck.structured.all4x4.refutation773.all_equations.v1": {
        "current_increment": 116_028,
        "independent_current_increment": 116_034,
        "raw_coverage": 4_625_148,
        "source_count": 74,
        "target_count": 62_502,
        "priority": 394,
        "representative_pairs": [
            (283, 53_184),
            (31_409, 4_320),
            (31_409, 30_128),
            (1, 60_838),
        ],
    },
    "false.finmodel.setcheck.structured.all4x4.refutation852.all_equations.v1": {
        "current_increment": 101_609,
        "independent_current_increment": 101_609,
        "raw_coverage": 2_688_919,
        "source_count": 43,
        "target_count": 62_533,
        "priority": 395,
        "representative_pairs": [
            (56, 45_933),
            (7_328, 4_065),
            (7_328, 60_823),
            (1, 60_823),
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


def test_all4x4_tail_setcheck_bank_counts_and_evidence(registry, summary):
    assert summary["raw_false_union_covered"] == 2_384_904_817
    assert summary["conflict_count"] == 0

    for strategy_id, expected in ALL4X4_TAIL_SETCHECKS.items():
        strategy = next(
            strategy
            for strategy in registry.strategies
            if strategy.strategy_id == strategy_id
        )

        assert strategy.priority == expected["priority"]
        assert summary["strategy_counts"][strategy_id] == expected["raw_coverage"]
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
        assert strategy.evidence["official_smoke"]["combo_smoke_accepted_count"] == 40
        assert (
            strategy.evidence["official_smoke"]["base_url"]
            == "http://10.220.69.172:8890"
        )


def test_all4x4_tail_setcheck_bank_representative_pairs_are_covered(
    registry,
    law_count: int,
):
    for strategy_id, expected in ALL4X4_TAIL_SETCHECKS.items():
        for source_id, target_id in expected["representative_pairs"]:
            pair_index = ids_to_pair_index(source_id, target_id, law_count=law_count)
            strategy_ids = [
                match["strategy_id"]
                for match in registry.find_covering_strategies(pair_index)
            ]

            assert strategy_id in strategy_ids
