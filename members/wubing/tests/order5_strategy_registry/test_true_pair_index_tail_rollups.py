import pytest

from math_distill_stage2.order5_strategy_registry import (
    DEFAULT_EQ_SIZE5_PATH,
    HINST_GROUND_CC_ACCEPTED_FAMILY_ROLLUP_STRATEGY_KEY,
    ONE_SIDED_CONSTANCY_COLUMN_RECURSIVE_NF_STRATEGY_KEY,
    ONE_SIDED_CONSTANCY_ROW_RECURSIVE_NF_STRATEGY_KEY,
    OPNORM_HCONST_DEFAULT_SANDWICH_GE25_LT100_TAIL_BATCH_STRATEGY_KEY,
    OPNORM_HCONST_DEFAULT_SANDWICH_LT25_REMAINING_TAIL_BATCH_STRATEGY_KEY,
    OPNORM_HCONST_PLUS_HSTEP_D14VC4_V17_TAIL_STRATEGY_KEY,
    OPNORM_HCONST_MATCH_GE10_TAIL_EXTENSION_STRATEGY_KEY,
    OPNORM_HCONST_MATCH_GE25K_TAIL_BATCH_STRATEGY_KEY,
    _build_hinst_ground_cc_accepted_family_rollup_strategy,
    _build_one_sided_constancy_column_recursive_nf_strategy,
    _build_one_sided_constancy_row_recursive_nf_strategy,
    _build_opnorm_hconst_default_sandwich_ge25_lt100_tail_batch_strategy,
    _build_opnorm_hconst_default_sandwich_lt25_remaining_tail_batch_strategy,
    _build_opnorm_hconst_match_ge10_tail_extension_strategy,
    _build_opnorm_hconst_match_ge25k_tail_batch_strategy,
    _build_opnorm_hconst_plus_hstep_d14vc4_v17_tail_strategy,
    find_true_strategy_ids_for_pair,
)


EXPECTED_TAIL_ROLLUPS = {
    OPNORM_HCONST_MATCH_GE25K_TAIL_BATCH_STRATEGY_KEY: {
        "builder": _build_opnorm_hconst_match_ge25k_tail_batch_strategy,
        "pair": (3270, 41655),
        "pair_count": 1_359_062,
        "union_increment": 1_359_062,
        "smoke_status": "accepted_64_of_64",
    },
    OPNORM_HCONST_MATCH_GE10_TAIL_EXTENSION_STRATEGY_KEY: {
        "builder": _build_opnorm_hconst_match_ge10_tail_extension_strategy,
        "pair": (340, 42467),
        "pair_count": 1_138_629,
        "union_increment": 1_138_629,
        "smoke_status": "accepted_134_of_134",
    },
    OPNORM_HCONST_DEFAULT_SANDWICH_GE25_LT100_TAIL_BATCH_STRATEGY_KEY: {
        "builder": _build_opnorm_hconst_default_sandwich_ge25_lt100_tail_batch_strategy,
        "pair": (314, 3473),
        "pair_count": 3_920_576,
        "union_increment": 3_920_576,
        "smoke_status": "accepted_324_of_324",
    },
    OPNORM_HCONST_DEFAULT_SANDWICH_LT25_REMAINING_TAIL_BATCH_STRATEGY_KEY: {
        "builder": _build_opnorm_hconst_default_sandwich_lt25_remaining_tail_batch_strategy,
        "pair": (337, 3342),
        "pair_count": 1_243_111,
        "union_increment": 1_243_111,
        "smoke_status": "accepted_288_of_288",
    },
    HINST_GROUND_CC_ACCEPTED_FAMILY_ROLLUP_STRATEGY_KEY: {
        "builder": _build_hinst_ground_cc_accepted_family_rollup_strategy,
        "pair": (38, 1),
        "pair_count": 4_622_829,
        "union_increment": 3_117_655,
        "smoke_status": "accepted_89_of_89",
    },
    OPNORM_HCONST_PLUS_HSTEP_D14VC4_V17_TAIL_STRATEGY_KEY: {
        "builder": _build_opnorm_hconst_plus_hstep_d14vc4_v17_tail_strategy,
        "pair": (317, 55594),
        "pair_count": 8_350_534,
        "union_increment": 1_317_879,
        "smoke_status": "accepted_1022_of_1022",
    },
}

EXPECTED_ONE_SIDED_CONSTANCY_STRATEGIES = {
    ONE_SIDED_CONSTANCY_ROW_RECURSIVE_NF_STRATEGY_KEY: {
        "builder": _build_one_sided_constancy_row_recursive_nf_strategy,
        "pair": (4, 1),
        "coverage_count": 6_287_120,
        "source_count": 3_139,
        "target_count": 2_003,
        "union_increment": 3_595_249,
        "smoke_status": "accepted_4_of_4",
        "candidate_key_fragment": "rhs_omits_right_arg.row_constancy_recursive_nf",
    },
    ONE_SIDED_CONSTANCY_COLUMN_RECURSIVE_NF_STRATEGY_KEY: {
        "builder": _build_one_sided_constancy_column_recursive_nf_strategy,
        "pair": (5, 1),
        "coverage_count": 6_287_120,
        "source_count": 3_139,
        "target_count": 2_003,
        "union_increment": 3_375_571,
        "smoke_status": "accepted_4_of_4",
        "candidate_key_fragment": "rhs_omits_left_arg.column_constancy_recursive_nf",
    },
}


@pytest.fixture(scope="module")
def strategies_by_key():
    return {
        strategy_key: expected["builder"](equations_path=DEFAULT_EQ_SIZE5_PATH)
        for strategy_key, expected in EXPECTED_TAIL_ROLLUPS.items()
    }


def test_true_tail_rollup_pair_index_strategies_load_registered_caches(
    strategies_by_key,
):
    for strategy_key, expected in EXPECTED_TAIL_ROLLUPS.items():
        strategy = strategies_by_key[strategy_key]
        source_id, target_id = expected["pair"]

        assert strategy.strategy_id == f"{strategy_key}.v1"
        assert strategy.verdict is True
        assert strategy.coverage_rule.coverage_kind == "compiler_pair_indexes"
        assert strategy.coverage_rule.covers(source_id, target_id)
        assert strategy.evidence["template_pair_count"] == expected["pair_count"]
        assert (
            strategy.evidence["template_current_union_increment"]
            == expected["union_increment"]
        )
        assert strategy.evidence["template_current_conflict_increment"] == 0
        assert (
            strategy.evidence["template_remote_smoke_status"]
            == expected["smoke_status"]
        )


def test_true_tail_rollup_pairs_are_discoverable_from_default_cache():
    for strategy_key, expected in EXPECTED_TAIL_ROLLUPS.items():
        source_id, target_id = expected["pair"]
        strategy_ids = find_true_strategy_ids_for_pair(source_id, target_id)

        assert f"{strategy_key}.v1" in strategy_ids


def test_one_sided_constancy_recursive_nf_strategies_load_candidate_sets():
    for strategy_key, expected in EXPECTED_ONE_SIDED_CONSTANCY_STRATEGIES.items():
        strategy = expected["builder"](equations_path=DEFAULT_EQ_SIZE5_PATH)
        source_id, target_id = expected["pair"]

        assert strategy.strategy_id == f"{strategy_key}.v1"
        assert strategy.verdict is True
        assert strategy.coverage_rule.coverage_kind == "source_target_sets"
        assert strategy.coverage_rule.covers(source_id, target_id)
        assert strategy.coverage_rule.coverage_count() == expected["coverage_count"]
        assert strategy.evidence["template_source_count"] == expected["source_count"]
        assert strategy.evidence["template_target_count"] == expected["target_count"]
        assert (
            strategy.evidence["template_current_union_increment"]
            == expected["union_increment"]
        )
        assert strategy.evidence["template_current_conflict_increment"] == 0
        assert (
            strategy.evidence["template_remote_smoke_status"]
            == expected["smoke_status"]
        )
        assert expected["candidate_key_fragment"] in str(
            strategy.evidence["template_candidate_key"]
        )


def test_one_sided_constancy_pairs_are_discoverable_from_default_candidate_sets():
    for strategy_key, expected in EXPECTED_ONE_SIDED_CONSTANCY_STRATEGIES.items():
        source_id, target_id = expected["pair"]
        strategy_ids = find_true_strategy_ids_for_pair(source_id, target_id)

        assert f"{strategy_key}.v1" in strategy_ids
