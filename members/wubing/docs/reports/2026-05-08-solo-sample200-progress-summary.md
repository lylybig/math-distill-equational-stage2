# Stage 2 Solo sample200 迭代总结

日期：2026-05-08

## 一句话结论

当前官方 Solo solver 已从最初 sample200 `175/200` 提升到 `187/200`，并且运行时 LLM calls 从 `25` 降到 `0`。也就是说，当前最佳版本 `2026-05-08/v8` 已经是 no-LLM runtime 的可复现 deterministic certificate baseline。

## 当前最佳版本

- 版本：`solvers/solo_official/versions/2026-05-08/v8/`
- current：`solvers/solo_official/current/`
- sample200：`187A / 13R / 0E`
- accepted rate：`93.50%`
- true / false accepted：`87 / 100`
- LLM calls：`0`
- judge calls：`361`
- aggregate problem elapsed：`2950.41s`（parallel run 中不是 wall time）
- wall time：约 `435.8s`（`7m15.8s`）
- solver bytes：`213368`
- solver hash：`dce917ff9673cc285297eae13aaa12136f26fff1cfc6663940ed9a6903558831`

评估证据：

- sample200 run：`artifacts/runs/2026-05-08/official-draft-d10-repair-sample200-parallel-w8/`
- version manifest：`solvers/solo_official/versions/2026-05-08/v8/manifest.json`
- current manifest：`solvers/solo_official/current/manifest.json`

`submissions/solo_official/solver.py` 尚未同步到 v8；正式导出应单独执行，避免训练迭代误改官方提交目录。

## 版本演进

| 版本 | 主要变化 | sample200 | true / false | LLM calls | 备注 |
| --- | --- | ---: | ---: | ---: | --- |
| `2026-05-07/v1` | opnorm 初始 baseline | `175/200` | `77 / 98` | `25` | false 仍有 2 个未解决 |
| `2026-05-07/v2` | fin7 false907 修复 | `176/200` | `77 / 99` | `24` | false +1 |
| `2026-05-07/v3` | fin5 false1682 修复 | `177/200` | `77 / 100` | `23` | false 达到 `100/100` |
| `2026-05-08/v4` | deterministic grind true fallback | `183/200` | `83 / 100` | `17` | true +6 |
| `2026-05-08/v5` | Vampire/superpose projection/absorption compilers | `185/200` | `85 / 100` | `15` | true +2 |
| `2026-05-08/v6` | collapse compiler | `186/200` | `86 / 100` | `14` | true +1 |
| `2026-05-08/v7` | `MAX_LLM_ROUNDS = 0` | `186/200` | `86 / 100` | `0` | no-LLM runtime baseline |
| `2026-05-08/v8` | square-shuffle + idempotent-expansion compilers | `187/200` | `87 / 100` | `0` | 当前最佳 |

核心趋势：

- false 侧已经从 `98/100` 提升到 `100/100`，当前主要瓶颈已经转为 true proof generation。
- true 侧从 `77/100` 提升到 `87/100`，主要来自 deterministic proof compiler，而不是运行时 LLM。
- LLM runtime 依赖已经完全移除：v8 在 sample200 上 `llmTotalCalls=0`。
- 并发评估已稳定使用 `--max-workers 8`；v8 sample200 wall time 约 7 分钟级别。

## 关键改动说明

当前提升主要来自三类 deterministic certificate 能力：

1. false counterexample coverage
   - v1 到 v3 主要补齐 false 侧。
   - 当前 sample200 false 已全部 accepted。

2. Lean 内置 tactic 与结构化 proof compiler
   - v4 引入 deterministic true fallback，显著提升 true accepted。
   - v5/v6 将外部 Vampire/superpose proof pattern 手工编译为 judge 可接受的 `have` / `calc` / `congrArg` 证书。

3. no-LLM 稳定化
   - v7 在 mass/gemma 服务不可用时把 `MAX_LLM_ROUNDS` 调为 `0`，保持 sample200 `186/200`。
   - v8 继续在 no-LLM 条件下提升到 `187/200`，并修复一个长尾搜索导致的回归风险。

v8 没有做的事情：

- 没有新增 known-proof table entry。
- 没有 import 外部 `equational_theories` theorem。
- 没有恢复运行时 LLM fallback。
- 没有修改 `submissions/solo_official/solver.py`。

## 当前判断

sample200 已经足够证明当前 solver 的本地闭环能力：能生成 Lean 4 judge 可验证 certificate，且不依赖 LLM 服务。

但 sample200 已不适合作为唯一训练目标。继续只针对 sample200 剩余 13 个 true failure 做模板，容易变成小样本过拟合。后续更应该把 sample200 定位为固定回归集和 promote gate，而不是唯一训练集。

当前剩余失败的形态：

- 数量：13 个，全部是 true proof miss。
- false 侧：0 个失败。
- 外部 `Generated/` 目录基本能找到 proof source，但不能直接作为官方 judge certificate 使用。
- 下一步价值在于把外部 proof trace 转成可泛化的 deterministic proof template。

## 下一步

建议按两条线推进：

1. 保持 sample200 作为版本门禁
   - 每次 draft 如果 targeted 有正收益，再跑 sample200。
   - 只有 sample200 accepted count 提升且无 error，才 promote 到 `versions/` 和 `current/`。

2. 扩大训练/验证数据面
   - 构建 order4 分层扩展集，例如 `sample1000` 或 `sample5000`。
   - 用 v8 跑 no-LLM baseline，按失败 proof pattern 聚类。
   - 优先实现能覆盖多题的 proof compiler，而不是只修 sample200 单点。

order5 建议先做小规模 smoke，不建议在 order4 分层验证集稳定前直接大规模投入。

## 数据来源

- `solvers/solo_official/versions/*/*/manifest.json`
- `solvers/solo_official/current/manifest.json`
- `artifacts/runs/2026-05-08/official-draft-d10-repair-sample200-parallel-w8/summary.json`
- `artifacts/runs/2026-05-08/official-draft-d10-repair-sample200-parallel-w8/results/sample_200.json`
