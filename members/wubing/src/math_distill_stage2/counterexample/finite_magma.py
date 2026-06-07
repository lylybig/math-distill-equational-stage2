from __future__ import annotations

from dataclasses import dataclass
from itertools import product

from math_distill_stage2.equations import Equation, Expr


@dataclass(frozen=True)
class FiniteMagma:
    order: int
    table: tuple[tuple[int, ...], ...]

    def satisfies(self, equation: Equation) -> bool:
        variables = equation.variables()
        for values in product(range(self.order), repeat=len(variables)):
            assignment = dict(zip(variables, values))
            if self.evaluate(equation.left, assignment) != self.evaluate(equation.right, assignment):
                return False
        return True

    def evaluate(self, expr: Expr, assignment: dict[str, int]) -> int:
        if expr.kind == "var":
            assert expr.value is not None
            return assignment[expr.value]
        assert expr.left is not None
        assert expr.right is not None
        left = self.evaluate(expr.left, assignment)
        right = self.evaluate(expr.right, assignment)
        return self.table[left][right]

    def to_json_table(self) -> list[list[int]]:
        return [list(row) for row in self.table]


def enumerate_magmas(order: int):
    for values in product(range(order), repeat=order * order):
        table = tuple(
            tuple(values[row * order + column] for column in range(order))
            for row in range(order)
        )
        yield FiniteMagma(order=order, table=table)


def find_countermodel(
    lhs_equation: Equation,
    rhs_equation: Equation,
    max_order: int,
) -> FiniteMagma | None:
    for order in range(1, max_order + 1):
        for magma in enumerate_magmas(order):
            if magma.satisfies(lhs_equation) and not magma.satisfies(rhs_equation):
                return magma
    return None
