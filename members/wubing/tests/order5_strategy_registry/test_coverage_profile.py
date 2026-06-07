import pytest

import math_distill_stage2.order5_strategy_registry as strategy_registry_module
from math_distill_stage2.order5_coverage_profile import (
    build_coverage_profile,
    covered_targets_by_source_from_profile,
    coverage_delta_summary_from_profile,
    read_coverage_profile,
    write_coverage_profile,
)
from math_distill_stage2.order5_pair_space import ids_to_pair_index
from math_distill_stage2.order5_strategy_registry import (
    CompilerPairIndexesRule,
    CoverageStrategy,
    Order5StrategyRegistry,
    SourceTargetSetsRule,
)


def test_coverage_profile_delta_matches_registry_delta(tmp_path):
    registry = Order5StrategyRegistry(
        law_count=5,
        strategies=[
            CoverageStrategy(
                strategy_key="false.block",
                strategy_version=1,
                verdict=False,
                priority=20,
                coverage_rule=SourceTargetSetsRule(
                    source_ids=frozenset({1, 2}),
                    target_ids=frozenset({3, 4}),
                    excluded_blocks=((frozenset({2}), frozenset({4})),),
                ),
                certificate_family="false_block",
            ),
            CoverageStrategy(
                strategy_key="true.block",
                strategy_version=1,
                verdict=True,
                priority=30,
                coverage_rule=SourceTargetSetsRule(
                    source_ids=frozenset({2, 3}),
                    target_ids=frozenset({4, 5}),
                ),
                certificate_family="true_block",
            ),
            CoverageStrategy(
                strategy_key="true.explicit",
                strategy_version=1,
                verdict=True,
                priority=40,
                coverage_rule=strategy_registry_module.ExplicitPairsRule(
                    pair_indexes=frozenset(
                        {
                            ids_to_pair_index(1, 5, law_count=5),
                            ids_to_pair_index(4, 1, law_count=5),
                        }
                    ),
                    law_count=5,
                ),
                certificate_family="true_pair",
            ),
        ],
    )
    candidate_rule = SourceTargetSetsRule(
        source_ids=frozenset({1, 2, 4}),
        target_ids=frozenset({3, 4, 5}),
    )
    profile_path = tmp_path / "coverage_profile.json"

    profile = build_coverage_profile(registry)
    write_coverage_profile(profile, profile_path)
    reloaded_profile = read_coverage_profile(profile_path)

    assert coverage_delta_summary_from_profile(
        reloaded_profile,
        candidate_rule,
        verdict=False,
    ) == registry.coverage_delta_summary(candidate_rule, verdict=False)
    assert covered_targets_by_source_from_profile(
        reloaded_profile,
        verdict=True,
        source_ids={1, 2, 4},
    ) == {
        1: frozenset({5}),
        2: frozenset({4, 5}),
        4: frozenset({1}),
    }


def test_coverage_profile_delta_respects_exact_threshold():
    registry = Order5StrategyRegistry(law_count=5, strategies=[])
    profile = build_coverage_profile(registry)
    candidate_rule = SourceTargetSetsRule(
        source_ids=frozenset({1, 2, 3}),
        target_ids=frozenset({4, 5}),
    )

    with pytest.raises(ValueError, match="exceeds exact_pair_threshold"):
        coverage_delta_summary_from_profile(
            profile,
            candidate_rule,
            verdict=True,
            exact_pair_threshold=4,
        )


def test_coverage_profile_treats_compiler_pair_indexes_as_pair_rules():
    registry = Order5StrategyRegistry(
        law_count=5,
        strategies=[
            CoverageStrategy(
                strategy_key="true.compiler",
                strategy_version=1,
                verdict=True,
                priority=40,
                coverage_rule=CompilerPairIndexesRule(
                    pair_indexes=frozenset(
                        {
                            ids_to_pair_index(1, 5, law_count=5),
                            ids_to_pair_index(4, 1, law_count=5),
                        }
                    ),
                    law_count=5,
                    compiler_name="unit_compiler",
                ),
                certificate_family="compiler",
            )
        ],
    )
    profile = build_coverage_profile(registry)
    candidate_rule = strategy_registry_module.ExplicitPairsRule(
        pair_indexes=frozenset(
            {
                ids_to_pair_index(1, 5, law_count=5),
                ids_to_pair_index(2, 5, law_count=5),
            }
        ),
        law_count=5,
    )

    delta = coverage_delta_summary_from_profile(
        profile,
        candidate_rule,
        verdict=True,
    )

    assert delta["same_verdict_overlap"] == 1
    assert delta["union_increment"] == 1
