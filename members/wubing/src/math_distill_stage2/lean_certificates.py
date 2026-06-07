from __future__ import annotations

from math_distill_stage2.equations import Equation, Expr, parse_equation


def validate_finite_magma_table(table: list[list[int]]) -> int:
    order = len(table)
    if order == 0:
        raise ValueError("finite magma table must be non-empty")
    if any(len(row) != order for row in table):
        raise ValueError("finite magma table must be square")
    for row in table:
        for value in row:
            if not isinstance(value, int) or value < 0 or value >= order:
                raise ValueError(f"finite magma table entry {value!r} is outside Fin {order}")
    return order


def module_name_from_lean_filename(filename: str) -> str:
    normalized = filename.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    if normalized.endswith(".lean"):
        normalized = normalized[:-5]
    return normalized.replace("/", ".")


def positive_implication_certificate(theorem_name: str, lhs_id: int, rhs_id: int) -> str:
    return f"""import equational_theories.Subgraph

theorem stage2_positive_cert (G : Type*) [Magma G] (h : Equation{lhs_id} G) : Equation{rhs_id} G :=
  {theorem_name} G h
"""


def positive_path_certificate(edges: list[dict]) -> str:
    if not edges:
        raise ValueError("positive path certificate requires at least one edge")
    imports = sorted({module_name_from_lean_filename(edge["filename"]) for edge in edges})
    lhs_id = int(edges[0]["lhs_id"])
    rhs_id = int(edges[-1]["rhs_id"])
    proof = "h"
    for edge in edges:
        proof = f"({edge['name']} G {proof})"
    return "\n".join([*(f"import {module}" for module in imports), ""]) + f"""
theorem stage2_positive_cert (G : Type*) [Magma G] (h : Equation{lhs_id} G) : Equation{rhs_id} G :=
  {proof}
"""


def negative_finite_counterexample_certificate(lhs_id: int, rhs_id: int) -> str:
    return f"""import Mathlib.Tactic
import equational_theories.Equations.Basic

theorem stage2_negative_cert :
    ∃ (G : Type) (_ : Magma G), Equation{lhs_id} G ∧ ¬ Equation{rhs_id} G :=
  ⟨Fin 2, ⟨fun x _ => x⟩, by decide⟩
"""


def finite_magma_counterexample_certificate(
    lhs_id: int,
    rhs_id: int,
    table: list[list[int]],
    theorem_name: str = "stage2_negative_cert",
) -> str:
    order = validate_finite_magma_table(table)
    op_body = finite_magma_operation_body(table, indent="    ")
    return f"""import Mathlib.Tactic
import equational_theories.Equations.All

theorem {theorem_name} :
    ∃ (G : Type) (_ : Magma G), Equation{lhs_id} G ∧ ¬ Equation{rhs_id} G :=
  let op : Fin {order} → Fin {order} → Fin {order} := fun x y =>
{op_body}
  ⟨Fin {order}, ⟨op⟩, by decide⟩
"""


def finite_magma_operation_body(table: list[list[int]], indent: str) -> str:
    validate_finite_magma_table(table)
    lines = table_if_lines("x", [table_row_expr(row) for row in table], indent)
    return "\n".join(lines)


def table_row_expr(row: list[int]) -> str:
    return inline_if_chain("y", [str(value) for value in row])


def inline_if_chain(variable: str, values: list[str]) -> str:
    if len(values) == 1:
        return values[0]
    expression = values[-1]
    for index, value in reversed(list(enumerate(values[:-1]))):
        expression = f"if {variable} = {index} then {value} else {expression}"
    return expression


def table_if_lines(variable: str, values: list[str], indent: str) -> list[str]:
    if len(values) == 1:
        return [f"{indent}{values[0]}"]
    lines: list[str] = []
    for index, value in enumerate(values):
        if index == 0:
            lines.append(f"{indent}if {variable} = {index} then")
        elif index < len(values) - 1:
            lines.append(f"{indent}else if {variable} = {index} then")
        else:
            lines.append(f"{indent}else")
        lines.append(f"{indent}  {value}")
    return lines


def pure_finite_magma_counterexample_certificate(
    lhs_id: int,
    lhs_equation: str,
    rhs_id: int,
    rhs_equation: str,
    table: list[list[int]],
    theorem_name: str = "stage2_negative_cert",
) -> str:
    order = validate_finite_magma_table(table)
    op_body = finite_magma_operation_body(table, indent="    ")
    lhs_definition = pure_equation_definition(lhs_id, lhs_equation)
    rhs_definition = pure_equation_definition(rhs_id, rhs_equation)
    return f"""class Magma (G : Type) where
  op : G -> G -> G

infixl:70 " ◇ " => Magma.op

{lhs_definition}

{rhs_definition}

theorem {theorem_name} :
    ∃ (G : Type) (_ : Magma G), Equation{lhs_id} G ∧ ¬ Equation{rhs_id} G :=
  let op : Fin {order} -> Fin {order} -> Fin {order} := fun x y =>
{op_body}
  ⟨Fin {order}, ⟨op⟩, by decide⟩
"""


def pure_equation_definition(equation_id: int, source: str) -> str:
    equation = parse_equation(source)
    variables = " ".join(equation.variables())
    return (
        f"abbrev Equation{equation_id} (G : Type) [Magma G] :=\n"
        f"  ∀ {variables} : G, {lean_expr(equation.left, top=True)} = {lean_expr(equation.right, top=True)}"
    )


def lean_expr(expr: Expr, top: bool = False) -> str:
    if expr.kind == "var":
        assert expr.value is not None
        return expr.value
    assert expr.left is not None
    assert expr.right is not None
    left = lean_expr(expr.left)
    right = lean_expr(expr.right)
    expression = f"{left} ◇ {right}"
    return expression if top else f"({expression})"
