import json

import pytest

import math_distill_stage2.order5_strategy_registry as strategy_registry_module
from math_distill_stage2.order5_pair_space import ids_to_pair_index
from math_distill_stage2.order5_strategy_registry import (
    CompilerPairIndexesRule,
    CoverageStrategy,
    Order5StrategyRegistry,
    SourceTargetSetsRule,
    build_default_order5_strategy_registry,
    build_paircheck_bank_strategy,
    build_setcheck_bank_strategies,
    find_true_strategy_ids_for_pair,
    write_strategy_registry_outputs,
)


def test_explicit_pairs_rule_counts_and_covers_sparse_pairs():
    rule = strategy_registry_module.ExplicitPairsRule(
        pair_indexes=frozenset(
            {
                ids_to_pair_index(1, 2, law_count=3),
                ids_to_pair_index(2, 1, law_count=3),
            }
        ),
        law_count=3,
    )

    assert rule.coverage_kind == "explicit_pairs"
    assert rule.coverage_count() == 2
    assert rule.covers(1, 2)
    assert rule.covers(2, 1)
    assert not rule.covers(1, 3)


def test_registry_summary_counts_explicit_pairs_with_source_target_rules():
    false_block = CoverageStrategy(
        strategy_key="false.block",
        strategy_version=1,
        verdict=False,
        priority=10,
        coverage_rule=SourceTargetSetsRule(
            source_ids=frozenset({1}),
            target_ids=frozenset({2, 3}),
        ),
        certificate_family="block",
    )
    false_pair = CoverageStrategy(
        strategy_key="false.pair",
        strategy_version=1,
        verdict=False,
        priority=20,
        coverage_rule=strategy_registry_module.ExplicitPairsRule(
            pair_indexes=frozenset(
                {
                    ids_to_pair_index(1, 2, law_count=3),
                    ids_to_pair_index(2, 1, law_count=3),
                }
            ),
            law_count=3,
        ),
        certificate_family="paircheck",
    )
    registry = Order5StrategyRegistry(
        law_count=3,
        strategies=[false_block, false_pair],
    )

    summary = registry.coverage_summary()

    assert summary["raw_false_union_covered"] == 3
    assert summary["strategy_counts"]["false.pair.v1"] == 2
    assert summary["same_verdict_overlap"] == 1


def test_registry_summary_counts_compiler_pair_indexes_with_source_target_rules():
    true_block = CoverageStrategy(
        strategy_key="true.block",
        strategy_version=1,
        verdict=True,
        priority=10,
        coverage_rule=SourceTargetSetsRule(
            source_ids=frozenset({1}),
            target_ids=frozenset({2, 3}),
        ),
        certificate_family="block",
    )
    true_compiler_pairs = CoverageStrategy(
        strategy_key="true.compiler",
        strategy_version=1,
        verdict=True,
        priority=20,
        coverage_rule=CompilerPairIndexesRule(
            pair_indexes=frozenset(
                {
                    ids_to_pair_index(1, 2, law_count=3),
                    ids_to_pair_index(2, 1, law_count=3),
                }
            ),
            law_count=3,
            compiler_name="unit_compiler",
        ),
        certificate_family="compiler",
    )
    registry = Order5StrategyRegistry(
        law_count=3,
        strategies=[true_block, true_compiler_pairs],
    )

    summary = registry.coverage_summary()

    assert true_compiler_pairs.coverage_rule.coverage_kind == "compiler_pair_indexes"
    assert summary["raw_true_union_covered"] == 3
    assert summary["strategy_counts"]["true.compiler.v1"] == 2
    assert summary["same_verdict_overlap"] == 1


def test_conflict_count_intersects_explicit_pairs_with_source_target_rules():
    false_pair = CoverageStrategy(
        strategy_key="false.pair",
        strategy_version=1,
        verdict=False,
        priority=10,
        coverage_rule=strategy_registry_module.ExplicitPairsRule(
            pair_indexes=frozenset(
                {
                    ids_to_pair_index(2, 1, law_count=4),
                    ids_to_pair_index(3, 1, law_count=4),
                }
            ),
            law_count=4,
        ),
        certificate_family="paircheck",
    )
    true_block = CoverageStrategy(
        strategy_key="true.block",
        strategy_version=1,
        verdict=True,
        priority=20,
        coverage_rule=SourceTargetSetsRule(
            source_ids=frozenset({2, 4}),
            target_ids=frozenset({1}),
        ),
        certificate_family="template",
    )
    registry = Order5StrategyRegistry(
        law_count=4,
        strategies=[false_pair, true_block],
    )

    summary = registry.coverage_summary()

    assert summary["raw_false_union_covered"] == 2
    assert summary["raw_true_union_covered"] == 2
    assert summary["conflict_count"] == 1
    assert summary["deterministic_false_covered"] == 1
    assert summary["deterministic_true_covered"] == 1


def test_conflict_count_intersects_pair_index_rules_directly():
    false_pair = CoverageStrategy(
        strategy_key="false.pair",
        strategy_version=1,
        verdict=False,
        priority=10,
        coverage_rule=strategy_registry_module.ExplicitPairsRule(
            pair_indexes=frozenset(
                {
                    ids_to_pair_index(1, 2, law_count=4),
                    ids_to_pair_index(2, 3, law_count=4),
                }
            ),
            law_count=4,
        ),
        certificate_family="paircheck",
    )
    true_pair = CoverageStrategy(
        strategy_key="true.compiler",
        strategy_version=1,
        verdict=True,
        priority=20,
        coverage_rule=CompilerPairIndexesRule(
            pair_indexes=frozenset(
                {
                    ids_to_pair_index(1, 2, law_count=4),
                    ids_to_pair_index(3, 4, law_count=4),
                }
            ),
            law_count=4,
            compiler_name="unit_compiler",
        ),
        certificate_family="compiler",
    )
    registry = Order5StrategyRegistry(
        law_count=4,
        strategies=[false_pair, true_pair],
    )

    summary = registry.coverage_summary()

    assert summary["raw_false_union_covered"] == 2
    assert summary["raw_true_union_covered"] == 2
    assert summary["conflict_count"] == 1
    assert summary["deterministic_false_covered"] == 1
    assert summary["deterministic_true_covered"] == 1


def test_conflict_count_does_not_double_count_pair_rule_inside_source_overlap():
    false_block = CoverageStrategy(
        strategy_key="false.block",
        strategy_version=1,
        verdict=False,
        priority=10,
        coverage_rule=SourceTargetSetsRule(
            source_ids=frozenset({1}),
            target_ids=frozenset({2}),
        ),
        certificate_family="false_block",
    )
    false_pair = CoverageStrategy(
        strategy_key="false.pair",
        strategy_version=1,
        verdict=False,
        priority=20,
        coverage_rule=strategy_registry_module.ExplicitPairsRule(
            pair_indexes=frozenset({ids_to_pair_index(1, 2, law_count=4)}),
            law_count=4,
        ),
        certificate_family="paircheck",
    )
    true_block = CoverageStrategy(
        strategy_key="true.block",
        strategy_version=1,
        verdict=True,
        priority=30,
        coverage_rule=SourceTargetSetsRule(
            source_ids=frozenset({1}),
            target_ids=frozenset({2}),
        ),
        certificate_family="true_block",
    )
    registry = Order5StrategyRegistry(
        law_count=4,
        strategies=[false_block, false_pair, true_block],
    )

    summary = registry.coverage_summary()

    assert summary["raw_false_union_covered"] == 1
    assert summary["raw_true_union_covered"] == 1
    assert summary["conflict_count"] == 1
    assert summary["deterministic_false_covered"] == 0
    assert summary["deterministic_true_covered"] == 0


def test_registry_coverage_summary_can_report_timings():
    registry = Order5StrategyRegistry(
        law_count=4,
        strategies=[
            CoverageStrategy(
                strategy_key="false.example",
                strategy_version=1,
                verdict=False,
                priority=20,
                coverage_rule=SourceTargetSetsRule(
                    source_ids=frozenset({1}),
                    target_ids=frozenset({2}),
                ),
                certificate_family="example_family",
            )
        ],
    )

    summary = registry.coverage_summary(include_timings=True)

    assert summary["raw_false_union_covered"] == 1
    assert set(summary["timings_seconds"]) == {
        "active_strategy_filter_seconds",
        "strategy_counts_seconds",
        "verdict_partition_seconds",
        "false_union_seconds",
        "true_union_seconds",
        "conflict_count_seconds",
        "derived_counts_seconds",
        "total_seconds",
    }
    assert all(value >= 0 for value in summary["timings_seconds"].values())


def test_registry_all_order5_view_removes_source_target_exclusions():
    excluded_rule = SourceTargetSetsRule(
        source_ids=frozenset({1}),
        target_ids=frozenset({2}),
        excluded_blocks=((frozenset({1}), frozenset({2})),),
    )
    strategy = CoverageStrategy(
        strategy_key="true.block",
        strategy_version=1,
        verdict=True,
        priority=10,
        coverage_rule=excluded_rule,
        certificate_family="template",
    )
    registry = Order5StrategyRegistry(law_count=3, strategies=[strategy])

    legacy_summary = registry.coverage_summary()
    canonical = registry.without_source_target_exclusions()
    canonical_summary = canonical.coverage_summary()

    assert legacy_summary["raw_true_union_covered"] == 0
    assert legacy_summary["source_target_excluded_block_count"] == 1
    assert legacy_summary["coverage_scope"] == "source_target_sets_with_excluded_blocks"
    assert canonical_summary["raw_true_union_covered"] == 1
    assert canonical_summary["source_target_excluded_block_count"] == 0
    assert canonical_summary["coverage_scope"] == "all_order5_directed_nonself"
    assert canonical_summary["includes_order4_source_to_order4_target"] is True
    assert registry.strategies[0].coverage_rule.excluded_blocks
    assert not canonical.strategies[0].coverage_rule.excluded_blocks


def test_write_strategy_registry_outputs_writes_single_canonical_summary(tmp_path):
    strategy = CoverageStrategy(
        strategy_key="true.block",
        strategy_version=1,
        verdict=True,
        priority=10,
        coverage_rule=SourceTargetSetsRule(
            source_ids=frozenset({1}),
            target_ids=frozenset({2}),
            excluded_blocks=((frozenset({1}), frozenset({2})),),
        ),
        certificate_family="template",
    )
    registry = Order5StrategyRegistry(law_count=3, strategies=[strategy])

    strategies, summary = write_strategy_registry_outputs(registry, output_dir=tmp_path)

    written_strategies = json.loads((tmp_path / "strategies.json").read_text())
    written_summary = json.loads((tmp_path / "coverage_summary.json").read_text())
    assert strategies == written_strategies
    assert summary == written_summary
    assert summary["raw_true_union_covered"] == 1
    assert summary["source_target_excluded_block_count"] == 0
    assert written_strategies[0]["excluded_block_count"] == 0
    assert not (tmp_path / "coverage_summary_all_order5.json").exists()
    assert not (tmp_path / "strategies_all_order5.json").exists()


def test_registry_coverage_delta_summary_counts_overlap_and_conflict():
    false_block = CoverageStrategy(
        strategy_key="false.block",
        strategy_version=1,
        verdict=False,
        priority=20,
        coverage_rule=SourceTargetSetsRule(
            source_ids=frozenset({1}),
            target_ids=frozenset({2, 3}),
        ),
        certificate_family="false_family",
    )
    true_block = CoverageStrategy(
        strategy_key="true.block",
        strategy_version=1,
        verdict=True,
        priority=10,
        coverage_rule=SourceTargetSetsRule(
            source_ids=frozenset({2}),
            target_ids=frozenset({4}),
        ),
        certificate_family="true_family",
    )
    registry = Order5StrategyRegistry(
        law_count=4,
        strategies=[false_block, true_block],
    )
    candidate_rule = SourceTargetSetsRule(
        source_ids=frozenset({1, 2, 3}),
        target_ids=frozenset({2, 4}),
    )

    delta = registry.coverage_delta_summary(candidate_rule, verdict=False)

    assert delta == {
        "schema_version": 1,
        "verdict": False,
        "coverage_kind": "source_target_sets",
        "raw_coverage": 5,
        "same_verdict_overlap": 1,
        "opposite_verdict_overlap": 1,
        "conflict_increment": 1,
        "union_increment": 4,
        "candidate_verdict_deterministic_increment": 3,
        "total_deterministic_increment": 2,
        "unresolved_delta": -2,
    }


def test_registry_coverage_delta_summary_respects_exact_threshold():
    registry = Order5StrategyRegistry(law_count=5, strategies=[])
    candidate_rule = SourceTargetSetsRule(
        source_ids=frozenset({1, 2, 3}),
        target_ids=frozenset({4, 5}),
    )

    with pytest.raises(ValueError, match="exceeds exact_pair_threshold"):
        registry.coverage_delta_summary(
            candidate_rule,
            verdict=True,
            exact_pair_threshold=4,
        )


def test_find_true_strategy_ids_for_pair_detects_template_shape_conflicts(
    tmp_path,
):
    equations_path = tmp_path / "eq_size5.txt"
    equations_path.write_text(
        "\n".join(
            [
                "x = y * y",
                "x * x = y * y",
                "x = x * y",
                "x * z = x * w",
                "x * (x * y) = x",
                "z * (z * w) = z",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assert (
        "true.proof.templatecheck.singleton_collapse.any_target.v1"
        in find_true_strategy_ids_for_pair(
            1,
            2,
            equations_path=equations_path,
            order4_max_id=0,
            include_seedbank=False,
        )
    )
    assert (
        "true.proof.templatecheck.singleton_collapse.any_target.v1"
        in find_true_strategy_ids_for_pair(
            1,
            2,
            equations_path=equations_path,
            order4_max_id=6,
            include_seedbank=False,
        )
    )
    assert (
        "true.proof.templatecheck.projection_normalizer.left.any_left_normal_target.v1"
        in find_true_strategy_ids_for_pair(
            3,
            4,
            equations_path=equations_path,
            order4_max_id=0,
            include_seedbank=False,
        )
    )
    assert (
        "true.proof.templatecheck.law_instance.left_self_absorption.any_instance.v1"
        in find_true_strategy_ids_for_pair(
            5,
            6,
            equations_path=equations_path,
            order4_max_id=0,
            include_seedbank=False,
        )
    )
    assert (
        "true.proof.templatecheck.law_instance.target_instance_of_source.v1"
        in find_true_strategy_ids_for_pair(
            5,
            6,
            equations_path=equations_path,
            order4_max_id=0,
            include_seedbank=False,
        )
    )
    assert (
        find_true_strategy_ids_for_pair(
            2,
            1,
            equations_path=equations_path,
            order4_max_id=0,
            include_seedbank=False,
        )
        == []
    )


def test_target_instance_of_source_code_handles_direct_and_symmetric_targets():
    direct_code = strategy_registry_module.target_instance_of_source_true_judge_code(
        "x = y",
        "x * z = y * z",
    )

    assert "intro x z y" in direct_code
    assert "exact h (x ◇ z) (y ◇ z)" in direct_code

    symmetric_code = (
        strategy_registry_module.target_instance_of_source_true_judge_code(
            "x * (y * z) = (z * w) * u",
            "(x * y) * z = (z * x) * (z * x)",
        )
    )

    assert ".symm" in symmetric_code


def test_target_instance_of_source_explicit_pairs_on_small_equation_set(tmp_path):
    equations_path = tmp_path / "eq_size5.txt"
    equations_path.write_text(
        "\n".join(
            [
                "x = x",
                "x = y",
                "x * z = y * z",
                "(x * y) * z = (z * x) * (z * x)",
                "x * (y * z) = (z * w) * u",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    strategy = strategy_registry_module._build_target_instance_of_source_strategy(
        equations_path=equations_path,
        order4_max_id=0,
    )

    assert strategy.priority == 319
    assert strategy.coverage_rule.coverage_kind == "explicit_pairs"
    assert strategy.coverage_rule.covers(2, 3)
    assert strategy.coverage_rule.covers(5, 4)
    assert not strategy.coverage_rule.covers(2, 2)
    assert (
        "true.proof.templatecheck.law_instance.left_self_absorption.any_instance.v1"
        in strategy.supersedes_strategy_ids
    )

    matches = find_true_strategy_ids_for_pair(
        2,
        3,
        equations_path=equations_path,
        order4_max_id=0,
        include_seedbank=False,
    )
    assert (
        "true.proof.templatecheck.law_instance.target_instance_of_source.v1"
        in matches
    )


def test_source_level_singleton_code_wraps_bare_singleton_body():
    code = strategy_registry_module._source_level_singleton_proof_judge_code(
        "intro x y\nhave h0 := h x y\nexact h0",
        "x = y * y",
    )

    assert "have singleton : ∀ (x y : G), x = y := by" in code
    assert "  intro x y\n" in code
    assert "  exact singleton (x) (y ◇ y)" in code


def test_harvested_singleton_seed_proofs_accept_bare_singleton_body(tmp_path):
    proof_bank = tmp_path / "proof_bank"
    proof_sha = "ab" * 32
    (proof_bank / "proof_bodies" / proof_sha[:2]).mkdir(parents=True)
    (proof_bank / "proof_bodies" / proof_sha[:2] / f"{proof_sha}.lean").write_text(
        "intro x y\nhave h0 := h x y\nexact h0\n",
        encoding="utf-8",
    )
    problem_key = "problem:test"
    attempt_id = "attempt:test:000001"
    (proof_bank / "problems.jsonl").write_text(
        json.dumps(
            {
                "problem_key": problem_key,
                "eq1_id": 42,
                "eq1_signature": "v0=v1",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (proof_bank / "accepted.jsonl").write_text(
        json.dumps({"attempt_id": attempt_id}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (proof_bank / "attempts.jsonl").write_text(
        json.dumps(
            {
                "attempt_id": attempt_id,
                "official_judge_status": "accepted",
                "problem_key": problem_key,
                "proof_body_sha256": proof_sha,
                "source_run_id": "order5-top3-shape-singleton-like-20260521",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    strategy_registry_module._load_harvested_singleton_seed_proofs.cache_clear()
    try:
        proofs = strategy_registry_module._load_harvested_singleton_seed_proofs(
            proof_bank
        )
    finally:
        strategy_registry_module._load_harvested_singleton_seed_proofs.cache_clear()

    assert proofs[42] == (
        "v0=v1",
        "intro x y\nhave h0 := h x y\nexact h0\n",
    )


def test_harvested_singleton_seed_proofs_accept_phase1_seedgate_bare_body(tmp_path):
    proof_bank = tmp_path / "proof_bank"
    proof_sha = "cd" * 32
    (proof_bank / "proof_bodies" / proof_sha[:2]).mkdir(parents=True)
    (proof_bank / "proof_bodies" / proof_sha[:2] / f"{proof_sha}.lean").write_text(
        "intro x y\nhave h0 := h x y\nexact h0\n",
        encoding="utf-8",
    )
    problem_key = "problem:test"
    attempt_id = "attempt:test:000001"
    (proof_bank / "problems.jsonl").write_text(
        json.dumps(
            {
                "problem_key": problem_key,
                "eq1_id": 42,
                "eq1_signature": "v0=v1",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (proof_bank / "accepted.jsonl").write_text(
        json.dumps({"attempt_id": attempt_id}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (proof_bank / "attempts.jsonl").write_text(
        json.dumps(
            {
                "attempt_id": attempt_id,
                "official_judge_status": "accepted",
                "problem_key": problem_key,
                "proof_body_sha256": proof_sha,
                "source_run_id": "topshape-seedgate-phase1-20260518",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    strategy_registry_module._load_harvested_singleton_seed_proofs.cache_clear()
    try:
        proofs = strategy_registry_module._load_harvested_singleton_seed_proofs(
            proof_bank
        )
    finally:
        strategy_registry_module._load_harvested_singleton_seed_proofs.cache_clear()

    assert proofs[42] == (
        "v0=v1",
        "intro x y\nhave h0 := h x y\nexact h0\n",
    )


def test_singleton_seedbank_specialization_uses_harvested_bare_proof_body(
    monkeypatch,
    tmp_path,
):
    seed_equation = strategy_registry_module._parse_stage2_equation("a = b")
    proof_source_path = tmp_path / "empty_solver.py"
    proof_source_path.write_text(
        "_MAGMAEGG_SINGLETON_PROOF_BODIES = {}\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        strategy_registry_module,
        "_match_singleton_seedbank_specialization",
        lambda source, equations_path: (
            4242,
            seed_equation,
            "direct",
            {
                "x": seed_equation.left,
                "y": seed_equation.right,
            },
        ),
    )
    monkeypatch.setattr(
        strategy_registry_module,
        "_load_harvested_singleton_seed_proofs",
        lambda proof_bank_path: {
            4242: ("v0=v1", "intro x y\nhave h0 := h x y\nexact h0\n")
        },
    )

    code = strategy_registry_module.singleton_seedbank_specialization_true_judge_code(
        "x = y",
        "u = v",
        proof_source_path=proof_source_path,
    )

    assert "have h : ∀ (a b : G), a = b := by" in code
    assert "have singleton : ∀ (x y : G), x = y := by" in code
    assert "  exact singleton (u) (v)" in code


def test_build_paircheck_bank_strategy_loads_registry_ready_pairs(tmp_path):
    bank_path = tmp_path / "registry_ready_bank.jsonl"
    pair_a = ids_to_pair_index(1, 2, law_count=4)
    pair_b = ids_to_pair_index(3, 4, law_count=4)
    bank_path.write_text(
        "\n".join(
            json.dumps(row, sort_keys=True)
            for row in [
                {"pair_index": pair_b, "registry_ready": True},
                {"pair_index": pair_a, "registry_ready": True},
                {"pair_index": pair_a, "registry_ready": True},
                {"pair_index": ids_to_pair_index(2, 1, law_count=4), "registry_ready": False},
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    strategy = build_paircheck_bank_strategy(
        bank_path=bank_path,
        law_count=4,
        priority=400,
    )

    assert strategy.strategy_id == "false.finmodel.paircheck.bank.v1"
    assert strategy.verdict is False
    assert strategy.priority == 400
    assert strategy.coverage_count() == 2
    assert strategy.covers(1, 2)
    assert strategy.covers(3, 4)
    assert not strategy.covers(2, 1)
    assert strategy.manifest_record()["pair_bank_path"] == str(bank_path)


def test_build_setcheck_bank_strategies_loads_active_models(tmp_path):
    equations_path = tmp_path / "eq_size5.txt"
    equations_path.write_text(
        "\n".join(["x * y = x", "x * y = y", "x = x"]) + "\n",
        encoding="utf-8",
    )
    bank_path = tmp_path / "discovered_setcheck_bank.jsonl"
    bank_path.write_text(
        "\n".join(
            json.dumps(row, sort_keys=True)
            for row in [
                {
                    "schema_version": 1,
                    "active": True,
                    "strategy_key": (
                        "false.finmodel.setcheck.bank.test_left_projection"
                    ),
                    "priority": 360,
                    "label": "test_left_projection",
                    "table": [[0, 0], [1, 1]],
                    "current_increment": 2,
                    "provenance": "unit_test",
                },
                {
                    "schema_version": 1,
                    "active": False,
                    "strategy_key": "false.finmodel.setcheck.bank.inactive",
                    "priority": 361,
                    "label": "inactive",
                    "table": [[0, 1], [0, 1]],
                },
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    [strategy] = build_setcheck_bank_strategies(
        bank_path=bank_path,
        equations_path=equations_path,
        order4_max_id=0,
    )

    assert strategy.strategy_id == "false.finmodel.setcheck.bank.test_left_projection.v1"
    assert strategy.priority == 360
    assert strategy.coverage_count() == 2
    assert strategy.covers(1, 2)
    assert strategy.covers(3, 2)
    assert not strategy.covers(2, 1)
    manifest = strategy.manifest_record()
    assert manifest["setcheck_bank_path"] == str(bank_path)
    assert manifest["discovery_label"] == "test_left_projection"
    assert manifest["current_increment"] == 2


def test_build_setcheck_bank_strategies_loads_affine_rows_symbolically(tmp_path):
    equations_path = tmp_path / "eq_size5.txt"
    equations_path.write_text(
        "\n".join(
            [
                "x = x",
                "x = y",
                "x * x = y * y",
                "x * y = y * x",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    bank_path = tmp_path / "discovered_setcheck_bank.jsonl"
    bank_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "active": True,
                "strategy_key": "false.finmodel.setcheck.bank.test_affine_mod3",
                "priority": 624,
                "label": "test_affine_mod3",
                "table": [[0, 1, 2], [2, 0, 1], [1, 2, 0]],
                "modulus": 3,
                "a": 2,
                "b": 1,
                "c": 0,
                "current_increment": 4,
                "current_true_overlap_count": 0,
                "provenance": "unit_test_affine_bank_row",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    [strategy] = build_setcheck_bank_strategies(
        bank_path=bank_path,
        equations_path=equations_path,
        order4_max_id=0,
    )

    assert strategy.strategy_id == "false.finmodel.setcheck.bank.test_affine_mod3.v1"
    assert strategy.priority == 624
    assert strategy.coverage_count() == 4
    assert strategy.covers(1, 2)
    assert strategy.covers(3, 4)
    assert not strategy.covers(2, 1)
    manifest = strategy.manifest_record()
    assert manifest["affine_modulus"] == 3
    assert manifest["affine_a"] == 2
    assert manifest["affine_b"] == 1
    assert manifest["affine_c"] == 0
    assert manifest["source_set_method"] == "symbolic_affine_mod_linear_coefficients"
    assert manifest["current_true_overlap_count"] == 0


def test_default_registry_includes_setcheck_bank_when_path_is_provided(tmp_path):
    equations_path = tmp_path / "eq_size5.txt"
    equations_path.write_text(
        "\n".join(["x * y = x", "x * y = y", "x = x"]) + "\n",
        encoding="utf-8",
    )
    bank_path = tmp_path / "discovered_setcheck_bank.jsonl"
    bank_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "strategy_key": "false.finmodel.setcheck.bank.test_left_projection",
                "priority": 360,
                "label": "test_left_projection",
                "table": [[0, 0], [1, 1]],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    registry = build_default_order5_strategy_registry(
        equations_path=equations_path,
        order4_max_id=0,
        include_true_strategies=False,
        paircheck_bank_path=None,
        setcheck_bank_path=bank_path,
    )

    assert any(
        strategy.strategy_id
        == "false.finmodel.setcheck.bank.test_left_projection.v1"
        for strategy in registry.strategies
    )
