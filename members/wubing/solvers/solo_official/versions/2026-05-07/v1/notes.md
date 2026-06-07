# 2026-05-07/v1 opnorm sample200 baseline 175

这是当前冻结的官方 Solo baseline 版本。

- sample200：`175/200`
- accepted rate：`87.50%`
- LLM calls：`25`
- LLM solved：`0`
- run：`artifacts/runs/2026-05-07/official-opnorm-sample200-max1024-round1-baseline/`
- 实验记录：`docs/experiments/2026-05-07-opnorm-sample200-baseline.md`

该版本保留 `extended_counterexample(... max_n=5 ...)`，没有在 false certificate 中设置 `maxRecDepth`。它是 `false_907_2534` Fin 7 候选改动之前的可回退基线。
