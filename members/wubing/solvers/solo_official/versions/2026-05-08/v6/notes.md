# 2026-05-08/v6 Vampire/superpose collapse sample200 186

这是从 `2026-05-08/d8` promote 的当前最佳版本。

- sample200：`186/200`
- accepted rate：`93.00%`
- accepted true / false：`86 / 100`
- LLM calls：`14`
- judge calls：`393`
- aggregate problem elapsed：`3547.9s`（parallel run 中不是 wall time）
- wall time：约 `545.0s`（`9m05.0s`，按 `createdAt` 到 `summary.json` mtime 估算）
- solver hash：`4b60a63a858f38c7e5d4ca6ea2212c6d04bb09d93dcc614e5c3df82d365d285e`
- solver bytes：`204806`
- sample200 run：`artifacts/runs/2026-05-08/official-draft-d8-sample200-parallel-w8/`
- failed-subset run：`artifacts/runs/2026-05-08/official-draft-d8-truefailed17-parallel-w8/`

相对 `2026-05-08/v5`，新增解决 1 个 true 样本：

- `true_689_1350`

核心改动：

- 新增 `try_vampire_superpose_collapse_compiler`：
  - 识别 `x = y ◇ (x ◇ ((z ◇ x) ◇ w))`。
  - 编译外部 superpose proof 中的 collapse lemmas。
  - 生成 judge 可接受的 `have`、`congrArg`、`exact` 证书。
  - 不依赖外部 theorem import 或 known-proof 表。

当前 sample200 中 false 已全部解决：

- false：`100/100`
- true：`86/100`

仍失败的 true 样本：

- `true_1167_2000`, `true_1698_555`, `true_1604_1822`,
  `true_2860_3458`, `true_1738_1258`, `true_2654_2864`,
  `true_2789_898`, `true_2935_3138`, `true_428_3725`,
  `true_1500_498`, `true_691_1976`, `true_2771_2775`,
  `true_2055_2656`, `true_1636_1839`

`submissions/solo_official/solver.py` 仍未自动同步；最终官方导出单独处理。
