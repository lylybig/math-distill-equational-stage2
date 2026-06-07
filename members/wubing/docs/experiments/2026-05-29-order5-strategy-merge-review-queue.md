# Order5 strategy merge review queue

## 一句话结论

`postedge7` 已从待合并队列移除；当前没有 register-ready 或 needs-rescore/smoke 主线候选。

## 当前 baseline

- `total_pairs`: `3915693200`
- `deterministic_false_covered`: `2387093988`
- `deterministic_true_covered`: `1394597946`
- `unresolved_estimate`: `134001266`
- `conflict_count`: `0`
- active goal sessions: `0`

## 队列计数

- `postedge7_controller_review`: `0`
- `register_ready_main`: `0`
- `needs_rescore_or_smoke_main`: `0`
- `certificate_blocked_high_roi`: `0`
- `tail_candidates`: `310`
- `parking_lot`: `1493`
- `needs_metadata_review`: `1283`
- `stale_or_subsumed`: `503`

## postedge7 总控复核

无。

## 主线 register-ready

无。

## 主线需 rescore/smoke

无。

## 高 ROI 但证书阻塞

无。

## tail candidates

| candidate | status | increment | smoke | path |
| --- | --- | ---: | --- | --- |
| false.accepted_packets.nonmod17_tail.trueclean_worklist.current_graph_pack_20260529 | tail_candidate | `891916` | `91/91` | `data/processed/order5_strategy_registry/candidates/controller_false_nonmod17_tail_worklist_current_graph_pack_20260529_summary.json` |
| true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.topbucket_probe.v1 | tail_candidate | `567220` | `none` | `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge_top09_v16_20260522_summary.json` |
| true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.round28_top01_02_combined_tail.v1 | tail_candidate | `514848` | `none` | `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_round28_all_combined_tail_candidates_20260522_summary.json` |
| true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.topbucket_probe.v1 | tail_candidate | `506680` | `none` | `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_after_postedge_top60_top29_v17_20260522_summary.json` |
| true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.current_d14vc5_to_d13vc3.v1 | tail_candidate | `506680` | `50/50` | `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_latest_d14vc5_to_d13vc3_full_v12_20260522_summary.json` |
| true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.round28_top28_31_combined_tail.v1 | tail_candidate | `502194` | `100/100` | `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_round28_top28_31_combined_tail_20260522_summary.json` |
| true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.topbucket_probe.v1 | tail_candidate | `498944` | `none` | `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_after_postedge_top60_top60_v17_20260522_summary.json` |
| true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.topbucket_probe.v1 | tail_candidate | `493296` | `none` | `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_after_postedge_top60_top33_v17_20260522_summary.json` |
| true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.current_d14vc5_to_d23vc3.v1 | tail_candidate | `493296` | `50/50` | `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_latest_d14vc5_to_d23vc3_full_v12_20260522_summary.json` |
| true.proof.templatecheck.opnorm.hconst_match_collapse.goal_probe112_143_combined_tail_batch.v1 | tail_candidate | `481616` | `64/64` | `data/processed/order5_strategy_registry/candidates/true_template_candidates_20260528_hconst_probe112_143_combined_tail_v28_rescore_summary.json` |

## 建议动作

1. 主线 merge queue 已清空；下一步只处理 certificate-blocked、metadata review 或 tail batch，不直接合并 registry。
2. 对主线候选只做 current profile delta rescore；不要直接相信旧 summary 的高分。
3. `affine_mod17` 只进入 certificate/smoke debug，不再扩大 false finite-model 广搜。
4. tail candidates 只在主线队列清空后批量处理，避免小增量频繁改 registry。
