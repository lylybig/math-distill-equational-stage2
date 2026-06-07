# 2026-05-08/v4 deterministic grind sample200 183

这是从 `2026-05-08/d6` promote 的当前最佳版本。

- sample200：`183/200`
- accepted rate：`91.50%`
- accepted true / false：`83 / 100`
- LLM calls：`17`
- judge calls：`417`
- solver hash：`16a82efaa8e4333974298d31e5104297e0eaa98c2eabeb07ce3947cb02d41153`
- solver bytes：`192763`
- sample200 run：`artifacts/runs/2026-05-08/official-draft-d6-sample200-parallel-w8/`
- targeted grind run：`artifacts/runs/2026-05-08/official-draft-d6-grind5-parallel-w8/`

相对 `2026-05-07/v3`，新增解决 6 个 true 样本：

- `true_2942_5`
- `true_2111_1755`
- `true_2061_307`
- `true_2135_2128`
- `true_2137_1325`
- `true_2074_2082`

核心改动：

- 新增 deterministic `try_grind_proof(problem, eq2_text)` true fallback。
- 对 true 目标输出 `intro <eq2 variables>` 后接 Lean 4 `grind`。
- 调用位置放在 `try_transitive_library_proof` 之后、较重的 custom true
  search 和 LLM fallback 之前。

当前 sample200 中 false 已全部解决：

- false：`100/100`
- true：`83/100`

仍失败的 true 样本：

- `true_3108_4642`, `true_1167_2000`, `true_1698_555`, `true_1604_1822`,
  `true_2860_3458`, `true_1738_1258`, `true_2654_2864`,
  `true_2789_898`, `true_2935_3138`, `true_428_3725`,
  `true_1500_498`, `true_691_1976`, `true_2771_2775`,
  `true_2055_2656`, `true_689_1350`, `true_674_668`,
  `true_1636_1839`

下一步应使用 `stage2-train-offline-explore-solver` 对剩余 true failures 做有界离线探索，再交给 `stage2-train-improve-solver` 实现聚焦改进。
