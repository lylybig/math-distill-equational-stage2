# Order5 current residual cluster analysis

日期：2026-05-20

## 目标

对当前 `unresolved_estimate=258,171,947` 的 order5 residual（剩余未解决集合）做一次轻量聚类复盘，判断下一轮 deterministic strategy（确定性策略）挖掘应该继续押 true、false，还是先补 current residual sample（当前残差采样）。

本实验只汇总已有产物，不重新枚举 39 亿 pair，不修改 `solver.py`，不修改正式 strategy registry（策略注册表）。

## 输入

聚合报告：

- `data/processed/order5_strategy_registry/residual_cluster_report_20260520.json`

主要来源：

- `data/processed/order5_strategy_registry/coverage_summary.json`
- `data/processed/order5_strategy_registry/strategies.json`
- `data/processed/order5_strategy_registry/setcheck_increment_history.jsonl`
- `data/processed/order5_strategy_registry/current_residual_refresh_quick_summary_5000_seed20260519.json`
- `data/processed/order5_strategy_registry/current_residual_after_true_shape_buckets_5000_seed20260519.json`
- `data/processed/order5_strategy_registry/candidates/true_template_etp_order5_eq2_rolling_controller_summary_20260519.json`
- `data/processed/order5_strategy_registry/candidates/true_template_etp_order5_eq2_register_readiness_audit_20260520.json`
- `data/processed/order5_strategy_registry/candidates/false_predicate_model_family_size4_5_after_current_registry_exact_20260519_summary.json`
- `data/processed/order5_strategy_registry/candidates/false_affine_structured_mod17_blocked_encoding_controller_review_20260520.json`

## 方法

本报告采用三层口径：

1. 当前 coverage（覆盖）使用最新 `coverage_summary.json`，这是 `258,171,947` residual 的事实来源。
2. shape bucket（句法形状桶）使用 2026-05-19 的 quick refresh proxy。该 proxy 的 `projection_base=583,513,224`，早于 2026-05-20 大块 true import，因此只能作为优先级线索，不能当作当前 exact union increment（精确并集增量）。
3. true / false ROI（投入产出）使用最近 controller review（总控复核）和 exact tail check（精确长尾检查），避免把旧的 raw coverage（原始覆盖）当成当前增量。

## 结果

当前工作宇宙：

| 指标 | 值 |
| --- | ---: |
| `total_pairs` | `3,915,693,200` |
| `deterministic_false_covered` | `2,359,859,888` |
| `deterministic_true_covered` | `1,297,661,365` |
| `unresolved_estimate` | `258,171,947` |
| `conflict_count` | `0` |
| coverage ratio | `93.4067%` |

相对旧报告的变化：

| 对比点 | residual | delta |
| --- | ---: | ---: |
| 2026-05-18 residual report | `957,323,435` | `-699,151,488` |
| 2026-05-19 quick refresh | `583,513,224` | `-325,341,277` |
| 2026-05-20 readiness audit before import | `557,474,500` | `-299,302,553` |

2026-05-19 quick refresh 到当前的覆盖变化：

| 方向 | delta |
| --- | ---: |
| false deterministic coverage | `+25,563,766` |
| true deterministic coverage | `+299,777,511` |

这说明当前 2.58 亿 residual 已经不是 5/18 那个 true-template 大红利阶段；最近主要收益来自一大块 true source import / singleton seedbank specialization（单点源证明库特化）扩展。

## Shape Proxy

因为当前没有 2.58 亿 residual 的全新 shape sample，本报告只用 5/19 proxy 做方向判断。若把 5/19 bucket estimate 按 `258,171,947 / 583,513,224 = 0.4424` 粗缩放，top bucket 量级如下：

| 视图 | top1 | top3 | top5 | top10 | top20 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 5/19 proxy estimate | `8,599,813` | `24,206,881` | `37,584,367` | `66,585,628` | `104,795,383` |
| naive scaled current estimate | `3,804,936` | `10,710,190` | `16,628,979` | `29,453,022` | `46,363,848` |

这个缩放不是 soundness evidence（可靠性证据）。大块 true import 很可能非均匀地改变了 shape 分布，所以下一轮深挖前应该先刷新 current residual sample。

## True Lane

true 侧已吃掉的大块：

| 指标 | 值 |
| --- | ---: |
| accepted source rows | `4,627` |
| accepted source exact delta | `289,478,613` |
| current true delta since readiness audit | `299,302,553` |

剩余有希望的 true 线索：

| 候选方向 | 量级 |
| --- | ---: |
| general congruence-closure plan upper bound | `47,740,813` |
| congruence closure ge1m sequence categories | `10` |
| ge1m sequence category delta sum | `16,080,587` |

递归 anchor（锚点）方向本轮不应继续无界推进：broad binary-grind、target-variable superposition 和 top30 seedgate smoke 都是 `0 accepted`，现有 summary 结论是 `no_promotable_true_template_candidate_found_in_this_pass`。

## False Lane

false 侧最近仍有进展，但长尾已经明显：

| 指标 | 值 |
| --- | ---: |
| false coverage delta since 5/19 quick refresh | `25,563,766` |
| setcheck last 20 increment sum | `1,087,712` |
| setcheck last 20 best increment | `232,881` |
| Fin3 selector hit rate | `0.05%` |
| targeted Fin4/Fin5 top exact increment | `19` |

已合并 predicatecheck（谓词检查）top family 后，剩余同族候选被精确复核：

| candidate | after-current exact increment |
| --- | ---: |
| `e3_345__e3_1521__e3_3651__e3_425` | `59,173` |
| `e3_345__e3_1521__e3_3651__e3_425__e3_553` | `16,527` |

Mod17 structured affine setcheck 虽有 `1,061,432` exact candidate increment，但 remote judge certificate encoding（远程验证器证书编码）被证伪为不可用，状态是 `blocked_do_not_merge`。因此 false 侧下一步应该找新 predicate family，而不是继续打磨当前尾部。

## 结论

当前 ROI 排序：

1. **true congruence-closure / ETP adapter tail。** 仍可能有 `10M-50M` 量级，但前提是 proof adapter 或 compiler 能产出 representative remote judge accepted certificate。
2. **新 false predicate family。** 现有 predicate 和 setcheck 尾部偏薄；除非出现新 family，否则更像 `1M-20M`。
3. **先刷新 current residual sample。** 当前 residual 只有 `258M`，而可用 shape proxy 来自 `583M` 阶段；继续深挖前需要避免拿旧 bucket 排名当真。
4. **setcheck tail 停车场。** 无 encoding 突破或新模型类时，不适合作为主线。

## 下一步

- 新增或运行一个轻量 current-residual sampler，目标是从 `258,171,947` universe 重新产出 5k/20k shape bucket 和 true/false probe。
- true 侧优先推进 congruence-closure / ETP adapter tail，但必须以 remote judge accepted representative pair 为 gate。
- false 侧只继续新 predicate family 搜索；当前 setcheck、Fin3 selector 和已合并 model-family tail 只保留为 seed / parking lot。
- 继续保持 `solver.py` 不动；本报告只服务 strategy registry 决策。
