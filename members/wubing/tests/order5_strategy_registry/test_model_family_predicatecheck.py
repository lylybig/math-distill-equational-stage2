from pathlib import Path
import json

import pytest

from math_distill_stage2.order5_pair_space import ids_to_pair_index
from math_distill_stage2.order5_strategy_registry import (
    DEFAULT_EQ_SIZE5_PATH,
    DEFAULT_SOURCE_TARGET_CACHE_PATH,
    MODEL_FAMILY_PREDICATECHECK_SHARDS,
    MODEL_FAMILY_PREDICATECHECK_STRATEGY_KEY_PREFIX,
    build_default_order5_strategy_registry,
)


K40_PREDICATECHECK_PREFIX = (
    "false.finmodel.predicatecheck.etp_prefix_family.k40."
    "source_any_target_all_refuted"
)
TOP80_MIN25K_PREFIX = (
    "false.finmodel.predicatecheck.model_family.beam_after_k40."
    "top80_min25k"
)
PLUS_SAMPLE30000_PREFIX = f"{TOP80_MIN25K_PREFIX}.plus_sample30000"
COMBINED_MUTATED_STRUCTURED_PREFIX = (
    f"{TOP80_MIN25K_PREFIX}.combined_mutated_structured.batch03"
)
POST_FRONTIER_Z3_PREFIX = (
    "false.finmodel.predicatecheck.model_family.beam_after_k40."
    "post_frontier_z3.batch01"
)
TOP80_MIN25K_SMOKED_CANDIDATES = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "false_predicate_beam_family_after_k40_batch_greedy_top80_min25k_smoked_"
    "20260521.jsonl"
)
PLUS_SAMPLE30000_SMOKED_CANDIDATES = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "false_predicate_beam_family_after_top80_min25k_combined_plus_sample30000_"
    "top40_min25k_smoked_20260521.jsonl"
)
CONTROLLER_SMOKE_MERGE_SELECTION = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "false_controller_current_smoke_merge_selection_20260521.jsonl"
)
POST_FRONTIER_Z3_MERGE_SELECTION = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "false_controller_to_date_predicate_family_current_merge_selection_20260522.jsonl"
)
TOP5_PACKET_PREDICATECHECK_ROWS = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "false_postcanonical_joint_min1m_oldhigh_mod17_nonmod17_top5_predicatecheck_rows_20260527.jsonl"
)
EXPECTED_RAW_FALSE_UNION_COVERED = 2_384_904_817


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


def test_default_registry_includes_model_family_predicatecheck_shards(summary):
    shard_ids = [
        f"{MODEL_FAMILY_PREDICATECHECK_STRATEGY_KEY_PREFIX}.{shard['name']}.v1"
        for shard in MODEL_FAMILY_PREDICATECHECK_SHARDS
    ]

    assert len(shard_ids) == 6
    assert all(strategy_id in summary["strategy_counts"] for strategy_id in shard_ids)
    assert sum(summary["strategy_counts"][strategy_id] for strategy_id in shard_ids) == (
        309_164_544
    )
    assert summary["raw_false_union_covered"] == EXPECTED_RAW_FALSE_UNION_COVERED
    assert summary["conflict_count"] == 0


def test_model_family_predicatecheck_shards_match_review_packet(summary):
    shard_counts = {
        strategy_id: count
        for strategy_id, count in summary["strategy_counts"].items()
        if strategy_id.startswith(MODEL_FAMILY_PREDICATECHECK_STRATEGY_KEY_PREFIX)
    }

    assert shard_counts == {
        f"{MODEL_FAMILY_PREDICATECHECK_STRATEGY_KEY_PREFIX}.witness_shard_1_enum_order3_345.v1": 159_441_552,
        f"{MODEL_FAMILY_PREDICATECHECK_STRATEGY_KEY_PREFIX}.witness_shard_2_enum_order3_1521.v1": 46_248_912,
        f"{MODEL_FAMILY_PREDICATECHECK_STRATEGY_KEY_PREFIX}.witness_shard_3_enum_order3_3651.v1": 48_021_120,
        f"{MODEL_FAMILY_PREDICATECHECK_STRATEGY_KEY_PREFIX}.witness_shard_4_enum_order3_425.v1": 5_430_960,
        f"{MODEL_FAMILY_PREDICATECHECK_STRATEGY_KEY_PREFIX}.witness_shard_5_enum_order3_553.v1": 39_274_416,
        f"{MODEL_FAMILY_PREDICATECHECK_STRATEGY_KEY_PREFIX}.witness_shard_6_enum_order3_659.v1": 10_747_584,
    }


def test_model_family_predicatecheck_representative_pairs_have_expected_shards(
    registry,
    law_count: int,
):
    expected = {
        (9, 43527): "witness_shard_1_enum_order3_345",
        (4747, 3667): "witness_shard_1_enum_order3_345",
        (4696, 43527): "witness_shard_1_enum_order3_345",
        (41753, 4287): "witness_shard_2_enum_order3_1521",
        (19958, 1647): "witness_shard_3_enum_order3_3651",
        (10900, 1039): "witness_shard_4_enum_order3_425",
        (22244, 3315): "witness_shard_5_enum_order3_553",
        (16998, 1647): "witness_shard_6_enum_order3_659",
    }

    for pair, shard_name in expected.items():
        pair_index = ids_to_pair_index(*pair, law_count=law_count)
        matches = registry.find_covering_strategies(pair_index)
        shard_ids = [
            match["strategy_id"]
            for match in matches
            if match["strategy_id"].startswith(MODEL_FAMILY_PREDICATECHECK_STRATEGY_KEY_PREFIX)
        ]

        assert shard_ids == [
            f"{MODEL_FAMILY_PREDICATECHECK_STRATEGY_KEY_PREFIX}.{shard_name}.v1"
        ]


def test_predicatecheck_bank_k40_family_matches_candidate_packet(summary):
    shard_counts = {
        strategy_id: count
        for strategy_id, count in summary["strategy_counts"].items()
        if strategy_id.startswith(K40_PREDICATECHECK_PREFIX)
    }

    assert len(shard_counts) == 26
    assert sum(shard_counts.values()) == 721_978_044
    assert summary["raw_false_union_covered"] == EXPECTED_RAW_FALSE_UNION_COVERED
    assert summary["conflict_count"] == 0


def test_predicatecheck_bank_k40_representative_pairs_are_covered(
    registry,
    law_count: int,
):
    for pair in [(25, 45254), (5573, 413), (5573, 49629), (1, 7326)]:
        pair_index = ids_to_pair_index(*pair, law_count=law_count)
        matches = registry.find_covering_strategies(pair_index)
        assert any(
            match["strategy_id"].startswith(K40_PREDICATECHECK_PREFIX)
            for match in matches
        )


def test_predicatecheck_bank_top80_min25k_matches_candidate_packet(summary):
    candidate_rows = _read_jsonl(TOP80_MIN25K_SMOKED_CANDIDATES)
    assert len(candidate_rows) == 6

    shard_counts = {
        strategy_id: count
        for strategy_id, count in summary["strategy_counts"].items()
        if strategy_id.startswith(f"{TOP80_MIN25K_PREFIX}.batch")
    }

    assert shard_counts
    assert sum(shard_counts.values()) == sum(
        int(row["raw_coverage"]) for row in candidate_rows
    )
    assert summary["raw_false_union_covered"] == EXPECTED_RAW_FALSE_UNION_COVERED
    assert summary["conflict_count"] == 0


def test_predicatecheck_bank_plus_sample30000_matches_candidate_packet(summary):
    candidate_rows = _read_jsonl(PLUS_SAMPLE30000_SMOKED_CANDIDATES)
    assert len(candidate_rows) == 4

    shard_counts = {
        strategy_id: count
        for strategy_id, count in summary["strategy_counts"].items()
        if strategy_id.startswith(PLUS_SAMPLE30000_PREFIX)
    }

    assert shard_counts
    assert sum(shard_counts.values()) == sum(
        int(row["raw_coverage"]) for row in candidate_rows
    )
    assert summary["raw_false_union_covered"] == EXPECTED_RAW_FALSE_UNION_COVERED
    assert summary["conflict_count"] == 0


def test_predicatecheck_bank_combined_mutated_structured_matches_controller_selection(
    summary,
):
    candidate_rows = _read_jsonl(CONTROLLER_SMOKE_MERGE_SELECTION)
    assert len(candidate_rows) == 1

    shard_counts = {
        strategy_id: count
        for strategy_id, count in summary["strategy_counts"].items()
        if strategy_id.startswith(COMBINED_MUTATED_STRUCTURED_PREFIX)
    }

    assert len(shard_counts) == 4
    assert sum(shard_counts.values()) == int(candidate_rows[0]["raw_coverage"])
    assert summary["raw_false_union_covered"] == EXPECTED_RAW_FALSE_UNION_COVERED
    assert summary["conflict_count"] == 0


def test_predicatecheck_bank_post_frontier_z3_matches_controller_selection(summary):
    candidate_rows = _read_jsonl(POST_FRONTIER_Z3_MERGE_SELECTION)
    assert len(candidate_rows) == 1
    assert int(candidate_rows[0]["exact_union_increment"]) == 59_038
    assert int(candidate_rows[0]["true_overlap_count"]) == 0

    shard_counts = {
        strategy_id: count
        for strategy_id, count in summary["strategy_counts"].items()
        if strategy_id.startswith(POST_FRONTIER_Z3_PREFIX)
    }

    assert len(shard_counts) == 4
    assert sum(shard_counts.values()) == int(candidate_rows[0]["raw_coverage"])
    assert summary["raw_false_union_covered"] == EXPECTED_RAW_FALSE_UNION_COVERED
    assert summary["conflict_count"] == 0


def test_top5_packet_predicatecheck_rows_are_registered(summary, registry):
    rows = _read_jsonl(TOP5_PACKET_PREDICATECHECK_ROWS)
    assert len(rows) == 2

    for row in rows:
        strategy_prefix = f"{row['strategy_key']}."
        shard_counts = {
            strategy_id: count
            for strategy_id, count in summary["strategy_counts"].items()
            if strategy_id.startswith(strategy_prefix)
        }

        assert len(shard_counts) == int(row["model_family_size"])
        assert sum(shard_counts.values()) == int(row["raw_coverage"])

        shards = [
            strategy
            for strategy in registry.strategies
            if strategy.strategy_id.startswith(strategy_prefix)
        ]
        assert len(shards) == int(row["model_family_size"])
        assert {strategy.evidence["model_label"] for strategy in shards} == set(
            row["model_labels"]
        )
        for strategy in shards:
            assert strategy.evidence["expected_family_source_count"] == int(
                row["source_count"]
            )
            assert strategy.evidence["expected_family_target_count"] == int(
                row["target_count"]
            )
            assert strategy.evidence["expected_raw_coverage"] == int(
                row["raw_coverage"]
            )
            assert strategy.evidence["official_smoke"]["status"] == "accepted"
            assert strategy.evidence["official_smoke"]["accepted_count"] == int(
                row["official_smoke"]["accepted_count"]
            )


def test_predicatecheck_bank_top80_min25k_representative_pairs_are_covered(
    registry,
    law_count: int,
):
    for row in _read_jsonl(TOP80_MIN25K_SMOKED_CANDIDATES):
        batch_index = int(row["batch_selection"]["batch_index"])
        strategy_prefix = f"{TOP80_MIN25K_PREFIX}.batch{batch_index:02d}"
        for pair in row["representative_pairs"].values():
            if pair is None:
                continue
            pair_index = ids_to_pair_index(*pair, law_count=law_count)
            matches = registry.find_covering_strategies(pair_index)
            assert any(
                match["strategy_id"].startswith(strategy_prefix)
                for match in matches
            )


def test_predicatecheck_bank_plus_sample30000_representative_pairs_are_covered(
    registry,
    law_count: int,
):
    for row in _read_jsonl(PLUS_SAMPLE30000_SMOKED_CANDIDATES):
        batch_index = int(row["batch_selection"]["batch_index"])
        strategy_prefix = f"{PLUS_SAMPLE30000_PREFIX}.batch{batch_index:02d}"
        for pair in row["representative_pairs"].values():
            if pair is None:
                continue
            pair_index = ids_to_pair_index(*pair, law_count=law_count)
            matches = registry.find_covering_strategies(pair_index)
            assert any(
                match["strategy_id"].startswith(strategy_prefix)
                for match in matches
            )


def test_predicatecheck_bank_combined_mutated_structured_representative_pairs_are_covered(
    registry,
    law_count: int,
):
    row = _read_jsonl(CONTROLLER_SMOKE_MERGE_SELECTION)[0]

    for pair in row["representative_pairs"].values():
        if pair is None:
            continue
        pair_index = ids_to_pair_index(*pair, law_count=law_count)
        matches = registry.find_covering_strategies(pair_index)
        assert any(
            match["strategy_id"].startswith(COMBINED_MUTATED_STRUCTURED_PREFIX)
            for match in matches
        )


def test_predicatecheck_bank_post_frontier_z3_representative_pairs_are_covered(
    registry,
    law_count: int,
):
    row = _read_jsonl(POST_FRONTIER_Z3_MERGE_SELECTION)[0]

    for pair in row["representative_pairs"].values():
        if pair is None:
            continue
        pair_index = ids_to_pair_index(*pair, law_count=law_count)
        matches = registry.find_covering_strategies(pair_index)
        assert any(
            match["strategy_id"].startswith(POST_FRONTIER_Z3_PREFIX)
            for match in matches
        )


def test_top5_packet_predicatecheck_representative_pairs_are_covered(
    registry,
    law_count: int,
):
    for row in _read_jsonl(TOP5_PACKET_PREDICATECHECK_ROWS):
        strategy_prefix = f"{row['strategy_key']}."
        for pair in row["representative_pairs"].values():
            if pair is None:
                continue
            pair_index = ids_to_pair_index(*pair, law_count=law_count)
            matches = registry.find_covering_strategies(pair_index)
            assert any(
                match["strategy_id"].startswith(strategy_prefix) for match in matches
            )


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
