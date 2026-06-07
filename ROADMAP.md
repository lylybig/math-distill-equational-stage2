# Roadmap

## 比赛信息

- **赛事**: Equational Theories Project · Stage 2（蒸馏赛道）
- **截止**: 2026-08-31
- **约束**: solver.py ≤ 500KB，32B 级模型（非前沿），Lean 4 证明或有限反例

## 目标分层

| 阶段 | 全图覆盖率 | 允许未解 (/22M) | 状态 |
|---|---|---|---|
| 起点 | ~53.6% (1669 题 TIER 1 估计) | — | 当前 |
| 中期 | ≥ 90% | ≤ 2.2M | 攻关中 |
| 长期 | ≥ 98% | ≤ 440K | 最终目标 |

> **注**：1669 contest benchmark 是从 22M 全图采样的训练集，不是真正目标。任何针对 1669 中具体题的 hardcoded 在全图上贡献为零，**禁止 over-fit**。

## 引擎全景（按 ROI 排序）

```
✅ Stage 1   closure BFS (TRUE)              v3 graph 8884 边
✅ Stage 2   brute Fin 2-3 (FALSE)
✅ Stage 3   cex 6+ cheap families
✅ Stage 4   tactic_sweep ~22 candidates
✅ Stage 4.5 superposition simulator (浅)
✅ Stage 5   invertibility_sweep 6 patterns
✅ Stage 6   LLM (V4-Flash, 弱)
✅ Layer 3.6 meta-closure (lambda-only)

🚧 Layer 4.6 Vampire trace decoder           (Class A, ~9 题, 500+ LOC)
🚧 Layer 3.x twisting + cohomology           (Class C, 3 题 + hard 集)
🚧 Layer 3.6 meta-closure tactic-aware       (Class B, 重做)
🚧 强化 LLM  Qwen3-Max / V3.1 切换
```

## 三个月节奏（M = month）

| 月份 | 主线 | 负责人 | 验收 |
|---|---|---|---|
| M1 (6 月) | solvers/ 库稳定 + 周报机制跑通 + 每个 `member/<name>` 分支有 baseline solver | 全员 | SCOREBOARD 有 3 行手工填写数据 |
| M2 (7 月) | 攻 Class A / B / C 中至少一类，全图采样估计提升 +10pp | 各成员认领 | 蓝图 PR + 实验卡片 |
| M3 (8 月) | 集成最优组合，跑全图采样估计；按约束打包提交 | 组长收尾 | 估计覆盖 ≥ 90% |

## 个人路线图

每位成员在自己的 `member/<you>` 分支上写 `members/<you>/BLUEPRINT.md`，并在周报中更新进度。
组长统一看周报对齐方向。

## 决策记录

重要技术选择写入 `docs/blueprints/`（ADR 风格），见 [0001-monorepo.md](docs/blueprints/0001-monorepo.md)。
