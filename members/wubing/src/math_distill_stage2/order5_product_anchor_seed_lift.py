from __future__ import annotations

from math_distill_stage2.lean_certificates import lean_expr
from math_distill_stage2.order5_strategy_registry import (
    _is_product_root_target,
    _parse_stage2_equation,
    _product_anchor_h_args,
    _product_anchor_shape,
)


FORBIDDEN_LEAN_TOKENS = ("sorry", "admit", "axiom", "unsafe", "by_contra!")


def render_product_anchor_seed_lift_certificate(
    *,
    seed_equation: str,
    target_equation: str,
    source_to_seed_proof_body: str,
) -> str:
    """Compose a source->seed proof body with the product-anchor template."""

    seed = _parse_stage2_equation(seed_equation)
    target = _parse_stage2_equation(target_equation)
    shape = _product_anchor_shape(seed)
    if shape is None:
        raise ValueError("seed equation is not a product-anchor template")
    if not _is_product_root_target(target):
        raise ValueError("target equation is not a product-root equation")

    proof_body = _normalized_proof_body(source_to_seed_proof_body)
    side, first_variable, second_variable = shape
    seed_variables = seed.variables()
    h_seed_type = (
        f"∀ ({' '.join(seed_variables)} : G), "
        f"{lean_expr(seed.left, top=True)} = {lean_expr(seed.right, top=True)}"
    )
    h_pq = (
        "h_seed "
        + _product_anchor_h_args(seed, first_variable, second_variable, "p", "q")
    )
    h_rs = (
        "h_seed "
        + _product_anchor_h_args(seed, first_variable, second_variable, "r", "s")
    )
    if side == "left":
        allprod_proof = f"({h_pq}).trans ({h_rs}).symm"
    elif side == "right":
        allprod_proof = f"({h_pq}).symm.trans ({h_rs})"
    else:
        raise ValueError(f"unknown product-anchor side: {side}")

    target_variables = target.variables()
    target_intro = f"  intro {' '.join(target_variables)}\n" if target_variables else ""
    assert target.left.left is not None
    assert target.left.right is not None
    assert target.right.left is not None
    assert target.right.right is not None
    code = (
        "import JudgeProblem\n"
        "set_option linter.unusedVariables false\n\n"
        "def submission : Goal := by\n"
        "  intro G _ h\n"
        f"  have h_seed : {h_seed_type} := by\n"
        f"{_indent_nonblank(proof_body, '    ')}"
        "  have allprod : ∀ (p q r s : G), p ◇ q = r ◇ s := by\n"
        "    intro p q r s\n"
        f"    exact {allprod_proof}\n"
        f"{target_intro}"
        f"  exact allprod ({lean_expr(target.left.left, top=True)}) "
        f"({lean_expr(target.left.right, top=True)}) "
        f"({lean_expr(target.right.left, top=True)}) "
        f"({lean_expr(target.right.right, top=True)})\n"
    )
    forbidden = forbidden_lean_token(code)
    if forbidden is not None:
        raise ValueError(f"generated certificate contains forbidden token: {forbidden}")
    return code


def forbidden_lean_token(code: str) -> str | None:
    lowered = code.lower()
    for token in FORBIDDEN_LEAN_TOKENS:
        if token in lowered:
            return token
    return None


def _normalized_proof_body(proof_body: str) -> str:
    stripped = proof_body.strip()
    if not stripped:
        raise ValueError("source-to-seed proof body is empty")
    forbidden = forbidden_lean_token(stripped)
    if forbidden is not None:
        raise ValueError(f"source-to-seed proof body contains forbidden token: {forbidden}")
    return stripped + "\n"


def _indent_nonblank(text: str, prefix: str) -> str:
    return "".join((prefix + line) if line.strip() else line for line in text.splitlines(True))
