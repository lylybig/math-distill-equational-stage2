# 2026-05-08/v5 Vampire/superpose compilers sample200 185

这是从 `2026-05-08/d7` promote 的当前最佳版本。

- sample200：`185/200`
- accepted rate：`92.50%`
- accepted true / false：`85 / 100`
- LLM calls：`15`
- judge calls：`402`
- aggregate problem elapsed：`3354.77s`（parallel run 中不是 wall time）
- wall time：约 `514.78s`（`8m34.8s`，按 `createdAt` 到 `summary.json` mtime 估算）
- solver hash：`bc3d31a3596243a9915b1bbfefe8955f60e92947d92fd6c561776f39538326ee`
- solver bytes：`201155`
- sample200 run：`artifacts/runs/2026-05-08/official-draft-d7-sample200-parallel-w8/`
- failed-subset run：`artifacts/runs/2026-05-08/official-draft-d7-truefailed17-parallel-w8/`

相对 `2026-05-08/v4`，新增解决 2 个 true 样本：

- `true_3108_4642`
- `true_674_668`

核心改动：

- 新增 `try_vampire_superpose_projection_compiler`：
  - 识别 `x = (((y ◇ x) ◇ x) ◇ z) ◇ x`。
  - 编译外部 superpose proof 中的 `e12/e24` projection lemmas。
  - 生成 `have`、`calc`、`congrArg` 证书。
- 新增 `try_vampire_superpose_left_absorption_compiler`：
  - 识别 `x = y ◇ (x ◇ ((x ◇ z) ◇ z))`。
  - 编译出 `c ◇ (a ◇ b) = a` left absorption lemma。
  - 不依赖 `simp`、`rw`、外部 theorem import 或 known-proof 表。

当前 sample200 中 false 已全部解决：

- false：`100/100`
- true：`85/100`

仍失败的 true 样本：

- `true_1167_2000`, `true_1698_555`, `true_1604_1822`,
  `true_2860_3458`, `true_1738_1258`, `true_2654_2864`,
  `true_2789_898`, `true_2935_3138`, `true_428_3725`,
  `true_1500_498`, `true_691_1976`, `true_2771_2775`,
  `true_2055_2656`, `true_689_1350`, `true_1636_1839`

`submissions/solo_official/solver.py` 仍未自动同步；最终官方导出单独处理。
