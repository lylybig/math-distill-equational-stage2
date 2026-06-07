# Order4 22M 上周实验报告

日期：2026-05-18
覆盖周期：2026-05-11 至 2026-05-17

## 一句话结论

上周 order4 22M 工作的核心进展不是全量 22M official judge sweep（官方验证器全量扫），而是把 22M 语料沉淀成可复现 split、用远程 judge 验证当前 solver gate，并通过 proof bank（证明库）把 true 侧高价值样本转成可泛化 deterministic compiler（确定性证明编译器）。当前最佳 v12 在 `test_locked` 50000 题上达到 `47031A / 2969R / 0E`，比 v11 净增 `+700A`，运行时 LLM calls 为 `0`。

## 语料与口径

`data/processed/order4_implication_problems/` 是本轮 order4 22M directed implication corpus（有向蕴含语料），来自 `raw_implications.csv`：

| 项目 | 数值 |
| --- | ---: |
| 总行数 | `22,028,942` |
| true | `8,173,585` |
| false | `13,855,357` |
| law count | `4,694` |
| shard count | `23` |

`data/processed/order4_splits/` 是从 22M 语料派生的固定训练/评估 split，seed 为 `20260508`：

| Split | 规模 | true | false | 用途 |
| --- | ---: | ---: | ---: | --- |
| `dev_fast` | `2,000` | `1,000` | `1,000` | 快速训练 gate |
| `dev_main` | `10,000` | `5,000` | `5,000` | 主训练 gate |
| `test_locked` | `50,000` | `25,000` | `25,000` | 锁定泛化 gate |
| `stress_true` | `5,000` | `5,000` | `0` | true 侧压力测试 |
| `stress_false` | `5,000` | `0` | `5,000` | false 侧压力测试 |
| `label_probe_100k` | `100,000` | `37,062` | `62,938` | 近自然分布探针 |

重要边界：上周没有跑全量 22M official judge sweep。全量 22M 只作为候选池和分层抽样宇宙；solver 可提交性仍以远程 judge 接受的 certificate（证书）为边界。

## Solver Gate 结果

当前最佳版本为 `solvers/solo_official/versions/2026-05-12/v12/`，已同步到 `solvers/solo_official/current/solver.py`。v12 是 no-LLM deterministic solver，`solver.py` 大小 `263,124` bytes，仍低于官方 `500,000` bytes 限制。

| Gate | v12 结果 | all rate | true accepted | false accepted | judge calls | LLM calls |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `dev_fast` | `1895A / 105R / 0E` | `94.75%` | `895 / 1000` | `1000 / 1000` | `3,541` | `0` |
| `dev_main` | `9442A / 558R / 0E` | `94.42%` | `4447 / 5000` | `4995 / 5000` | `18,291` | `0` |
| `test_locked` | `47031A / 2969R / 0E` | `94.06%` | `22063 / 25000` | `24968 / 25000` | `92,462` | `0` |

相对 v11，v12 在 `test_locked` 上净增 `+700A`，增量全部来自 true accepted；false accepted 不变。相对最早可比 full-gate no-LLM 版本 v10，v12 在 `test_locked` 上从 `40971A` 提升到 `47031A`，净增 `+6060A`。

## Proof Bank 与 22M 直采

上周 proof bank 的作用是把 22M 派生样本、train failure（训练失败样本）和外部 proof seed 转成可验证 true certificate，再筛出可泛化模板。当前 bank 汇总：

| 指标 | 数值 |
| --- | ---: |
| attempts | `73,108` |
| accepted attempts | `70,326` |
| latest problem count | `72,282` |
| recent accepted yield | `96.19%` |

其中直接来自 `order4_implication_problems` 的 22M true exploration 仍是小规模探索层：`254` 个 unique problem，latest status 为 `209 accepted / 4 rejected / 41 skipped`；按 attempts 计为 `271` 次尝试，`210 accepted / 19 rejected / 42 skipped`。这说明直接 22M 直采有价值，但当前样本量还不足以代表整个 22M 分布。

`dev_main` 失败池和 high-signal pool 也是 22M 下游产物，但不是 22M 均匀样本。后续报告里应继续区分：

- `dev_main`/`test_locked`：固定 split gate 证据。
- `order4_implication_problems`：全量 22M 候选宇宙。
- proof bank accepted：可验证证书资产，不等同于 solver 已覆盖。
- solver compiler：真正能进入官方提交的泛化策略。

## 关键判断

1. v12 是上周最明确的 solver 侧产出：在 locked gate 上有完整远程 judge 证据，且没有使用运行时 LLM。
2. false 侧接近饱和，当前主要瓶颈仍在 true 侧证明覆盖。
3. 22M 不能直接做原始 lookup table 放进 `solver.py`；需要继续把 proof bank 证据归纳为短模板或编译器。
4. 直接 22M true exploration 应保留在 nightly/proofbank 采样中，但占比不宜过大；它负责发现 dev split 外的新形态，高信号 train failure 负责快速产出。

## 下一步

1. 继续分析 v12 在 `test_locked` 上的 rejected 残差，优先找 true 侧可泛化 proof template。
2. proof bank sampling 维持三类来源平衡：high-signal failures、rejected repair、direct 22M true exploration。
3. 只有出现新 compiler 或大覆盖策略候选时，才考虑扩大到更大 order4 shard smoke；暂不建议发起全量 22M official judge sweep。
4. 若准备正式提交，需要单独确认 `solvers/solo_official/current/solver.py` 与 `submissions/solo_official/solver.py` 的同步状态，并跑提交目录单文件检查。

## 主要证据路径

- `data/processed/order4_implication_problems/manifest.json`
- `data/processed/order4_splits/manifest.json`
- `solvers/solo_official/current/manifest.json`
- `docs/reports/2026-05-12-solo-official-v12-promotion-brief.md`
- `data/processed/proof_banks/gpt_true_certificates/bank_summary.json`
- `data/processed/proof_banks/gpt_true_certificates/attempts.jsonl`
- `data/processed/proof_banks/gpt_true_certificates/latest_by_problem.jsonl`
