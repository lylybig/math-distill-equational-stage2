# Playbook — 如何使用 solvers/ 库

> 给写 solver.py 的人看的 how-to。

## 章节

- [judge.md](judge.md) — 起 judge service + 怎么用 / 调试
- [llm.md](llm.md) — LLM 配置、模型选择、协议
- [lawbook.md](lawbook.md) — lawbook 本地生成与使用（typeA/B/C JSON）
- (待补) `engines.md` — `solvers.engines` 各引擎的 API 速查
- (待补) `baseline.md` — `solvers.baseline_solver_v3e` 的 Stage 流程与可 fork 点
- (待补) `datasets.md` — 采样 sample_200 / hard1-3 的方法
- (待补) `eval.md` — 人工跑分流程 + SCOREBOARD 更新约定

## 写 solver 的标准骨架（参考 baseline）

```python
# members/<you>/solver.py
from solvers.engines import (
    try_linear_sec, try_cyclic_sec, try_finite_sec,
    tactic_sweep, try_invertibility,
)


def solve(eq1_id, eq2_id, eq1_text, eq2_text, budget_s=30.0):
    # TIER 1: closure BFS for TRUE  (照搬 baseline 的 Stage 1 即可)
    # ...

    # TIER 1: cex for FALSE
    cex = try_finite_sec(eq2_text, budget_s=budget_s * 0.1)
    if cex: return {"verdict": "false", "cex": cex, "stage": "finite-sec"}
    cex = try_linear_sec(eq2_text, budget_s=budget_s * 0.1)
    if cex: return {"verdict": "false", "cex": cex, "stage": "linear-sec"}
    # ...

    # TIER 2+: your own engine
    ...
    return {"verdict": "unknown", "stage": "fallthrough"}
```

完整参考实现见 [solvers/baseline_solver_v3e.py](../../solvers/baseline_solver_v3e.py)。
