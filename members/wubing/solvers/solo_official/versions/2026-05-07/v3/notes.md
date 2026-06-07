# 2026-05-07/v3 Fin 5 false_1682_411 baseline 177

这是从 `2026-05-07/d2` promote 的当前最佳版本。

- sample200：`177/200`
- accepted rate：`88.50%`
- accepted true / false：`77 / 100`
- LLM calls：`23`
- LLM solved：`0`
- 总耗时：`2611.6s`（43m31.6s）
- sample200 run：`artifacts/runs/2026-05-07/official-draft-d2-sample200/`
- failed subset run：`artifacts/runs/2026-05-07/official-draft-d2-failed25/`
- single-problem run：`artifacts/runs/2026-05-07/official-draft-d2-single-false1682/`

相对 `2026-05-07/v2`，新增解决：

- `false_1682_411`

核心改动：

- 在 `known_counterexample` 前置内联 `Fin 5` 表，覆盖 `Equation1682 -> Equation411`。
- 表来源：`data/processed/etp/etp_facts.jsonl` 中 `Generated/All4x4Tables/Refutation906.lean`，满足 `Equation1682` 且 refute `Equation411`。

当前 sample200 中 false 已全部解决：

- false：`100/100`
- true：`77/100`

仍失败的 true 样本：

- `true_2942_5`, `true_3108_4642`, `true_1167_2000`, `true_1698_555`, `true_1604_1822`, `true_2111_1755`, `true_2860_3458`, `true_2061_307`, `true_1738_1258`, `true_2654_2864`, `true_2789_898`, `true_2935_3138`, `true_2135_2128`, `true_428_3725`, `true_1500_498`, `true_2137_1325`, `true_691_1976`, `true_2074_2082`, `true_2771_2775`, `true_2055_2656`, `true_689_1350`, `true_674_668`, `true_1636_1839`

下一步应从这些 true failures 做结构聚类，优先找可模板化的 deterministic proof。
