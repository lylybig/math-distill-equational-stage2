from math_distill_stage2.equations import parse_equation
from math_distill_stage2.order5_egraph_proof_search import (
    find_rewrite_proof,
    render_true_certificate,
)


def test_context_renderer_parenthesizes_right_nested_nonhole_subterm():
    proof = find_rewrite_proof(
        parse_equation("x = x * (x * x)"),
        parse_equation("x = (x * (x * x)) * (x * x)"),
        max_steps=5,
        max_term_size=9,
        max_nodes=5000,
    )

    assert proof is not None
    code = render_true_certificate(proof.source, proof.target, proof)

    assert "fun t => (t ◇ (x ◇ x))" in code
    assert "fun t => (t ◇ x ◇ x)" not in code


def test_context_renderer_parenthesizes_left_nested_nonhole_subterm():
    proof = find_rewrite_proof(
        parse_equation("x = (x * x) * x"),
        parse_equation("x = (x * x) * ((x * x) * x)"),
        max_steps=5,
        max_term_size=9,
        max_nodes=5000,
    )

    assert proof is not None
    code = render_true_certificate(proof.source, proof.target, proof)

    assert "fun t => ((x ◇ x) ◇ t)" in code
    assert "fun t => (x ◇ x ◇ t)" not in code
