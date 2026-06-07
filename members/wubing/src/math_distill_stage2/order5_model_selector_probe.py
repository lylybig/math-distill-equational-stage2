from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import product
from typing import Sequence

from math_distill_stage2.equations import Equation, Expr
from math_distill_stage2.order5_paircheck_bank import PaircheckModel


CompiledExpr = int | tuple["CompiledExpr", "CompiledExpr"]


@dataclass(frozen=True)
class _CompiledEquation:
    variables: tuple[str, ...]
    left: CompiledExpr
    right: CompiledExpr


def fast_satisfies(table: tuple[tuple[int, ...], ...], equation: Equation) -> bool:
    compiled = _compile_equation(equation)
    return _compiled_satisfies(table, compiled)


def find_model_selector_hits(
    *,
    candidate_pairs: Sequence[dict],
    equations: dict[int, Equation],
    models: Sequence[PaircheckModel],
) -> tuple[list[dict], dict]:
    source_equation_ids = sorted({int(pair["eq1_id"]) for pair in candidate_pairs})
    target_equation_ids = sorted({int(pair["eq2_id"]) for pair in candidate_pairs})
    equation_ids = sorted(set(source_equation_ids) | set(target_equation_ids))
    compiled_equations = {
        equation_id: _compile_equation(equations[equation_id])
        for equation_id in equation_ids
    }

    hit_pair_indexes: set[int] = set()
    rows: list[dict] = []
    model_hit_counts: Counter[str] = Counter()
    for model in models:
        satisfied_sources = {
            equation_id
            for equation_id in source_equation_ids
            if _compiled_satisfies(model.table, compiled_equations[equation_id])
        }
        if not satisfied_sources:
            continue
        needed_target_ids = {
            int(pair["eq2_id"])
            for pair in candidate_pairs
            if int(pair["pair_index"]) not in hit_pair_indexes
            and int(pair["eq1_id"]) in satisfied_sources
        }
        satisfied_targets = {
            equation_id
            for equation_id in needed_target_ids
            for compiled in [compiled_equations[equation_id]]
            if _compiled_satisfies(model.table, compiled)
        }
        for pair in candidate_pairs:
            pair_index = int(pair["pair_index"])
            if pair_index in hit_pair_indexes:
                continue
            eq1_id = int(pair["eq1_id"])
            eq2_id = int(pair["eq2_id"])
            if eq1_id in satisfied_sources and eq2_id not in satisfied_targets:
                hit_pair_indexes.add(pair_index)
                model_hit_counts[model.label] += 1
                rows.append(
                    {
                        "pair_index": pair_index,
                        "eq1_id": eq1_id,
                        "eq2_id": eq2_id,
                        "stratum": str(pair["stratum"]),
                        "model_label": model.label,
                        "model_source": model.source,
                        "order": model.order,
                        "table": model.to_json_table(),
                        "python_verified": True,
                    }
                )
        if len(hit_pair_indexes) == len(candidate_pairs):
            break

    summary = {
        "schema_version": 1,
        "candidate_count": len(candidate_pairs),
        "model_count": len(models),
        "hit_count": len(rows),
        "hit_rate": len(rows) / len(candidate_pairs) if candidate_pairs else 0.0,
        "model_hit_counts": dict(model_hit_counts),
        "stratum_counts": dict(Counter(str(pair["stratum"]) for pair in candidate_pairs)),
        "hit_stratum_counts": dict(Counter(row["stratum"] for row in rows)),
    }
    return rows, summary


def _compile_equation(equation: Equation) -> _CompiledEquation:
    variables = tuple(equation.variables())
    variable_indexes = {name: index for index, name in enumerate(variables)}
    return _CompiledEquation(
        variables=variables,
        left=_compile_expr(equation.left, variable_indexes),
        right=_compile_expr(equation.right, variable_indexes),
    )


def _compile_expr(expr: Expr, variable_indexes: dict[str, int]) -> CompiledExpr:
    if expr.kind == "var":
        assert expr.value is not None
        return variable_indexes[expr.value]
    assert expr.left is not None
    assert expr.right is not None
    return (
        _compile_expr(expr.left, variable_indexes),
        _compile_expr(expr.right, variable_indexes),
    )


def _compiled_satisfies(
    table: tuple[tuple[int, ...], ...],
    equation: _CompiledEquation,
) -> bool:
    order = len(table)
    for assignment in product(range(order), repeat=len(equation.variables)):
        if _evaluate_compiled(equation.left, assignment, table) != _evaluate_compiled(
            equation.right,
            assignment,
            table,
        ):
            return False
    return True


def _evaluate_compiled(
    expr: CompiledExpr,
    assignment: tuple[int, ...],
    table: tuple[tuple[int, ...], ...],
) -> int:
    if isinstance(expr, int):
        return assignment[expr]
    left, right = expr
    return table[_evaluate_compiled(left, assignment, table)][
        _evaluate_compiled(right, assignment, table)
    ]
