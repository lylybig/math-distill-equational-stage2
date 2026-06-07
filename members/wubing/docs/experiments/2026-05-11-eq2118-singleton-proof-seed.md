# Equation2118 singleton proof seed

## 目标

本记录是一个 bounded proof seed（有界证明种子），用于下一轮 true proof template（真命题证明模板）候选选择；本次不修改 `solver.py`。

## 选择原因

- 来源 run：`artifacts/runs/2026-05-09/order4-d11-magmaegg-singleton-dev-fast-w8/`
- `dev_fast` true failed 中，`Equation2118` 是重复失败且总耗时最高的 `eq1` 族之一：
  - `4` 个 failed true rows
  - aggregate elapsed：`213.35s`
  - judge calls：`35`
- 代表样例：
  - `true_2118_13`
  - `true_2118_448`
  - `true_2118_532`
  - `true_2118_3570`

## 方程形状

`Equation2118`：

```text
x = ((y ◇ x) ◇ z) ◇ (z ◇ w)
```

这个形状距离 `Equation2117` 只有一个 simple rewrite（简单重写）：

```text
Equation2118 -> Equation2117
```

ETP 外部 trace 显示：

```text
Equation2118 -> Equation2117
Equation2117 -> Equation2
```

其中 `Equation2` 是 singleton/collapse（单点坍缩）目标：`x = y`。一旦在 Stage 2 certificate 内构造出 `∀ x y, x = y`，任意 `EquationRHS` 都可关闭。

## 外部来源

- `external/equational_theories/equational_theories/Generated/SimpleRewrites/theorems/Rewrite_wz.lean`
  - `Equation2118_implies_Equation2117`
  - line `488`
  - 证明形状：`λ x y z => h x y z z`
- `external/equational_theories/equational_theories/Generated/MagmaEgg/small/_002.lean`
  - `Equation2117_implies_Equation2`
  - line `773`
  - 证明形状：MagmaEgg proof term（自动证明项）

## 当前失败形态

`true_2118_13` 在当前 solver 中失败：

- elapsed：`47.29s`
- judge calls：`8`
- 失败主要集中在：
  - `grind` 失败
  - `simp made no progress`
  - 当前 constancy helper 留下 unsolved goals（未解决目标）

这说明现有通用 true fallback 没有识别到 `Equation2118 -> Equation2117 -> Equation2` 这条短链。

## 可复用候选模板

候选方向：新增一个 eq1-level singleton compiler（按 `eq1` 级别生成 singleton 证明，不是 pair-level known proof 表）。

实现思路：

1. 先用 `h x y z z` 把 `Equation2118` 降成 `Equation2117`。
2. 把 `Equation2117_implies_Equation2` 的 MagmaEgg proof term 翻译为当前 solver 的 proof body。
3. 在 `try_magmaegg_singleton_compiler` 中让 `eq1_id=2118` 先构造 `Equation2`，再用现有 singleton closure 关闭任意 true target。

## 下一步 focused test

建议下一个 solver draft 先加 focused test：

```text
tests/official/test_official_solo_submission.py::test_solver_emits_eq2118_singleton_compiler_for_dev_fast_family
```

测试样例优先用 `true_2118_13`，再用 `true_2118_3570` 做 targeted official check。若 targeted check 通过，再跑 `dev_fast` 观察是否修复这 4 个 failed true rows，且 judge calls 是否下降。

## 边界

- 本 proof seed 已进入 `solvers/solo_official/drafts/2026-05-11/d1/solver.py`，
  并在 targeted official runner 中通过 `true_2118_*` dev_fast 四题验证：
  `4A / 0R / 0E`，`judge_calls=4`，`llm_calls=0`。
- 远端 `dev_fast` 标准回归 `remote-d1-eq2118-dev-fast-w24-c50-20260511-115647`
  结果为 `1652A / 348R / 0E`，相对 current v10 的 `1648A / 352R / 0E`
  提升 `+4A`，符合本 seed 预期。
- 不建议把 `true_2118_*` 直接加入 known-proof table。
- 这是可泛化的 eq1-level singleton strategy（单点坍缩策略）候选，适合进入 `stage2-train-improve-solver`。
