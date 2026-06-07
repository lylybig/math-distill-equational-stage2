"""wubing's solver entry point.

Contract:
    def solve(problem: Problem, budget_s: float) -> Solution: ...

The eval harness will import this module and call `solve` on each problem with the
configured per-problem budget. Return a `Solution` with either a Lean proof term
(for TRUE verdict) or a finite counterexample table (for FALSE verdict).

Size limit: this file (the file in members/<you>/solver.py) must stay ≤ 500KB.
Helper modules can live alongside it; only solver.py itself is size-checked.

See core/ for shared utilities. Do not duplicate work that core already does.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from core.datasets_api import Problem


@dataclass
class Solution:
    verdict: Literal["true", "false", "unknown"]
    proof_lean: str = ""           # if verdict == "true"
    cex_family: str = ""           # if verdict == "false", e.g. "linear-sec"
    cex_table: list[list[int]] | None = None
    stage: str = ""                # which engine produced it, for analytics


def solve(problem: Problem, budget_s: float = 30.0) -> Solution:
    """Default stub — replace with your pipeline.

    See docs/playbook/ for examples of wiring core engines together.
    """
    return Solution(verdict="unknown", stage="stub")
