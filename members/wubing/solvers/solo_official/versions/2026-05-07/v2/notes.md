# 2026-05-07/v2 Fin 7 false_907_2534 baseline 176

这是从 `2026-05-07/d1` promote 的当前最佳版本。

- sample200：`176/200`
- accepted rate：`88.00%`
- accepted true / false：`77 / 99`
- LLM calls：`24`
- LLM solved：`0`
- 总耗时：`2654.5s`（44m14.5s）
- sample200 run：`artifacts/runs/2026-05-07/official-draft-d1-sample200/`
- failed subset run：`artifacts/runs/2026-05-07/official-draft-d1-failed25/`

相对 `2026-05-07/v1`，新增解决：

- `false_907_2534`

仍失败：

- false：`false_1682_411`
- true：`true_2942_5`, `true_3108_4642`, `true_1167_2000`, `true_1698_555`, `true_1604_1822`, `true_2111_1755`, `true_2860_3458`, `true_2061_307`, `true_1738_1258`, `true_2654_2864`, `true_2789_898`, `true_2935_3138`, `true_2135_2128`, `true_428_3725`, `true_1500_498`, `true_2137_1325`, `true_691_1976`, `true_2074_2082`, `true_2771_2775`, `true_2055_2656`, `true_689_1350`, `true_674_668`, `true_1636_1839`

下一步优先创建 `d2`，继续解决 `false_1682_411`；若 false 全部解决，再按 true failure 结构聚类加入 deterministic proof templates。
