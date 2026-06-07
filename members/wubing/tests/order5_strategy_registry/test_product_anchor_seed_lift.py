import pytest

from math_distill_stage2.order5_product_anchor_seed_lift import (
    render_product_anchor_seed_lift_certificate,
)
from math_distill_stage2.order5_strategy_registry import (
    DEFAULT_EQ_SIZE5_PATH,
    DEFAULT_ORDER4_MAX_ID,
    PRODUCT_ANCHOR_SEED_LIFT_ANY_PRODUCT_TARGET_STRATEGY_KEY,
    _build_product_anchor_seed_lift_strategy,
    _product_anchor_seed_lift_sets,
    find_true_strategy_ids_for_pair,
    product_anchor_seed_lift_true_judge_answer,
)


SOURCE_TO_SEED_PROOF_BODY = """intro x y z w
calc
  _ = _ := by exact h x y (z ◇ w) x
  _ = _ := by exact h (z ◇ w) (x ◇ x) z w
"""


def test_product_anchor_seed_lift_renderer_composes_seed_proof_with_target():
    code = render_product_anchor_seed_lift_certificate(
        seed_equation="x * y = z * (w * (z * w))",
        target_equation="x * x = x * (x * (x * (x * x)))",
        source_to_seed_proof_body=SOURCE_TO_SEED_PROOF_BODY,
    )

    assert "def submission : Goal := by" in code
    assert "intro G _ h" in code
    assert "have h_seed : ∀ (x y z w : G)" in code
    assert "exact h x y (z ◇ w) x" in code
    assert "have allprod : ∀ (p q r s : G), p ◇ q = r ◇ s" in code
    assert "exact (h_seed p q p p).trans (h_seed r s p p).symm" in code
    assert "intro x" in code
    assert "\\n" not in code
    for token in ("sorry", "admit", "axiom", "unsafe"):
        assert token not in code


def test_product_anchor_seed_lift_rejects_non_product_anchor_seed():
    with pytest.raises(ValueError, match="product-anchor"):
        render_product_anchor_seed_lift_certificate(
            seed_equation="x = y",
            target_equation="x * x = y * y",
            source_to_seed_proof_body=SOURCE_TO_SEED_PROOF_BODY,
        )


def test_product_anchor_seed_lift_rejects_non_product_root_target():
    with pytest.raises(ValueError, match="product-root"):
        render_product_anchor_seed_lift_certificate(
            seed_equation="x * y = z * (w * (z * w))",
            target_equation="x = y * y",
            source_to_seed_proof_body=SOURCE_TO_SEED_PROOF_BODY,
        )


def test_product_anchor_seed_lift_registry_candidate_sets_use_tail_bank():
    _, source_ids, target_ids, counts = _product_anchor_seed_lift_sets(
        DEFAULT_EQ_SIZE5_PATH
    )

    assert source_ids == frozenset({354, 398, 3821, 3988, 4191, 4218})
    assert len(target_ids) == 22603
    assert counts["candidate_source_count"] == 6
    assert counts["source_signature_mismatch_count"] == 0

    strategy = _build_product_anchor_seed_lift_strategy(
        equations_path=DEFAULT_EQ_SIZE5_PATH,
        order4_max_id=DEFAULT_ORDER4_MAX_ID,
    )
    manifest = strategy.manifest_record()
    assert strategy.strategy_key == PRODUCT_ANCHOR_SEED_LIFT_ANY_PRODUCT_TARGET_STRATEGY_KEY
    assert manifest["source_count"] == 6
    assert manifest["target_count"] == 22603
    assert manifest["excluded_block_count"] == 0
    assert manifest["coverage_count"] == 135612
    assert manifest["candidate_exact_union_increment"] == 124237
    assert manifest["remote_smoke_accepted_count"] == 18
    assert manifest["remote_smoke_total_count"] == 18


def test_product_anchor_seed_lift_true_strategy_lookup_and_code_generation():
    strategy_id = f"{PRODUCT_ANCHOR_SEED_LIFT_ANY_PRODUCT_TARGET_STRATEGY_KEY}.v1"

    assert strategy_id in find_true_strategy_ids_for_pair(354, 41529)
    assert strategy_id not in find_true_strategy_ids_for_pair(354, 2)
    assert strategy_id not in find_true_strategy_ids_for_pair(
        354,
        41529,
        include_seedbank=False,
    )

    answer = product_anchor_seed_lift_true_judge_answer(
        354,
        "x * x = x * (x * (x * (x * x)))",
    )
    assert answer["verdict"] == "true"
    assert "have h_seed" in answer["code"]
    assert "have allprod : ∀ (p q r s : G), p ◇ q = r ◇ s" in answer["code"]
    assert "exact allprod" in answer["code"]
