# 2026-05-08 v8 后续 proof-seed 扫描

基线：`solvers/solo_official/versions/2026-05-08/v8/`

- sample200：`187A / 13R / 0E`
- true / false accepted：`87 / 100`
- LLM calls：`0`
- sample200 run：`artifacts/runs/2026-05-08/official-draft-d10-repair-sample200-parallel-w8/`

## 剩余 true failures

- `true_1167_2000`
- `true_1698_555`
- `true_1604_1822`
- `true_2860_3458`
- `true_1738_1258`
- `true_2654_2864`
- `true_2789_898`
- `true_2935_3138`
- `true_1500_498`
- `true_691_1976`
- `true_2771_2775`
- `true_2055_2656`
- `true_1636_1839`

## 外部 proof source 覆盖

这些剩余失败都能在外部 `Generated/` 目录找到 proof source，但不能直接 import 到官方 judge：

- `Equation2935_implies_Equation3138`：`Generated/EquationSearch/theorems/Combined.lean`
- `Equation1604_implies_Equation1822`：`Generated/EquationSearch/theorems/Combined.lean`
- 其余样本：`Generated/VampireProven/Proofs*.lean`

## 初步候选

优先看短 trace、可抽成通用 deterministic template 的目标：

1. `true_1738_1258`
   - 方程：`x = (y ◇ y) ◇ ((z ◇ x) ◇ x)` -> `x = x ◇ (((y ◇ z) ◇ x) ◇ x)`
   - Vampire trace 中关键结论较短：
     - `((a ◇ b) ◇ b) = ((c ◇ c) ◇ b)`
     - `b ◇ ((a ◇ b) ◇ b) = b`
   - 候选 template：从 `h` 派生右吸收形态，再用 `.symm` 关闭目标。
   - 风险：需要把 `superpose` step 手工展开为 `have/calc/congrArg`；尚未有官方 judge accepted seed。

2. `true_2654_2864`
   - 方程：`x = ((x ◇ x) ◇ (y ◇ y)) ◇ z` -> `x = ((x ◇ (y ◇ x)) ◇ x) ◇ z`
   - Vampire trace 较短，关键结论包括：
     - `(((a ◇ a) ◇ b) ◇ c) = a`
     - `(a ◇ a) = (a ◇ b)`
   - 候选 template：先把目标 RHS 内层规约到 `((x ◇ x) ◇ x) ◇ z`，再用派生投影闭合。
   - 风险：同样需要手工展开 superpose；直接从 trace 到 Lean certificate 还未验证。

3. `true_2771_2775`
   - Vampire trace 很短且导出 `a = b` 形态。
   - 候选 template 可能 blast radius 较大，因为一旦能证明全等式会解决更多类似 collapse 目标。
   - 风险：过强结论需要特别谨慎，避免误匹配到不满足 trace 前提的等式形态。

## 下一步

先对 `true_1738_1258` 做单题 Lean proof-seed 探索。只有在得到 judge accepted 的手写 seed 后，再开 d11 focused test 和 draft solver template。

## Probe 记录

### `true_1738_1258`

- 目录：`artifacts/probes/2026-05-08/v8-proof-seed-1738/`
- 尝试：把 Vampire 的两个关键中间结论写成 `have ... := by grind`
  - `((a ◇ b) ◇ b) = ((c ◇ c) ◇ b)`
  - `b ◇ ((a ◇ b) ◇ b) = b`
- 结果：official judge rejected。
- 主要错误：`grind` 无法证明第一个中间 lemma；在给定第一个 lemma 后，也无法证明第二个 lemma。
- 结论：`true_1738_1258` 仍可能是 d11 候选，但需要手工展开 `superpose` 为 `calc/congrArg/trans`，不能直接依赖 tactic lemma。
