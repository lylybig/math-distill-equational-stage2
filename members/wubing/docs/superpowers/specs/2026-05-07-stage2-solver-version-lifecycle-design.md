# Stage 2 Solver 版本生命周期设计

## 背景

当前项目主线是构建官方 Solo `solver.py`。官方 runner 要求被评估的 submission 目录只能包含一个普通文件 `solver.py`。直接在最终导出目录 `submissions/solo_official/` 上持续试错会让“当前可提交版本”“实验候选”和“已验证 baseline”混在一起，难以回退和复现。

项目早期 cheatsheet 流程已经使用过 `current / drafts / versions` 三层生命周期。该模式适合迁移到 solver，但必须放在官方提交目录之外。

## 设计

新增 solver 版本工作台：

```text
solvers/solo_official/
  current/
  drafts/
  versions/
```

官方提交导出目录保持不变：

```text
submissions/solo_official/
  solver.py
```

日常评估从 `current`、`drafts/YYYY-MM-DD/dN` 或 `versions/YYYY-MM-DD/vN` 生成 run-local submission：`artifacts/runs/YYYY-MM-DD/<run-id>/submission/solver.py`。`submissions/solo_official/solver.py` 只作为最终官方提交导出路径。

`drafts/YYYY-MM-DD/dN/` 保存实验候选和 targeted validation 记录。`versions/YYYY-MM-DD/vN/` 保存完成标准评估、可长期比较或回退的冻结版本。

## 当前落地选择

- 将 `175/200` sample200 baseline 冻结到 `versions/2026-05-07/v1/`，label 为 `opnorm-sample200-baseline-175`。
- 将 baseline 同步为 `current/`。
- 将 `Fin 7 + maxRecDepth` 候选保存为 `drafts/2026-05-07/d1/`，label 为 `fin7-false907`，因为它只做了 targeted validation，尚未完整确认 sample200 无回归。

## 验证

新增/更新 official solver 测试，确保：

- `submissions/solo_official/` 仍只有 `solver.py`。
- baseline version 与 current 哈希一致。
- Fin 7 候选保存在 draft 中，而不是混入当前官方入口。

## 后续

下一步应先跑 baseline 失败 25 题子集验证 `drafts/2026-05-07/d1` 是否无回归。若通过，再考虑完整 sample200，并根据结果决定是否 promote 到 `versions/2026-05-07/vN`。
