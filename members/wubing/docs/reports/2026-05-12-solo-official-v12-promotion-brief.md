# Stage 2 Solo v12 promotion 简报

日期：2026-05-12

## 一句话结论

`2026-05-12/v12` 已成为当前最佳 no-LLM deterministic solver，在 50000 题 `test_locked` gate 上达到 `47031A / 2969R / 0E`，比 v11 净增 `+700` 个 accepted，且 false accepted 不变、LLM calls 为 `0`。

## 当前最佳版本

| 项目 | 当前值 |
| --- | --- |
| 当前最佳版本 | `solvers/solo_official/versions/2026-05-12/v12/` |
| 当前工作快照 | `solvers/solo_official/current/solver.py` |
| 来源 draft | `solvers/solo_official/drafts/2026-05-12/d5/` |
| base version | `2026-05-12/v11` |
| solver hash | `f43c446d60073dbfcddd34858ac3cc648f4eaa78faa151b51830100f771ec570` |
| solver bytes | `263124` |
| runtime LLM calls | `0` |
| 官方提交目录 | `submissions/solo_official/solver.py` 尚未同步到 v12 |

说明：v12 已同步到 `current`，但没有导出覆盖 `submissions/solo_official/solver.py`。正式提交前仍需要单独执行 export/sync 步骤。

## Gate 结果

| Gate | v11 accepted | v11 accepted rate all / true / false | v12 accepted | v12 accepted rate all / true / false | delta | v12 judge calls | LLM calls |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `dev_fast` 2000 | `1861A / 139R / 0E` | `93.05% / 86.10% / 100.00%` | `1895A / 105R / 0E` | `94.75% / 89.50% / 100.00%` | `+34A` | `3541` | `0` |
| `dev_main` 10000 | `9293A / 707R / 0E` | `92.93% / 85.96% / 99.90%` | `9442A / 558R / 0E` | `94.42% / 88.94% / 99.90%` | `+149A` | `18291` | `0` |
| `test_locked` 50000 | `46331A / 3669R / 0E` | `92.66% / 85.45% / 99.87%` | `47031A / 2969R / 0E` | `94.06% / 88.25% / 99.87%` | `+700A` | `92462` | `0` |

`test_locked` all accepted rate 从 v11 的 `92.66%` 提升到 v12 的 `94.06%`，提升约 `+1.40` 个百分点；true accepted rate 从 `85.45%` 提升到 `88.25%`，提升 `+2.80` 个百分点。新增 accepted 全部来自 true 侧；false accepted rate 维持 `99.87%`，没有牺牲 false 侧覆盖。

## 基准对比

### 相对 opnorm baseline

opnorm baseline 目前有直接可比的 `sample200` 证据；v12 已补跑同一 `sample200` 作为报告对照。

| 数据集 | 版本 | accepted | accepted rate all / true / false | judge calls | LLM calls |
| --- | --- | ---: | ---: | ---: | ---: |
| `sample200` | opnorm baseline `2026-05-07/v1` | `175A / 25R / 0E` | `87.50% / 77.00% / 98.00%` | `561` | `25` |
| `sample200` | v12 | `193A / 7R / 0E` | `96.50% / 93.00% / 100.00%` | `321` | `0` |

同集 `sample200` 上，v12 相对 opnorm baseline 净增 `+18A`，all accepted rate 提升 `+9.00` 个百分点，true accepted rate 提升 `+16.00` 个百分点，false accepted rate 提升 `+2.00` 个百分点，同时运行时 LLM calls 从 `25` 降到 `0`。

opnorm baseline 没有 50000 题 `test_locked` 同集完整 run。若只看 order4 full-gate 的最早可比 no-LLM 版本，v10 在 `test_locked` 上为 `40971A / 9029R / 0E`，accepted rate 为 `81.94% / 64.01% / 99.87%`；v12 相对 v10 为 `+6060A`，true accepted 为 `+6060`，false accepted 不变。

### 相对上一个最佳版本

上一个最佳版本是 `2026-05-12/v11`。v12 对 v11 的提升在三个 gate 上都复现：

| Gate | v11 | v12 | accepted delta | all rate delta | true rate delta | false rate delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `dev_fast` | `1861A` | `1895A` | `+34A` | `+1.70` pp | `+3.40` pp | `+0.00` pp |
| `dev_main` | `9293A` | `9442A` | `+149A` | `+1.49` pp | `+2.98` pp | `+0.00` pp |
| `test_locked` | `46331A` | `47031A` | `+700A` | `+1.40` pp | `+2.80` pp | `+0.00` pp |

这里 `pp` 表示 percentage point（百分点）。

## 关键改动

v12 来自 d5，核心新增是 compact anchor h-instantiated grind compiler（紧凑锚点 h 实例化后交给 `grind` 的证明编译器）。

它面向一类单变量 LHS 的 true 目标：

- 先识别 `eq1` 是单变量左侧，例如 `x = ...`。
- 选择 goal 中第一个变量作为 anchor。
- 对 goal 中每个变量，各生成一次 `h` 实例，把非 LHS 的 `h` 参数固定到 anchor。
- 最后用 Lean 4 的 `grind` 闭合。

这个策略来自 proofbank accepted certificates 的共同形态：很多样本不需要长证明表，只需要少量稳定的 `h` 实例作为锚点，`grind` 就能完成剩余等式推理。它不是 pair-level known-proof table，也没有运行时读取 proofbank。

## 验证证据

- focused test：`test_d19_solver_emits_compact_anchor_hinst_grind_for_eq1356_proofbank_failure`
- proofbank targeted：`official-draft-d5-anchor-targeted4-w2-abs3`，`4A / 0R / 0E`
- proofbank failed53 subset：`official-draft-d5-proofbank-failed53-w8`，`27A / 26R / 0E`，对比 d4 `6A / 47R / 0E`
- v12 sample200 对照 run：`official-v12-sample200-report-w8`，`193A / 7R / 0E`，true/false accepted 为 `93 / 100`
- full solver tests：`pytest tests/official/test_official_solo_submission.py -q`，`29 passed in 356.52s`
- final submission-dir check：`submissions/solo_official/` 最终只包含 `solver.py`

主要记录文件：

- `solvers/solo_official/versions/2026-05-12/v12/manifest.json`
- `solvers/solo_official/current/manifest.json`
- `solvers/solo_official/drafts/2026-05-12/d5/manifest.json`

## 当前判断

v12 是一次可 promote 的真实提升：三个 gate 都比 v11 更好，`test_locked` 完整 50000 题通过，errors 为 `0`，LLM calls 为 `0`。改动规模仍在官方单文件大小限制内，且 judge calls 在 `test_locked` 上比 v11 少 `576` 次。

需要注意的边界：

- v12 仍只代表 order4 当前闭环上的最佳版本。
- 还没有导出到 `submissions/solo_official/solver.py`。
- 后续不要直接把 proofbank pair 当 known-proof table 扩入 solver；应继续优先抽可泛化 deterministic pattern。

## 下一步

1. 如果准备正式提交，单独执行 v12 到 `submissions/solo_official/solver.py` 的 export，并立即跑官方提交目录单文件测试。
2. 继续分析 v12 在 `test_locked` 剩余 `2969` 个 rejected true 样本，优先从 proofbank 和失败聚类里找能覆盖多题的 deterministic compiler。
3. order5 先做 smoke 和候选池建设，不建议在 order4 v12 残差模式还没消化前直接大规模训练。
