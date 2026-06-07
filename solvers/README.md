# solvers/ — Shared Library + Baseline

> 公共代码。改这里需 PR + ≥ 1 人 review。

## 设计原则

1. **通用引擎，不写题面针对性 hardcoded**（见根 [CLAUDE.md](../CLAUDE.md)）
2. **API 稳定优先**：成员的 solver 可能 import `solvers.engines`，破坏性改动要发 ADR
3. **薄而精**：solvers/ 只放跨成员复用的能力；成员私有工具放 `members/<you>/`

## 文件清单

| 文件 | 用途 | 状态 |
|---|---|---|
| `engines.py` | Layer 3/3.5/4 通用引擎：counterexample families (linear-sec, cyclic-sec, finite-sec, bilinear, near-miss, backtrack, random_fin), tactic_sweep, invertibility 6 patterns | 47KB，已验证 |
| `baseline_solver_v3e.py` | 团队当前 baseline solver：stellar_v3-e 全管道 (Stage 0.5 lawbook → 1 closure BFS → 2 brute Fin → 3 cex → 4 tactic_sweep → 4.5 superposition → 4.6 paramod → 4.6.6 bidir → 4.6.7 BFS w/CONST/LCONST → 4.6.5 KB-saturation → 4.6.8 const_sq + LLM σ → 5 invertibility → 4.9 LLM free-emit) | 484KB，已验证 sample_200 ≈ 92.0% |

## 用法

```python
# 引擎模块直接 import
from solvers.engines import (
    try_linear_sec,        # §3.2 linear-sec
    try_cyclic_sec,        # §3.3 cyclic-sec
    try_finite_sec,        # §3.1 brute Fin
    tactic_sweep,          # Layer 4 tactic 扫描
    # ... etc
)

# baseline solver 作为参考 / fork 起点
# (不要直接当 entry point 用; 写你自己的 solver, 选择性 import 它的子函数)
```

## baseline_solver_v3e.py 是什么

- 团队**当前最佳**的 solver 实现，sample_200 ≈ 92.0%, hard1 ≈ 55.1%
- 自包含单文件，只依赖 stdlib + 比赛 judge runtime
- **不要直接修改它当作你的 solver**；它是 baseline reference
- 自己的 solver 写在 `members/<你>/solver.py`，可以 fork / 抄它的 stage 函数 / import 其中的工具

## 改动政策

- 改 `engines.py` API → 需要给 baseline + 所有成员 solver 跑一遍跑分对照
- 改 `baseline_solver_v3e.py` → 应该谨慎，建议先在自己的 `member/<你>` 分支 fork 实验，确认无 regression 再 PR 进 solvers/
- 新增 engine → 先在 `members/<你>/experiments/` 写出来，pattern 成熟后再蓝图 ADR + PR 进 `solvers/engines.py`

## 不在 solvers 的东西

| 不在 solvers/ | 原因 | 在哪 |
|---|---|---|
| judge | 比赛官方提供 | `third_party/equational-theories-lean-stage2/judge/verify.py` |
| 全图 22M 蕴含数据 | 比赛官方提供 | `third_party/equational_theories/data/` |
| 论文反例族原始 Lean 实现 | 比赛官方提供 | `third_party/equational_theories/EquationalTheories/Counterexamples/` |
| lawbook | zhangkang 维护的本地知识库 | `datasets/lawbook/` (gitignored); 见 [docs/playbook/lawbook.md](../docs/playbook/lawbook.md) |
