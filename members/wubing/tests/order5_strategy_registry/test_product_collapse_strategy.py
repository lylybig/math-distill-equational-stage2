from math_distill_stage2.order5_strategy_registry import (
    PRODUCT_COLLAPSE_STRATEGY_KEY_PREFIX,
    PRODUCT_COLLAPSE_TEMPLATES,
    find_true_strategy_ids_for_pair,
    product_collapse_true_judge_code,
)


def test_product_collapse_template_family_has_expected_shapes():
    assert len(PRODUCT_COLLAPSE_TEMPLATES) == 11
    assert {template["name"] for template in PRODUCT_COLLAPSE_TEMPLATES} == {
        "binary_square",
        "left_nested_3_distinct",
        "left_nested_repeat_inner_pair",
        "left_nested_repeat_outer_left",
        "left_nested_repeat_outer_right",
        "left_nested_triple_same",
        "right_nested_3_distinct",
        "right_nested_repeat_inner_pair",
        "right_nested_repeat_outer_inner_left",
        "right_nested_repeat_outer_inner_right",
        "right_nested_triple_same",
    }


def test_product_collapse_representative_pair_gets_true_strategy_id():
    strategy_id = (
        f"{PRODUCT_COLLAPSE_STRATEGY_KEY_PREFIX}.left_nested_3_distinct.v1"
    )

    strategy_ids = find_true_strategy_ids_for_pair(37, 59946, include_seedbank=False)

    assert strategy_id in strategy_ids


def test_product_collapse_renderer_emits_safe_true_certificate():
    code = product_collapse_true_judge_code(
        "x = (y * z) * w",
        "(x * x) * x = (x * x) * (x * x)",
        term_pattern="((v0*v1)*v2)",
    )

    assert "def submission : Goal := by" in code
    assert "intro G _ h" in code
    assert "exact" in code
    assert "h (x) (x) (x) (x)" in code
    assert "h (x) (x) (x) (x ◇ x)" in code
    for token in ("sorry", "admit", "axiom", "unsafe"):
        assert token not in code
