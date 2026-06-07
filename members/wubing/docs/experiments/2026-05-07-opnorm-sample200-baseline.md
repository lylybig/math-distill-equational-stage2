# 2026-05-07 opnorm sample200 baseline

日期：2026-05-07

## 目标

记录当前官方 Solo `solver.py` 在标准 `sample_200` 上的 baseline（基线）评估结果，作为后续 solver 改进、LLM fallback（大模型兜底）实验和失败样本分析的对照。

本次 baseline 的重点是：

- 使用官方 runner 和官方 judge 输出作为唯一证据。
- 记录 accepted rate（通过率）。
- 记录总耗时的秒数和分秒表达。
- 单独区分 deterministic solved（确定性策略解决）和 LLM solved（LLM 实际贡献）。

## 输入

- submission（提交目录）：`submissions/solo_official/`
- solver：`submissions/solo_official/solver.py`
- problem set（题集）：`external/equational-theories-lean-stage2/examples/problems/sample_200.json`
- run 目录：`artifacts/runs/2026-05-07/official-opnorm-sample200-max1024-round1-baseline/`
- result JSON：`artifacts/runs/2026-05-07/official-opnorm-sample200-max1024-round1-baseline/results/sample_200.json`
- summary：`artifacts/runs/2026-05-07/official-opnorm-sample200-max1024-round1-baseline/summary.json`
- log：`artifacts/runs/2026-05-07/official-opnorm-sample200-max1024-round1-baseline/logs/sample_200.log`

## 配置

- model：`gemma-4-31b`
- base URL：`http://60.171.65.125:30197/v1`
- `llm.max_output_tokens`：`1024`
- `llm.http_timeout_seconds`：`60`
- `llm.stream`：`true`
- `MAX_LLM_ROUNDS`：`1`

本次使用 `1024` 作为 LLM 输出上限，是为了降低 mass 服务在显存有限时的最坏情况预留和排队/生成延迟。

## 运行命令

```bash
timeout 14400s python scripts/evaluator/run_official_solo_history.py \
  --submission submissions/solo_official \
  --suite sample200 \
  --run-id official-opnorm-sample200-max1024-round1-baseline
```

## 结果

| 指标 | 数值 |
| --- | ---: |
| total problems | 200 |
| accepted | 175 |
| rejected | 25 |
| errors | 0 |
| accepted rate | 87.50% |
| accepted true verdicts | 77 |
| accepted false verdicts | 98 |
| judge calls | 561 |
| LLM calls | 25 |
| LLM errors | 0 |
| LLM timeouts | 0 |
| LLM solved | 0 |
| deterministic solved | 175 |
| total elapsed | 2674.35 秒（44 分 34.35 秒） |

LLM 调用耗时统计：

| 指标 | 数值 |
| --- | ---: |
| min | 3.03 秒 |
| avg | 15.22 秒 |
| max | 25.96 秒 |

## 失败样本

本次共有 25 个 failed 样本，其中 true 样本 23 个，false 样本 2 个。

true failed：

- `true_2942_5`
- `true_3108_4642`
- `true_1167_2000`
- `true_1698_555`
- `true_1604_1822`
- `true_2111_1755`
- `true_2860_3458`
- `true_2061_307`
- `true_1738_1258`
- `true_2654_2864`
- `true_2789_898`
- `true_2935_3138`
- `true_2135_2128`
- `true_428_3725`
- `true_1500_498`
- `true_2137_1325`
- `true_691_1976`
- `true_2074_2082`
- `true_2771_2775`
- `true_2055_2656`
- `true_689_1350`
- `true_674_668`
- `true_1636_1839`

false failed：

- `false_907_2534`
- `false_1682_411`

## 结论

这份 run 可以作为当前 sample200 baseline：

- accepted rate 为 87.50%，即 `175/200`。
- LLM 链路稳定，25 次调用没有 timeout，也没有 transport/API error。
- 当前 LLM fallback 没有贡献 accepted；175 个 accepted 全部来自 deterministic path。
- 后续提分应优先针对 25 个 failed ids 做 deterministic proof/counterexample 改进；LLM 方向则应先解决 proof 质量，而不是请求可用性。

## 下一步

- 对 23 个 true failed 样本聚类，优先寻找可模板化的 Lean proof 结构。
- 对 2 个 false failed 样本单独分析反模型搜索为何未产出可接受 certificate。
- 保留本次 run 作为后续 sample200 改动的对照 baseline。
