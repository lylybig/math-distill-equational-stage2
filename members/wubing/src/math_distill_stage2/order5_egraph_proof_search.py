from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable

from math_distill_stage2.equations import Equation, Expr
from math_distill_stage2.lean_certificates import lean_expr


FORBIDDEN_LEAN_TOKENS = ("sorry", "admit", "axiom", "unsafe", "by_contra!")


@dataclass(frozen=True)
class RewriteStep:
    path: tuple[str, ...]
    orientation: str
    substitution: dict[str, Expr]
    before: Expr
    after: Expr


@dataclass(frozen=True)
class RewriteProof:
    source: Equation
    target: Equation
    steps: tuple[RewriteStep, ...]


def match_pattern(pattern: Expr, expr: Expr) -> dict[str, Expr] | None:
    return _match_pattern(pattern, expr, {})


def find_rewrite_proof(
    source: Equation,
    target: Equation,
    *,
    max_steps: int,
    max_term_size: int,
    max_nodes: int,
) -> RewriteProof | None:
    if target.left == target.right:
        return RewriteProof(source=source, target=target, steps=())
    if max_steps <= 0 or max_nodes <= 0:
        return None

    queue = deque([(target.left, tuple[RewriteStep, ...]())])
    visited = {target.left.to_tuple()}
    nodes = 0
    while queue and nodes < max_nodes:
        expr, steps = queue.popleft()
        nodes += 1
        if len(steps) >= max_steps:
            continue
        for step, next_expr in _rewrite_successors(
            expr,
            source=source,
            desired=target.right,
            max_term_size=max_term_size,
        ):
            next_steps = (*steps, step)
            if next_expr == target.right:
                return RewriteProof(source=source, target=target, steps=next_steps)
            key = next_expr.to_tuple()
            if key in visited:
                continue
            visited.add(key)
            queue.append((next_expr, next_steps))
    return None


def proof_to_json(proof: RewriteProof) -> dict:
    return {
        "step_count": len(proof.steps),
        "steps": [
            {
                "path": list(step.path),
                "orientation": step.orientation,
                "substitution": {
                    name: _expr_to_string(expr)
                    for name, expr in sorted(step.substitution.items())
                },
                "before": _expr_to_string(step.before),
                "after": _expr_to_string(step.after),
            }
            for step in proof.steps
        ],
    }


def render_true_certificate(source: Equation, target: Equation, proof: RewriteProof) -> str:
    target_vars = target.variables()
    target_intro = f"  intro {' '.join(target_vars)}" if target_vars else None
    if not proof.steps:
        lines = [
            "import JudgeProblem",
            "set_option linter.unusedVariables false",
            "",
            "def submission : Goal := by",
            "  intro G _ h",
        ]
        if target_intro is not None:
            lines.append(target_intro)
        lines.extend(["  rfl", ""])
        return "\n".join(lines)

    exprs = [target.left]
    for step in proof.steps:
        exprs.append(step.after)

    lines = [
        "import JudgeProblem",
        "set_option linter.unusedVariables false",
        "",
        "def submission : Goal := by",
        "  intro G _ h",
    ]
    if target_intro is not None:
        lines.append(target_intro)
    lines.append("  calc")
    first = True
    for before, after, step in zip(exprs, exprs[1:], proof.steps):
        lhs = lean_expr(before, top=True) if first else "_"
        first = False
        lines.append(f"    {lhs} = {lean_expr(after, top=True)} := by")
        lines.append(f"      exact {_lean_step_proof(source, step)}")
    lines.append("")
    return "\n".join(lines)


def forbidden_lean_token(code: str) -> str | None:
    lowered = code.lower()
    for token in FORBIDDEN_LEAN_TOKENS:
        if token in lowered:
            return token
    return None


def _rewrite_successors(
    expr: Expr,
    *,
    source: Equation,
    desired: Expr,
    max_term_size: int,
) -> Iterable[tuple[RewriteStep, Expr]]:
    orientations = (
        ("forward", source.left, source.right),
        ("reverse", source.right, source.left),
    )
    for path, subexpr in _iter_subexprs(expr):
        desired_subexpr = _get_subexpr(desired, path)
        for orientation, pattern, replacement in orientations:
            substitution = _match_pattern(pattern, subexpr, {})
            if substitution is None:
                continue
            if not _replacement_variables(replacement) <= substitution.keys():
                if desired_subexpr is None:
                    continue
                substitution = _match_pattern(replacement, desired_subexpr, substitution)
                if substitution is None:
                    continue
            if not _replacement_variables(replacement) <= substitution.keys():
                continue
            rewritten_subexpr = _substitute(replacement, substitution)
            next_expr = _replace_subexpr(expr, path, rewritten_subexpr)
            if _term_size(next_expr) > max_term_size:
                continue
            yield (
                RewriteStep(
                    path=path,
                    orientation=orientation,
                    substitution=dict(sorted(substitution.items())),
                    before=expr,
                    after=next_expr,
                ),
                next_expr,
            )


def _match_pattern(
    pattern: Expr,
    expr: Expr,
    substitution: dict[str, Expr],
) -> dict[str, Expr] | None:
    if pattern.kind == "var":
        assert pattern.value is not None
        previous = substitution.get(pattern.value)
        if previous is None:
            return {**substitution, pattern.value: expr}
        return substitution if previous == expr else None
    if expr.kind != "mul":
        return None
    assert pattern.left is not None and pattern.right is not None
    assert expr.left is not None and expr.right is not None
    left_substitution = _match_pattern(pattern.left, expr.left, substitution)
    if left_substitution is None:
        return None
    return _match_pattern(pattern.right, expr.right, left_substitution)


def _substitute(expr: Expr, substitution: dict[str, Expr]) -> Expr:
    if expr.kind == "var":
        assert expr.value is not None
        return substitution[expr.value]
    assert expr.left is not None and expr.right is not None
    return Expr.mul(_substitute(expr.left, substitution), _substitute(expr.right, substitution))


def _replacement_variables(expr: Expr) -> set[str]:
    return set(expr.variable_names())


def _iter_subexprs(expr: Expr, path: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], Expr]]:
    yield path, expr
    if expr.kind == "mul":
        assert expr.left is not None and expr.right is not None
        yield from _iter_subexprs(expr.left, (*path, "left"))
        yield from _iter_subexprs(expr.right, (*path, "right"))


def _get_subexpr(expr: Expr, path: tuple[str, ...]) -> Expr | None:
    current = expr
    for item in path:
        if current.kind != "mul":
            return None
        assert current.left is not None and current.right is not None
        current = current.left if item == "left" else current.right
    return current


def _replace_subexpr(expr: Expr, path: tuple[str, ...], replacement: Expr) -> Expr:
    if not path:
        return replacement
    if expr.kind != "mul":
        raise ValueError("path does not exist in expression")
    assert expr.left is not None and expr.right is not None
    head, *tail = path
    if head == "left":
        return Expr.mul(_replace_subexpr(expr.left, tuple(tail), replacement), expr.right)
    if head == "right":
        return Expr.mul(expr.left, _replace_subexpr(expr.right, tuple(tail), replacement))
    raise ValueError(f"unknown path item: {head}")


def _term_size(expr: Expr) -> int:
    if expr.kind == "var":
        return 1
    assert expr.left is not None and expr.right is not None
    return 1 + _term_size(expr.left) + _term_size(expr.right)


def _lean_step_proof(source: Equation, step: RewriteStep) -> str:
    source_vars = source.variables()
    args = " ".join(lean_expr(step.substitution[name]) for name in source_vars)
    h_proof = f"h {args}".rstrip()
    if step.orientation == "reverse":
        h_proof = f"({h_proof}).symm"
    if not step.path:
        return h_proof
    return f"congrArg (fun t => {_lean_expr_with_hole(step.before, step.path)}) ({h_proof})"


def _lean_expr_with_hole(expr: Expr, path: tuple[str, ...]) -> str:
    if not path:
        return "t"
    if expr.kind != "mul":
        raise ValueError("path does not exist in expression")
    assert expr.left is not None and expr.right is not None
    head, *tail = path
    if head == "left":
        left = _lean_expr_with_hole(expr.left, tuple(tail))
        right = lean_expr(expr.right)
    elif head == "right":
        left = lean_expr(expr.left)
        right = _lean_expr_with_hole(expr.right, tuple(tail))
    else:
        raise ValueError(f"unknown path item: {head}")
    return f"({left} ◇ {right})"


def _expr_to_string(expr: Expr) -> str:
    if expr.kind == "var":
        assert expr.value is not None
        return expr.value
    assert expr.left is not None and expr.right is not None
    return f"({_expr_to_string(expr.left)} * {_expr_to_string(expr.right)})"
