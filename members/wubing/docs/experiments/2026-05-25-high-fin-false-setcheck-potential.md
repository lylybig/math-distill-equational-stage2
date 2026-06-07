# Fin 13/25/43 false setcheck 潜力复核

日期：2026-05-25

## 目标

复核截图中占比较高的 `Fin 13`、`Fin 25`、`Fin 43` finite witness，判断它们在当前 order5 strategy registry 之后还能新增多少 false 覆盖。

本次只做离线候选分析，不修改 `solver.py`，不写正式 registry，不运行 remote judge smoke。

## 输入

- 当前覆盖摘要：`data/processed/order5_strategy_registry/coverage_summary.json`
- 当前 active strategy 快照：`data/processed/order5_strategy_registry/strategies.json`
- source/target cache：
  - `data/processed/order5_strategy_registry/setcheck_source_target_cache.jsonl`
  - `data/processed/order5_strategy_registry/candidates/false_non_affine_all4x4_source_target_cache_20260520.jsonl`
- 高阶候选产物：
  - `data/processed/order5_strategy_registry/candidates/false_affine*.jsonl`
  - `data/processed/order5_strategy_registry/candidates/false_non_affine_all4x4_after_current_exact_20260520.jsonl`
  - `data/processed/order5_strategy_registry/candidates/false_non_affine_all4x4_union_batch_after_current_20260520.jsonl`
  - `external/equational_theories/equational_theories/LinearOps.lean`

本轮新落盘产物：

- `data/processed/order5_strategy_registry/candidates/false_high_fin_13_25_43_current_potential_fast_20260525_summary.json`
- `data/processed/order5_strategy_registry/candidates/false_high_fin_13_25_43_current_potential_fast_20260525.jsonl`

## 方法

先用 `strategies.json`、predicatecheck bank、paircheck bank 和 source/target cache 重建当前 active false 覆盖 mask。

Sanity check 结果：

- 重建出的 active false union：`2,369,622,194`
- `coverage_summary.json.deterministic_false_covered`：`2,369,622,194`

两者一致，因此后续 `current_false_union_increment` 可视为当前 registry 之后的 false 增量。

候选口径：

- affine 候选使用符号线性同余计算 source set。
- 非 affine `Refutation42/Refutation931` 使用已缓存 source bitset，避免重新扫描大表。
- 额外纳入 `LinearOps.lean` 中 `Fin 13/25/43` 的线性 finite witness。
- 不套 `>=100k` 合并门槛，先统计真实潜力。

## 结果

当前 baseline：

| 指标 | 数值 |
| --- | ---: |
| `total_pairs` | `3,915,693,200` |
| `deterministic_false_covered` | `2,369,622,194` |
| `deterministic_true_covered` | `1,366,426,483` |
| `unresolved_estimate` | `179,644,523` |
| `conflict_count` | `0` |

高阶候选整体：

| 口径 | 数值 |
| --- | ---: |
| 候选数 | `71` |
| 单候选增量直接求和，不去重 | `1,047,774` |
| 贪心去重后累计新增 | `129,131` |
| 占当前 unresolved 比例 | `0.072%` |
| 若全部通过并合并后的 false covered | `2,369,751,325` |
| 若 true 覆盖不变，unresolved 估计降至 | `179,515,392` |

按 `Fin` 阶数拆分：

| Fin | 候选数 | 单项增量和 | 贪心去重贡献 | 单候选最大增量 |
| ---: | ---: | ---: | ---: | ---: |
| 13 | `66` | `1,031,176` | `127,195` | `37,964` |
| 25 | `3` | `6,690` | `1,936` | `5,905` |
| 43 | `2` | `9,908` | `0` | `4,958` |

阈值视角：

| 口径 | `>=100k` | `>=10k` | `>=1k` | `>0` |
| --- | ---: | ---: | ---: | ---: |
| 单候选当前增量条数 | `0` | `28` | `55` | `71` |
| 贪心边际条数 | `0` | `3` | `16` | `34` |

贪心边际最高的候选：

| order | label | current increment | greedy increment |
| ---: | --- | ---: | ---: |
| 13 | `affine_mod13_a10_b4_c1` | `37,964` | `37,964` |
| 13 | `affine_mod13_a4_b10_c1` | `37,889` | `37,889` |
| 13 | `affine_mod13_a7_b7_c0` | `10,622` | `10,622` |
| 13 | `affine_mod13_a11_b3_c0` | `7,403` | `7,098` |
| 13 | `affine_mod13_a3_b11_c0` | `7,402` | `6,674` |
| 13 | `affine_mod13_a9_b5_c0` | `10,400` | `5,509` |
| 13 | `affine_mod13_a5_b9_c0` | `10,405` | `5,506` |
| 13 | `affine_mod13_a11_b5_c0` | `2,658` | `2,513` |
| 13 | `affine_mod13_a4_b11_c9` | `1,356` | `1,243` |
| 13 | `affine_mod13_a11_b4_c9` | `1,347` | `1,234` |
| 25 | `linearops.LinearInvariance1.fin25_a12_b14_c0` | `5,905` | `1,151` |

## 观察

1. 截图里 `Fin 13/25/43` 的 witness 数量看起来大，但那是 finite witness inventory，不等同于当前 registry 后的新增 deterministic coverage。
2. `Fin 13` 是主要来源；`Fin 25` 和 `Fin 43` 单独仍有正增量，但在这批高阶候选的贪心去重后贡献很小。
3. 很多 `affine_mod13_a10_b4_c*` 单项增量相同，说明它们覆盖集合高度重叠；合并时不能按单项增量相加。
4. `Refutation42` 单独 current increment 为 `10,622`，但和 `affine_mod13_a7_b7_c0` 的覆盖重叠很强；在当前排序下它的独立边际为 `0`。
5. `Fin 43` 两个 LinearOps witness 单项分别约 `4,958`、`4,950`，但被前面候选吸收后本轮 greedy 边际为 `0`。

## 是否可以合并到 registry

如果团队接受万级甚至千级 tail 策略，这批候选可以进入 registry 合并评审，但不建议理解为“71 条都直接合并”。

建议合并条件：

1. 只考虑贪心边际 `>0` 的候选或按同族 packet 合并；当前是 `34` 条，而不是全部 `71` 条。
2. 对 packet 做 true-overlap audit，必须保持 `current_true_overlap_count = 0`。
3. 对每个代表 family 做 remote-http judge smoke，优先覆盖：
   - 最大边际候选；
   - 非平凡 order5 source -> order5 target 代表 pair；
   - `LinearOps` 高阶 direct encoding 代表；
   - 已有策略重叠样例。
4. 对 order >= 10 的 finite model certificate 继续使用 direct match 或已确认可过 judge 的编码路径，不回退到可能有 parser 限制的 `finOpTable` 单 digit 路径。
5. 正式 registry 只记录去重后的策略和证据，不把 raw coverage 或单项增量和当作新增覆盖。

按当前结果，若放宽到万级：

- 可以优先评审 `affine_mod13_a10_b4_c1`、`affine_mod13_a4_b10_c1`、`affine_mod13_a7_b7_c0` 三个万级边际候选。
- 它们合计贪心边际 `86,475`，仍不到 `100k`，但实现成本低、语义清楚。

若放宽到千级：

- 可以把前 `16` 条贪心边际 `>=1k` 的候选组成一个 small-tail packet。
- 该 packet 贡献 `122,460`，已经超过 `100k` 的 batch 级新增覆盖。

## 结论

`Fin 13/25/43` 高阶 finite witness 值得保留为 tail false setcheck packet，但不是新的大块主线覆盖来源。

当前最现实的路线是：把 `Fin 13` affine 家族中贪心边际非零的候选做成 small-tail packet，完成 true-overlap audit 和 remote smoke 后，再按团队接受的阈值决定是否合并。若阈值仍坚持单策略 `>=100k`，这批应继续 parking；若接受 batch 级 `>=100k` 或万级策略，则可以进入 registry 合并流程。

## 下一步

1. 生成 `greedy_increment_after_previous_high_fin > 0` 的候选 packet。
2. 跑 true-overlap audit，确认无 true 冲突。
3. 为 top candidates 生成 representative pair smoke input。
4. 使用 remote-http primary backend `http://10.220.69.172:8888` 做小样本 judge smoke。
5. 如果通过，再准备 registry bank row 或正式 `order5_strategy_registry.py` 合并 patch。

## 2026-05-25 续扫补充：affine 24-43、Fin17 batch、all4x4 remaining

本补充使用同一天后续 current registry 摘要：

| 指标 | 数值 |
| --- | ---: |
| `total_pairs` | `3,915,693,200` |
| `deterministic_false_covered` | `2,369,622,194` |
| `deterministic_true_covered` | `1,369,895,240` |
| `unresolved_estimate` | `176,175,766` |
| `conflict_count` | `0` |

新增产物：

- `data/processed/order5_strategy_registry/candidates/false_affine_mod_highfin24_31_current_rank_20260525_summary.json`
- `data/processed/order5_strategy_registry/candidates/false_affine_mod_highfin32_37_current_rank_20260525_summary.json`
- `data/processed/order5_strategy_registry/candidates/false_affine_mod_highfin38_43_current_rank_20260525_summary.json`
- `data/processed/order5_strategy_registry/candidates/false_non_affine_all4x4_remaining_current_rerank_20260525.jsonl`
- `data/processed/order5_strategy_registry/candidates/false_non_affine_all4x4_remaining_current_rerank_20260525_summary.json`
- `data/processed/order5_strategy_registry/candidates/false_high_fin_mod17_current_truecheck_selection_20260525_summary.json`
- `data/processed/order5_strategy_registry/candidates/false_high_fin_mod17_top1_directmatch_decidefin_smoke_20260525_summary.json`

### affine mod 24-43

使用 `scripts/data/rank_order5_affine_mod_candidates.py`，在同一个 residual sample
`current_residual_false_mining_round3_after_postedge5_falsemerge_shape_16000_seed20260522_residual_sample.jsonl`
上按 `min_sample_hits=3` 扫描 `x*y = a*x + b*y + c mod n`。

| moduli | elapsed seconds | sample candidates | exact scored | `best_increment` | `ge_1m_count` |
| --- | ---: | ---: | ---: | ---: | ---: |
| `24-31` | `741.150` | `0` | `0` | `0` | `0` |
| `32-37` | `1080.119` | `0` | `0` | `0` | `0` |
| `38-43` | `1630.299` | `0` | `0` | `0` | `0` |

解释：在 1645 对 current false residual sample 上没有任何 `sample_hit_count >= 3`
的候选进入 exact scoring。按这一路线的历史表现，真正百万级单候选通常会在该样本上有多个 hit；
因此 `24-43` 的简单 affine high-fin 扩展不是当前百万级主线。

### Fin17 affine batch

`false_high_fin_mod17_current_truecheck_selection_20260525_summary.json` 仍是本轮唯一达到百万级的 high-fin setcheck 证据：

- greedy selected count：`10`
- cumulative exact current false union increment：`4,256,474`
- 第 1 个候选：`false.finmodel.setcheck.affine_mod_probe.mod17.a7.b11.c0.all_equations`
  - single exact current false union increment：`499,148`
  - true overlap：`0`
- 第 2 个候选后 cumulative：`997,855`
- 第 3 个候选后 cumulative：`1,438,731`

但 certificate smoke 仍阻塞，不能合并 registry。对 top1 使用 direct `match i.val, j.val`
表编码和标准 `refine ⟨Fin 17, m, ?_⟩; decideFin!`：

| tier | representative pair | remote result |
| --- | --- | --- |
| new order4 source -> order5 target | `503 -> 51201` | `REMOTE_SIMPLE_API_REJECTED`，约 `301.52s` |
| new order5 source -> order4 target | `4795 -> 3079` | `REMOTE_SIMPLE_API_REJECTED`，约 `301.43s` |
| new order5 source -> order5 target | `4787 -> 51201` | `REMOTE_SIMPLE_API_REJECTED`，约 `301.54s` |
| overlap existing | `1 -> 46794` | accepted，约 `5.47s` |

结论：Fin17 batch 覆盖上满足 `>=1,000,000`，soundness/true-overlap 离线证据也成立；
但新覆盖代表 pair 在官方 remote judge 上仍超时或 rejected，所以不是 merge-ready。

### all4x4 remaining 当前复核

对 `false_non_affine_all4x4_remaining_after_tail_current_20260520.txt` 的 925 个剩余表，
用 `false_non_affine_all4x4_source_target_cache_20260520.jsonl` 的 source bitset
在当前 registry mask 下重新排名，输出 top 80。

| 指标 | 数值 |
| --- | ---: |
| 输出候选数 | `80` |
| 最大 current increment | `38,043` |
| `>=1m` | `0` |
| `>=100k` | `0` |
| `>=10k` | `80` |

top 候选是 `etp_refutation899`，order `9`，current increment `38,043`。
top 80 中没有 order `>=10` 的 high-fin 表；由于排序按 current increment 降序，remaining all4x4 bank
当前不存在百万级或十万级剩余 setcheck 候选。

### 更新后结论

当前 high-fin false setcheck 的状态是：

1. 覆盖目标层面，Fin17 affine batch 已经达到 `exact_union_increment >= 1,000,000`。
2. 合并目标层面，Fin17 仍因 representative remote judge smoke 失败而不能进入 registry。
3. `Fin 13/25/43`、affine `24-43`、remaining all4x4 非 affine bank 都没有新的百万级 current 增量。
4. 下一轮如果继续专挖 high-fin，应优先解决 Fin17 certificate 编码或寻找新的非 affine high-fin model source；继续扩大简单 affine modulus 搜索的 ROI 很低。

## 2026-05-25 再更新：Fin17 source-first smoke 突破

后续复核发现，Fin17 top1 失败不是模型或 soundness 问题，而是 representative pair 选择问题。原先按 target 简单度选择的代表会触发 `decideFin!` 长尾；改成优先选择 source 结构较浅的 order5 source -> order4 target 后，direct `match i.val, j.val` 表编码可在 remote judge 通过。

最终选集产物：

- `data/processed/order5_strategy_registry/candidates/false_high_fin_mod17_sourcefirst_1m_selection_20260525.jsonl`
- `data/processed/order5_strategy_registry/candidates/false_high_fin_mod17_sourcefirst_1m_selection_20260525_summary.json`
- `data/processed/order5_strategy_registry/candidates/false_high_fin_mod17_top3_sourcefirst_smoke_20260525_results.jsonl`
- `data/processed/order5_strategy_registry/candidates/false_high_fin_mod17_batch5_sourcefirst_smoke_20260525_results.jsonl`

选集使用 Fin17 greedy selection 中的 batch `1, 2, 5`：

| batch | candidate | marginal increment | remote smoke |
| ---: | --- | ---: | ---: |
| `1` | `affine_mod17_a7_b11_c0` | `499,148` | `4/4 accepted` |
| `2` | `affine_mod17_a11_b7_c0` | `498,707` | `4/4 accepted` |
| `5` | `affine_mod17_a9_b2_c0` | `438,925` | `4/4 accepted` |

合计：

- cumulative exact current false union increment：`1,436,780`
- true overlap：三个候选的 `true_overlap_count`、`true_source_target_overlap_count`、`true_explicit_pair_overlap_count` 均为 `0`
- remote backend：`http://10.220.69.172:8888`
- remote smoke：`12/12 accepted`
- projected false coverage：`2,371,058,974`
- projected unresolved estimate：`174,738,986`

注意：batch `3` 的 source-first 代表仍在约 `301.5s` 被 remote rejected，因此本次 `>=1m` 包不包含 batch `3`。后续若要继续扩大 Fin17 coverage，应优先按 source-first 排序为 batch `3/4/6...` 寻找可过代表，而不是继续沿原 target-first representative 策略。
