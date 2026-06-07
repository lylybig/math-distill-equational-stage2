from pathlib import Path
import json

import pytest

from math_distill_stage2.order5_pair_space import ids_to_pair_index
from math_distill_stage2.order5_strategy_registry import (
    DEFAULT_EQ_SIZE5_PATH,
    DEFAULT_SOURCE_TARGET_CACHE_PATH,
    STRUCTURED_AFFINE_LOW_ORDER_LE9_COMBO19_SPECS,
    STRUCTURED_AFFINE_LOW_ORDER_TAIL_COMBO2_SPECS,
    STRUCTURED_AFFINE_MOD11_COMBO9_MATCHOP_NOHB_SPECS,
    STRUCTURED_AFFINE_MOD11_TOP2_MATCHOP_NOHB_SPECS,
    STRUCTURED_AFFINE_MOD4_A0_B1_C1_STRATEGY_KEY,
    STRUCTURED_AFFINE_MOD4_A1_B0_C3_STRATEGY_KEY,
    STRUCTURED_AFFINE_MOD4_A2_B3_C3_STRATEGY_KEY,
    STRUCTURED_AFFINE_MOD4_A3_B2_C3_STRATEGY_KEY,
    STRUCTURED_AFFINE_MOD5_A0_B1_C4_STRATEGY_KEY,
    STRUCTURED_AFFINE_MOD5_A1_B0_C4_STRATEGY_KEY,
    STRUCTURED_AFFINE_MOD5_A1_B3_C4_STRATEGY_KEY,
    STRUCTURED_AFFINE_MOD5_A2_B3_C0_STRATEGY_KEY,
    STRUCTURED_AFFINE_MOD5_A3_B1_C4_STRATEGY_KEY,
    STRUCTURED_AFFINE_MOD5_A3_B2_C0_STRATEGY_KEY,
    STRUCTURED_AFFINE_MOD7_A2_B5_C6_STRATEGY_KEY,
    STRUCTURED_AFFINE_MOD7_A1_B3_C6_STRATEGY_KEY,
    STRUCTURED_AFFINE_MOD7_A3_B1_C6_STRATEGY_KEY,
    STRUCTURED_AFFINE_MOD7_A5_B2_C6_STRATEGY_KEY,
    STRUCTURED_AFFINE_MOD7_A6_B2_C0_STRATEGY_KEY,
    STRUCTURED_ALL4X4_REFUTATION4_STRATEGY_KEY,
    STRUCTURED_ETP_ORDER4_REFUTATION482_STRATEGY_KEY,
    STRUCTURED_ETP_ORDER4_REFUTATION516_STRATEGY_KEY,
    build_default_order5_strategy_registry,
)


AFFINE_MOD17_CANDIDATE6_SOURCEFIRST_STRATEGY_KEY = (
    "false.finmodel.setcheck.affine_mod17_candidate6_sourcefirst_addon_20260526"
)
TOP5_PACKET_SETCHECK_ROWS = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "false_postcanonical_joint_min1m_oldhigh_mod17_nonmod17_top5_setcheck_rows_20260527.jsonl"
)
REVIVED_MOD17_PACKET_ROWS = [
    {
        "strategy_key": "false.finmodel.setcheck.affine_mod_probe.mod17.a7.b11.c0.all_equations",
        "priority": 665,
        "a": 7,
        "b": 11,
        "current_increment": 499_156,
        "raw_coverage": 21_902_848,
        "source_count": 352,
        "target_count": 62_224,
        "smoke_accepted_count": 4,
    },
    {
        "strategy_key": "false.finmodel.setcheck.affine_mod_probe.mod17.a11.b7.c0.all_equations",
        "priority": 666,
        "a": 11,
        "b": 7,
        "current_increment": 498_349,
        "raw_coverage": 21_902_848,
        "source_count": 352,
        "target_count": 62_224,
        "smoke_accepted_count": 4,
    },
    {
        "strategy_key": "false.finmodel.setcheck.affine_mod_probe.mod17.a9.b2.c0.all_equations",
        "priority": 667,
        "a": 9,
        "b": 2,
        "current_increment": 438_605,
        "raw_coverage": 3_063_823,
        "source_count": 49,
        "target_count": 62_527,
        "smoke_accepted_count": 4,
    },
    {
        "strategy_key": "false.finmodel.setcheck.affine_mod_probe.mod17.a8.b7.c0.all_equations",
        "priority": 668,
        "a": 8,
        "b": 7,
        "current_increment": 376_527,
        "raw_coverage": 2_001_408,
        "source_count": 32,
        "target_count": 62_544,
        "smoke_accepted_count": 2,
    },
    {
        "strategy_key": "false.finmodel.setcheck.affine_mod_probe.mod17.a7.b8.c0.all_equations",
        "priority": 669,
        "a": 7,
        "b": 8,
        "current_increment": 376_534,
        "raw_coverage": 2_001_408,
        "source_count": 32,
        "target_count": 62_544,
        "smoke_accepted_count": 2,
    },
]
EXPECTED_RAW_FALSE_UNION_COVERED = 2_387_093_988


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


def test_default_registry_includes_structured_affine_mod5_setcheck(summary):
    strategy_counts = summary["strategy_counts"]

    assert strategy_counts[f"{STRUCTURED_AFFINE_MOD5_A3_B2_C0_STRATEGY_KEY}.v1"] == (
        19_178_544
    )
    assert strategy_counts[f"{STRUCTURED_AFFINE_MOD5_A2_B3_C0_STRATEGY_KEY}.v1"] == (
        19_178_544
    )
    assert strategy_counts[f"{STRUCTURED_AFFINE_MOD4_A0_B1_C1_STRATEGY_KEY}.v1"] == (
        171_185_703
    )
    assert strategy_counts[f"{STRUCTURED_AFFINE_MOD4_A1_B0_C3_STRATEGY_KEY}.v1"] == (
        171_185_703
    )
    assert strategy_counts[f"{STRUCTURED_AFFINE_MOD5_A0_B1_C4_STRATEGY_KEY}.v1"] == (
        133_176_220
    )
    assert strategy_counts[f"{STRUCTURED_AFFINE_MOD5_A1_B0_C4_STRATEGY_KEY}.v1"] == (
        133_176_220
    )
    assert strategy_counts[f"{STRUCTURED_ETP_ORDER4_REFUTATION516_STRATEGY_KEY}.v1"] == (
        337_532_668
    )
    assert strategy_counts[f"{STRUCTURED_ETP_ORDER4_REFUTATION482_STRATEGY_KEY}.v1"] == (
        26_167_255
    )
    assert strategy_counts[f"{STRUCTURED_ALL4X4_REFUTATION4_STRATEGY_KEY}.v1"] == (
        44_841_975
    )
    assert strategy_counts[f"{STRUCTURED_AFFINE_MOD7_A2_B5_C6_STRATEGY_KEY}.v1"] == (
        10_484_544
    )
    assert strategy_counts[f"{STRUCTURED_AFFINE_MOD7_A5_B2_C6_STRATEGY_KEY}.v1"] == (
        10_484_544
    )
    assert strategy_counts[f"{STRUCTURED_AFFINE_MOD7_A6_B2_C0_STRATEGY_KEY}.v1"] == (
        55_326_063
    )
    assert strategy_counts[f"{STRUCTURED_AFFINE_MOD5_A1_B3_C4_STRATEGY_KEY}.v1"] == (
        16_636_503
    )
    assert strategy_counts[f"{STRUCTURED_AFFINE_MOD5_A3_B1_C4_STRATEGY_KEY}.v1"] == (
        16_636_503
    )
    assert strategy_counts[f"{STRUCTURED_AFFINE_MOD7_A1_B3_C6_STRATEGY_KEY}.v1"] == (
        7_245_360
    )
    assert strategy_counts[f"{STRUCTURED_AFFINE_MOD7_A3_B1_C6_STRATEGY_KEY}.v1"] == (
        7_245_360
    )
    assert strategy_counts[f"{STRUCTURED_AFFINE_MOD4_A3_B2_C3_STRATEGY_KEY}.v1"] == (
        34_913_319
    )
    assert strategy_counts[f"{STRUCTURED_AFFINE_MOD4_A2_B3_C3_STRATEGY_KEY}.v1"] == (
        34_913_319
    )
    for spec in STRUCTURED_AFFINE_LOW_ORDER_TAIL_COMBO2_SPECS:
        assert strategy_counts[f"{spec['strategy_key']}.v1"] == spec["raw_coverage"]
    for spec in STRUCTURED_AFFINE_MOD11_TOP2_MATCHOP_NOHB_SPECS:
        assert strategy_counts[f"{spec['strategy_key']}.v1"] == spec["raw_coverage"]
    for spec in STRUCTURED_AFFINE_MOD11_COMBO9_MATCHOP_NOHB_SPECS:
        assert strategy_counts[f"{spec['strategy_key']}.v1"] == spec["raw_coverage"]
    for spec in STRUCTURED_AFFINE_LOW_ORDER_LE9_COMBO19_SPECS:
        assert strategy_counts[f"{spec['strategy_key']}.v1"] == spec["raw_coverage"]
    assert (
        strategy_counts[f"{AFFINE_MOD17_CANDIDATE6_SOURCEFIRST_STRATEGY_KEY}.v1"]
        == 3_063_823
    )
    assert summary["raw_false_union_covered"] == EXPECTED_RAW_FALSE_UNION_COVERED
    assert summary["conflict_count"] == 0


def test_affine_mod17_candidate6_sourcefirst_bank_row_is_registered(registry):
    strategy = next(
        strategy
        for strategy in registry.strategies
        if strategy.strategy_id
        == f"{AFFINE_MOD17_CANDIDATE6_SOURCEFIRST_STRATEGY_KEY}.v1"
    )

    assert strategy.priority == 664
    assert strategy.evidence["affine_modulus"] == 17
    assert strategy.evidence["affine_a"] == 2
    assert strategy.evidence["affine_b"] == 9
    assert strategy.evidence["affine_c"] == 0
    assert strategy.evidence["model_source_count"] == 49
    assert strategy.evidence["model_target_count"] == 62_527
    assert strategy.evidence["current_increment"] == 438_774
    assert strategy.evidence["raw_coverage"] == 3_063_823
    assert strategy.evidence["seed_candidate_key"] == (
        "false.finmodel.setcheck.affine_mod_probe.mod17.a2.b9.c0.all_equations"
    )
    assert strategy.evidence["official_smoke"]["accepted_count"] == 4
    assert strategy.evidence["official_smoke"]["total_count"] == 4


def test_revived_affine_mod17_packet_rows_are_registered(registry, summary):
    strategies_by_id = {
        strategy.strategy_id: strategy for strategy in registry.strategies
    }

    for row in REVIVED_MOD17_PACKET_ROWS:
        strategy_id = f"{row['strategy_key']}.v1"
        strategy = strategies_by_id[strategy_id]

        assert summary["strategy_counts"][strategy_id] == row["raw_coverage"]
        assert strategy.priority == row["priority"]
        assert strategy.evidence["affine_modulus"] == 17
        assert strategy.evidence["affine_a"] == row["a"]
        assert strategy.evidence["affine_b"] == row["b"]
        assert strategy.evidence["affine_c"] == 0
        assert strategy.evidence["model_source_count"] == row["source_count"]
        assert strategy.evidence["model_target_count"] == row["target_count"]
        assert strategy.evidence["current_increment"] == row["current_increment"]
        assert strategy.evidence["raw_coverage"] == row["raw_coverage"]
        assert strategy.evidence["current_true_overlap_count"] == 0
        assert strategy.evidence["seed_candidate_key"] == row["strategy_key"]
        assert strategy.evidence["official_smoke"]["status"] == "accepted"
        assert strategy.evidence["official_smoke"]["accepted_count"] == row[
            "smoke_accepted_count"
        ]


def test_top5_packet_setcheck_rows_are_registered(registry, summary):
    rows = _read_jsonl(TOP5_PACKET_SETCHECK_ROWS)
    assert len(rows) == 3

    for row in rows:
        strategy_id = f"{row['strategy_key']}.v1"
        strategy = next(
            strategy
            for strategy in registry.strategies
            if strategy.strategy_id == strategy_id
        )

        assert summary["strategy_counts"][strategy_id] == int(row["raw_coverage"])
        assert strategy.priority == int(row["priority"])
        assert strategy.evidence["model_source_count"] == int(row["source_count"])
        assert strategy.evidence["model_target_count"] == int(row["target_count"])
        assert strategy.evidence["current_increment"] == int(row["current_increment"])
        assert strategy.evidence["raw_coverage"] == int(row["raw_coverage"])
        assert strategy.evidence["current_true_overlap_count"] == 0
        assert strategy.evidence["official_smoke"]["status"] == "accepted"
        assert strategy.evidence["official_smoke"]["accepted_count"] == int(
            row["official_smoke"]["accepted_count"]
        )


def test_structured_affine_mod5_representative_pairs_are_covered(registry, law_count):
    expected = {
        f"{STRUCTURED_AFFINE_MOD5_A3_B2_C0_STRATEGY_KEY}.v1": [
            (211, 54684),
            (8209, 1832),
            (8222, 42406),
            (1, 54684),
        ],
        f"{STRUCTURED_AFFINE_MOD5_A2_B3_C0_STRATEGY_KEY}.v1": [
            (107, 60823),
            (7326, 4065),
            (7326, 54684),
            (1, 54684),
        ],
        f"{STRUCTURED_AFFINE_MOD4_A0_B1_C1_STRATEGY_KEY}.v1": [
            (413, 42406),
            (5572, 1832),
            (5572, 58192),
            (1, 43283),
        ],
        f"{STRUCTURED_AFFINE_MOD4_A1_B0_C3_STRATEGY_KEY}.v1": [
            (3051, 52053),
            (28375, 151),
            (28375, 51176),
            (1, 55561),
        ],
        f"{STRUCTURED_AFFINE_MOD5_A0_B1_C4_STRATEGY_KEY}.v1": [
            (4695, 3050),
            (4695, 44160),
            (1, 43283),
        ],
        f"{STRUCTURED_AFFINE_MOD5_A1_B0_C4_STRATEGY_KEY}.v1": [
            (40652, 411),
            (40652, 50299),
            (1, 55561),
        ],
        f"{STRUCTURED_ETP_ORDER4_REFUTATION516_STRATEGY_KEY}.v1": [
            (308, 54897),
            (41546, 3458),
            (41530, 54897),
            (1, 54897),
        ],
        f"{STRUCTURED_ETP_ORDER4_REFUTATION482_STRATEGY_KEY}.v1": [
            (50, 58192),
            (6452, 4065),
            (6452, 58192),
            (1, 54684),
        ],
        f"{STRUCTURED_ALL4X4_REFUTATION4_STRATEGY_KEY}.v1": [
            (503, 60828),
            (4787, 3867),
            (4787, 60828),
            (1, 54897),
        ],
        f"{STRUCTURED_AFFINE_MOD7_A2_B5_C6_STRATEGY_KEY}.v1": [
            (2294, 54684),
            (5572, 4065),
            (5572, 49422),
            (1, 54684),
        ],
        f"{STRUCTURED_AFFINE_MOD7_A5_B2_C6_STRATEGY_KEY}.v1": [
            (1313, 54684),
            (6539, 4065),
            (6539, 54684),
            (1, 54684),
        ],
        f"{STRUCTURED_AFFINE_MOD7_A6_B2_C0_STRATEGY_KEY}.v1": [
            (439, 53184),
            (4711, 1023),
            (4711, 44166),
            (1, 54897),
        ],
        f"{STRUCTURED_AFFINE_MOD5_A1_B3_C4_STRATEGY_KEY}.v1": [
            (160, 42406),
            (9983, 4065),
            (9983, 54684),
            (1, 54684),
        ],
        f"{STRUCTURED_AFFINE_MOD5_A3_B1_C4_STRATEGY_KEY}.v1": [
            (105, 60823),
            (4724, 4065),
            (4695, 52053),
            (1, 54684),
        ],
        f"{STRUCTURED_AFFINE_MOD7_A1_B3_C6_STRATEGY_KEY}.v1": [
            (1525, 54684),
            (6477, 4065),
            (6477, 54684),
            (1, 54684),
        ],
        f"{STRUCTURED_AFFINE_MOD7_A3_B1_C6_STRATEGY_KEY}.v1": [
            (1279, 42406),
            (5591, 2238),
            (5591, 58192),
            (1, 42406),
        ],
        f"{STRUCTURED_AFFINE_MOD4_A3_B2_C3_STRATEGY_KEY}.v1": [
            (1630, 38898),
            (18728, 1426),
            (18728, 38898),
            (1, 6449),
        ],
        f"{STRUCTURED_AFFINE_MOD4_A2_B3_C3_STRATEGY_KEY}.v1": [
            (1025, 52053),
            (13470, 4065),
            (13470, 52053),
            (1, 44160),
        ],
        f"{AFFINE_MOD17_CANDIDATE6_SOURCEFIRST_STRATEGY_KEY}.v1": [
            (5598, 3456),
            (5598, 11711),
            (1, 11711),
        ],
        **{
            f"{spec['strategy_key']}.v1": [
                pair
                for pair in spec["representative_pairs"].values()
                if pair is not None
            ]
            for spec in STRUCTURED_AFFINE_LOW_ORDER_TAIL_COMBO2_SPECS
        },
        **{
            f"{spec['strategy_key']}.v1": [
                pair
                for pair in spec["representative_pairs"].values()
                if pair is not None
            ]
            for spec in STRUCTURED_AFFINE_MOD11_TOP2_MATCHOP_NOHB_SPECS
        },
        **{
            f"{spec['strategy_key']}.v1": [
                pair
                for pair in spec["representative_pairs"].values()
                if pair is not None
            ]
            for spec in STRUCTURED_AFFINE_MOD11_COMBO9_MATCHOP_NOHB_SPECS
        },
        **{
            f"{spec['strategy_key']}.v1": [
                pair
                for pair in spec["representative_pairs"].values()
                if pair is not None
            ]
            for spec in STRUCTURED_AFFINE_LOW_ORDER_LE9_COMBO19_SPECS
        },
    }

    for strategy_id, representative_pairs in expected.items():
        for source_id, target_id in representative_pairs:
            pair_index = ids_to_pair_index(source_id, target_id, law_count=law_count)
            strategy_ids = [
                match["strategy_id"]
                for match in registry.find_covering_strategies(pair_index)
            ]

            assert strategy_id in strategy_ids


def test_structured_affine_mod5_evidence_points_to_smoke_artifacts(registry):
    expected = {
        f"{STRUCTURED_AFFINE_MOD5_A3_B2_C0_STRATEGY_KEY}.v1": (
            "affine_mod5_a3_b2_c0",
            2_445_837,
            4,
            4,
        ),
        f"{STRUCTURED_AFFINE_MOD5_A2_B3_C0_STRATEGY_KEY}.v1": (
            "affine_mod5_a2_b3_c0",
            2_431_039,
            4,
            4,
        ),
        f"{STRUCTURED_AFFINE_MOD4_A0_B1_C1_STRATEGY_KEY}.v1": (
            "affine_mod4_a0_b1_c1",
            2_050_881,
            4,
            4,
        ),
        f"{STRUCTURED_AFFINE_MOD4_A1_B0_C3_STRATEGY_KEY}.v1": (
            "affine_mod4_a1_b0_c3",
            2_044_868,
            4,
            4,
        ),
        f"{STRUCTURED_AFFINE_MOD5_A0_B1_C4_STRATEGY_KEY}.v1": (
            "affine_mod5_a0_b1_c4",
            1_639_526,
            3,
            3,
        ),
        f"{STRUCTURED_AFFINE_MOD5_A1_B0_C4_STRATEGY_KEY}.v1": (
            "affine_mod5_a1_b0_c4",
            1_639_189,
            3,
            3,
        ),
        f"{STRUCTURED_ETP_ORDER4_REFUTATION516_STRATEGY_KEY}.v1": (
            "etp_order4_refutation516",
            1_290_220,
            4,
            4,
        ),
        f"{STRUCTURED_ETP_ORDER4_REFUTATION482_STRATEGY_KEY}.v1": (
            "etp_order4_refutation482",
            1_141_366,
            4,
            4,
        ),
        f"{STRUCTURED_ALL4X4_REFUTATION4_STRATEGY_KEY}.v1": (
            "etp_refutation4",
            2_394_698,
            4,
            4,
        ),
        f"{STRUCTURED_AFFINE_MOD7_A2_B5_C6_STRATEGY_KEY}.v1": (
            "affine_mod7_a2_b5_c6",
            982_772,
            4,
            4,
        ),
        f"{STRUCTURED_AFFINE_MOD7_A5_B2_C6_STRATEGY_KEY}.v1": (
            "affine_mod7_a5_b2_c6",
            978_963,
            4,
            4,
        ),
        f"{STRUCTURED_AFFINE_MOD7_A6_B2_C0_STRATEGY_KEY}.v1": (
            "affine_mod7_a6_b2_c0",
            712_809,
            4,
            4,
        ),
        f"{STRUCTURED_AFFINE_MOD5_A1_B3_C4_STRATEGY_KEY}.v1": (
            "affine_mod5_a1_b3_c4",
            606_069,
            4,
            4,
        ),
        f"{STRUCTURED_AFFINE_MOD5_A3_B1_C4_STRATEGY_KEY}.v1": (
            "affine_mod5_a3_b1_c4",
            602_979,
            4,
            4,
        ),
        f"{STRUCTURED_AFFINE_MOD7_A1_B3_C6_STRATEGY_KEY}.v1": (
            "affine_mod7_a1_b3_c6",
            376_264,
            4,
            4,
        ),
        f"{STRUCTURED_AFFINE_MOD7_A3_B1_C6_STRATEGY_KEY}.v1": (
            "affine_mod7_a3_b1_c6",
            376_157,
            4,
            4,
        ),
        f"{STRUCTURED_AFFINE_MOD4_A3_B2_C3_STRATEGY_KEY}.v1": (
            "affine_mod4_a3_b2_c3",
            181_916,
            4,
            4,
        ),
        f"{STRUCTURED_AFFINE_MOD4_A2_B3_C3_STRATEGY_KEY}.v1": (
            "affine_mod4_a2_b3_c3",
            179_407,
            4,
            4,
        ),
        **{
            f"{spec['strategy_key']}.v1": (
                spec["label"],
                spec["current_increment"],
                len(
                    [
                        pair
                        for pair in spec["representative_pairs"].values()
                        if pair is not None
                    ]
                ),
                len(
                    [
                        pair
                        for pair in spec["representative_pairs"].values()
                        if pair is not None
                    ]
                ),
            )
            for spec in STRUCTURED_AFFINE_LOW_ORDER_TAIL_COMBO2_SPECS
        },
        **{
            f"{spec['strategy_key']}.v1": (
                spec["label"],
                spec["current_increment"],
                len(
                    [
                        pair
                        for pair in spec["representative_pairs"].values()
                        if pair is not None
                    ]
                ),
                len(
                    [
                        pair
                        for pair in spec["representative_pairs"].values()
                        if pair is not None
                    ]
                ),
            )
            for spec in STRUCTURED_AFFINE_MOD11_TOP2_MATCHOP_NOHB_SPECS
        },
        **{
            f"{spec['strategy_key']}.v1": (
                spec["label"],
                spec["current_increment"],
                len(spec["smoke_tiers"]),
                len(spec["smoke_tiers"]),
            )
            for spec in STRUCTURED_AFFINE_MOD11_COMBO9_MATCHOP_NOHB_SPECS
        },
        **{
            f"{spec['strategy_key']}.v1": (
                spec["label"],
                spec["current_increment"],
                len(spec["smoke_tiers"]),
                len(spec["smoke_tiers"]),
            )
            for spec in STRUCTURED_AFFINE_LOW_ORDER_LE9_COMBO19_SPECS
        },
    }

    for (
        strategy_id,
        (
            candidate_label,
            candidate_exact_increment,
            smoke_accepted_count,
            smoke_total_count,
        ),
    ) in expected.items():
        strategy = next(
            strategy
            for strategy in registry.strategies
            if strategy.strategy_id == strategy_id
        )

        assert strategy.evidence["candidate_label"] == candidate_label
        assert strategy.evidence["candidate_exact_increment"] == candidate_exact_increment
        assert strategy.evidence["remote_smoke_accepted_count"] == smoke_accepted_count
        assert strategy.evidence["remote_smoke_total_count"] == smoke_total_count


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
