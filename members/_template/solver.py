"""__MEMBER__'s solver entry point.

Contract (草案，等 solvers eval harness 落地后再定稿):
    def solve(eq1_id: int, eq2_id: int, eq1_text: str, eq2_text: str,
              budget_s: float) -> dict
        return {"verdict": "true"|"false"|"unknown",
                "proof_lean": "...", "cex": {...}, "stage": "..."}

The eval harness will import this module and call `solve` on each problem.
Return either a Lean proof term (for TRUE verdict) or a finite counterexample
table (for FALSE verdict).

Size limit: this file must stay ≤ 500KB (contest rule).
Helper modules can live alongside it; only solver.py itself is size-checked.

参考 baseline: solvers/baseline_solver_v3e.py (484KB, ~92% on sample_200).
不要直接修改 baseline; 它是团队 reference. 这里写你自己的, 可以挑选 import.
"""
from __future__ import annotations

# Example: pull whichever engines you need from solvers.engines
# (engines.py 单文件, 47KB, 自己看 API)
# from solvers.engines import (
#     try_linear_sec, try_cyclic_sec, try_finite_sec,
#     tactic_sweep,
#     try_invertibility,
# )


def solve(
    eq1_id: int,
    eq2_id: int,
    eq1_text: str,
    eq2_text: str,
    budget_s: float = 30.0,
) -> dict:
    """Stub. Replace with your pipeline.

    建议起步顺序:
      1) closure BFS (TRUE 用)        → 见 solvers.baseline_solver_v3e 的 Stage 1
      2) brute Fin 2..3 (FALSE 用)    → solvers.engines.try_finite_sec
      3) cex families (FALSE 用)      → solvers.engines.try_linear_sec / cyclic_sec / ...
      4) tactic_sweep (TRUE 用)        → solvers.engines.tactic_sweep
      5) 你自己的新 engine             → 见 BLUEPRINT.md 选定的攻坚方向
    """
    return {"verdict": "unknown", "stage": "stub"}
