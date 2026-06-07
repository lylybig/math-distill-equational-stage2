# Order5 residual cluster analysis

日期：2026-05-18

## 目标

对当前 `unresolved_estimate=957,323,435` 的 order5 residual（剩余未解决集合）做轻量聚类分析，判断下一轮 true deterministic strategy（真命题确定性策略）和 false deterministic strategy（假命题确定性策略）哪边更有 ROI。

本实验不重新枚举 39 亿 pair，也不修改 `solver.py` 或正式 strategy registry。

## 输入

聚合报告：

- `data/processed/order5_strategy_registry/residual_cluster_report_20260518.json`

生成命令：

```bash
PYTHONPATH=src .venv/bin/python scripts/data/build_order5_residual_cluster_report.py \
  --output-json data/processed/order5_strategy_registry/residual_cluster_report_20260518.json
```

主要来源：

- `data/processed/order5_strategy_registry/coverage_summary.json`
- `data/processed/order5_strategy_registry/current_false_unresolved_after_bank_shape_buckets_50000_seed20260521.json`
- `data/processed/order5_strategy_registry/current_unresolved_after_bank_top_shape_buckets_with_targeted_seed_filter_seed20260521.json`
- `data/processed/order5_strategy_registry/current_unresolved_after_bank_top3_shape_synthesis_targets_seed20260521_summary.json`
- `data/processed/order5_strategy_registry/current_false_unresolved_after_bank_fin3_selector_probe_2000xall_seed20260521.json`
- `data/processed/order5_strategy_registry/predicate_bucket_probe_from_paircheck_v1.json`
- `data/processed/order5_strategy_registry/current_high_setcheck_candidate_rankings_seed20260521.jsonl`

## 方法

只聚合已有 residual artifacts（残差产物）：

1. 当前 coverage summary 提供 `957,323,435` residual 工作宇宙。
2. 50k current false-uncovered sample 提供 shape bucket（句法形状桶）分布。
3. cheap true + targeted seed filter 产物估计 true 侧仍能吃掉的残差比例。
4. Fin3 selector probe 检查裸 finite-model search 在 residual 中的命中率。
5. paircheck predicate probe 检查哪些 source/target feature cluster 值得 false predicatecheck 验证。
6. setcheck ranking 检查继续裸 setcheck 枚举的边际收益。

所有 `residual_estimate_if_uniform` 和 projected count 都是采样优先级估计，不是 soundness evidence（可靠性证据），不能直接进入 registry。

## 结果

当前工作宇宙：

| 指标 | 值 |
| --- | ---: |
| `total_pairs` | `3,915,693,200` |
| `deterministic_false_covered` | `2,334,245,819` |
| `deterministic_true_covered` | `624,123,946` |
| `unresolved_estimate` | `957,323,435` |
| `conflict_count` | `0` |

cheap true filter 信号很强：

| 采样范围 | filtered / sample | rate |
| --- | ---: | ---: |
| 50k residual sample | `19,339 / 50,000` | `38.678%` |
| top3 shape buckets pre-filter | `751 / 1,870` | `40.160%` |

如果按 uniform projection 粗估，50k sample 的 cheap true rate 对应约 `370,273,558` 个 residual pair。这个数不能当新增覆盖，但说明 true 方向还有大块结构可挖。

shape bucket 仍然集中：

| 视图 | top1 | top3 | top5 | top10 | top20 |
| --- | ---: | ---: | ---: | ---: | ---: |
| false-uncovered before true filter | `14,842,112` | `35,812,580` | `54,121,044` | `90,737,971` | `144,705,805` |
| after true + seed filter | `13,418,696` | `34,017,021` | `52,107,178` | `88,506,958` | `140,457,375` |

top buckets 主要是 `roots=var>mul`，depth `4/5`，variable count `3/4/5` 的 source-target 组合。这类 bucket 仍值得 true template session 优先研究，尤其是 target normalizer、projection/singleton/product anchor 的泛化。

Fin3 selector 命中很弱：

| probe | sample | hit | hit rate |
| --- | ---: | ---: | ---: |
| global current false-uncovered | `2,000` | `1` | `0.05%` |
| top1 shape bucket | `775` | `0` | `0%` |
| top2+top3 shape buckets | `1,095` | `0` | `0%` |

这说明继续裸 Fin3/Fin4/Fin5 setcheck 或 selector search 的 ROI 很低。false 侧如果要做大，应该从 paircheck feature cluster 反推 predicate，而不是继续无界枚举模型。

paircheck predicate probe 的 top seed：

| source feature | target feature | paircheck hits | capacity |
| --- | --- | ---: | ---: |
| `rhs_bare=False` | `rhs_bare=False` | `78` | `1,565,083,400` |
| `lhs_lm_rm=x:x` | `rhs_bare=False` | `22` | `1,416,560,144` |
| `rhs_bare=False` | `lhs_lm_rm=x:x` | `15` | `1,058,875,580` |
| `var_count=4` | `rhs_bare=False` | `34` | `749,658,208` |
| `rhs_bare=False` | `lhs_bare=False` | `78` | `666,091,894` |

这里的 capacity 只是潜在容量，不是 union increment。它的价值是给 false predicate session 提供验证顺序：先验证 `enum_order3_2/4/7` 这批 paircheck model 是否能在这些 feature bucket 上形成“source 全满足、target 全反驳”的 predicatecheck。

setcheck 长尾已经明显：

| label | current union increment |
| --- | ---: |
| `enum_order3_767` | `68,462` |
| `enum_order3_742` | `62,509` |
| `enum_order3_743` | `61,350` |
| `enum_order3_402` | `40,371` |

因此裸 setcheck 现在适合做 seed 或 parking lot，不适合作为主线继续烧成本。

## 结论

下一轮 ROI 排序：

1. **True template mining 优先。** cheap true filter 在 residual 样本中有约 `38.7%` 命中，top3 bucket 约 `40.2%`，是当前最像“亿级/千万级”的信号。
2. **False predicatecheck 次优先。** paircheck feature cluster 的 capacity 很大，但必须转成可全量验证的 predicate；不能把 paircheck 行数或 capacity 当作新增覆盖。
3. **裸 setcheck 暂停主线。** 当前最佳 increment 只有 `68,462`，不应继续作为主力挖掘方式。

## 下一步

True session：

- 读取 `residual_cluster_report_20260518.json`。
- 优先研究 top20 after true+seed filter shape buckets，总估计约 `140,457,375`。
- 从 top3 synthesis JSONL 取代表 pair，尝试抽象 `true.proof.templatecheck.*` 条件，而不是逐 pair proofbank。

False session：

- 读取 `residual_cluster_report_20260518.json`。
- 按 paircheck predicate probe 顺序，先验证 `rhs_bare=False -> rhs_bare=False`、`lhs_lm_rm=x:x -> rhs_bare=False` 等 cluster。
- 每个候选必须做 source/target 全量模型验证和 current union increment 估算；低于 `1,000,000` 的进入 parking lot。

总控 session：

- 每当 true/false 候选合入或过滤规则改变，重新生成 residual cluster report。
- 不再让子 session 从 39 亿全空间随机挖；默认从 current unresolved residual、top buckets、feature clusters 和 registry mask 工作。
