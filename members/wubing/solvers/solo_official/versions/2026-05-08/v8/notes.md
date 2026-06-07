# 2026-05-08/v8 no-LLM square-shuffle + idempotent expansion sample200 187

这是从 `2026-05-08/d10` promote 的 no-LLM 当前最佳版本，基于 `2026-05-08/v7`。

- sample200：`187/200`
- accepted rate：`93.50%`
- accepted true / false：`87 / 100`
- LLM calls：`0`
- judge calls：`361`
- aggregate problem elapsed：`2950.41s`（parallel run 中不是 wall time）
- wall time：约 `435.8s`（`7m15.8s`，按 `createdAt` 到 `summary.json` mtime 估算）
- solver hash：`dce917ff9673cc285297eae13aaa12136f26fff1cfc6663940ed9a6903558831`
- solver bytes：`213368`
- sample200 run：`artifacts/runs/2026-05-08/official-draft-d10-repair-sample200-parallel-w8/`
- targeted run：`artifacts/runs/2026-05-08/official-draft-d10-repair-true4082-true428-parallel-w8/`

相对 `2026-05-08/v7`：

- accepted：`186 -> 187`（`+1`）
- rejected：`14 -> 13`（`-1`）
- errors：`0 -> 0`（`+0`）
- true accepted：`86 -> 87`（`+1`）
- false accepted：`100 -> 100`（`+0`）
- LLM calls：`0 -> 0`（`+0`）
- judge calls：`376 -> 361`（`-15`）

核心改动：

- 新增 Equation428-style idempotent-expansion compiler：从 `x = x ◇ (y ◇ (x ◇ (x ◇ z)))` 推出 `a ◇ a = a` 和相关扩张等式，解决 `true_428_3725`。
- 新增 Equation4082-style square-shuffle compiler：把已存在但很靠后的 no-LLM calc proof 前置，避免并发评估中 `true_4082_4109` 因长尾超时回归。
- 保持 `MAX_LLM_ROUNDS = 0`，不依赖 mass/gemma runtime。
- 未新增 known-proof table entry，未使用外部 theorem import。

当前 sample200 中 false 已全部解决：

- false：`100/100`
- true：`87/100`

新解决：

- `true_428_3725`

仍失败的 true 样本：

- `true_1167_2000`, `true_1698_555`, `true_1604_1822`, `true_2860_3458`, `true_1738_1258`, `true_2654_2864`, `true_2789_898`, `true_2935_3138`, `true_1500_498`, `true_691_1976`, `true_2771_2775`, `true_2055_2656`, `true_1636_1839`

`submissions/solo_official/solver.py` 仍未自动同步；最终官方导出单独处理。
