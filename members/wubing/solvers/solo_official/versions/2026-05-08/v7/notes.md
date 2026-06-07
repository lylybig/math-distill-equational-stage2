# 2026-05-08/v7 no-LLM runtime sample200 186

这是从 `2026-05-08/d9` promote 的 no-LLM 运行版本，基于 `2026-05-08/v6`。

- sample200：`186/200`
- accepted rate：`93.00%`
- accepted true / false：`86 / 100`
- LLM calls：`0`
- judge calls：`376`
- aggregate problem elapsed：`3565.66s`（parallel run 中不是 wall time）
- wall time：约 `516.7s`（`8m36.7s`，按 `createdAt` 到 `summary.json` mtime 估算）
- solver hash：`788553fd06bdc81b9eb0ed652b510b3d901fca0e87fb9f22783c65bb8f7407b0`
- solver bytes：`204806`
- sample200 run：`artifacts/runs/2026-05-08/official-draft-d9-sample200-parallel-w8/`
- failed-subset run：`artifacts/runs/2026-05-08/official-draft-d9-truefailed14-parallel-w8/`

相对 `2026-05-08/v6`：

- accepted：`186 -> 186`（`+0`）
- rejected：`14 -> 14`（`+0`）
- errors：`0 -> 0`（`+0`）
- true accepted：`86 -> 86`（`+0`）
- false accepted：`100 -> 100`（`+0`）
- LLM calls：`14 -> 0`（`-14`）

核心改动：

- 将 `MAX_LLM_ROUNDS` 设置为 `0`。
- 保留 v6 的 deterministic proof compiler 和 false counterexample coverage。
- 在 mass/gemma 服务关闭时，sample200 仍可完整运行，不依赖 LLM endpoint。

当前 sample200 中 false 已全部解决：

- false：`100/100`
- true：`86/100`

仍失败的 true 样本：

- `true_1167_2000`, `true_1698_555`, `true_1604_1822`, `true_2860_3458`, `true_1738_1258`, `true_2654_2864`, `true_2789_898`, `true_2935_3138`, `true_428_3725`, `true_1500_498`, `true_691_1976`, `true_2771_2775`, `true_2055_2656`, `true_1636_1839`

`submissions/solo_official/solver.py` 仍未自动同步；最终官方导出单独处理。
