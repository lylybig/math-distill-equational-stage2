# Order5 strategy merge review queue

## 一句话结论

`postedge7` 已从待合并队列移除；下一步应从 8 个主线 register-ready 候选开始做 current baseline rescore。

## 当前 baseline

- `total_pairs`: `3915693200`
- `deterministic_false_covered`: `2383452378`
- `deterministic_true_covered`: `1376984345`
- `unresolved_estimate`: `155256477`
- `conflict_count`: `0`
- active goal sessions: `0`

## 队列计数

- `postedge7_controller_review`: `0`
- `register_ready_main`: `1`
- `needs_rescore_or_smoke_main`: `2`
- `certificate_blocked_high_roi`: `23`
- `tail_candidates`: `302`
- `parking_lot`: `999`
- `needs_metadata_review`: `828`
- `stale_or_subsumed`: `301`

## postedge7 总控复核

无。

## 主线 register-ready

| candidate | status | increment | smoke | path |
| --- | --- | ---: | --- | --- |
| false.finmodel.setcheck.affine_mod17_candidate6_sourcefirst_addon_20260526 | register_ready | `1436780` | `4/4` | `data/processed/order5_strategy_registry/candidates/false_high_fin_mod17_candidate6_sourcefirst_smoke_accepted_packet_20260526_summary.json` |

## 主线需 rescore/smoke

| candidate | status | increment | smoke | path |
| --- | --- | ---: | --- | --- |
| false.finmodel.setcheck.non_affine_all4x4_remaining_current_20260525.etp_refutation659 | needs_smoke_or_merge_review | `4909293` | `none` | `data/processed/order5_strategy_registry/candidates/false_non_affine_all4x4_remaining_current_batch_selection_full80_20260526_summary.json` |
| false.finmodel.setcheck.non_affine_all4x4_remaining_current_20260525.etp_refutation96 | needs_smoke_or_merge_review | `3646329` | `none` | `data/processed/order5_strategy_registry/candidates/false_accepted_handoff_joint_rescore_controller_audit_20260526_summary.json` |

## 高 ROI 但证书阻塞

| candidate | status | increment | smoke | path |
| --- | --- | ---: | --- | --- |
| true.proof.templatecheck.recursive_anchor.binary_grind_seedpool_20260519.any_target.v1 | certificate_blocked | `364058742` | `none` | `data/processed/order5_strategy_registry/candidates/true_template_candidates_20260519_recursive_anchor_binary_grind_summary.json` |
| false.finmodel.setcheck.affine_mod_probe.mod17.a7.b11.c0.all_equations | certificate_blocked | `4256474` | `none` | `data/processed/order5_strategy_registry/candidates/false_high_fin_mod17_current_truecheck_selection_20260525_summary.json` |
| candidate_layer_audit_only | certificate_blocked | `4256474` | `none` | `data/processed/order5_strategy_registry/candidates/false_affine_mod17_remote_artifact_access_audit_20260522_summary.json` |
| candidate_layer_false_affine_round3_lowcpu_recheck | certificate_blocked | `4256474` | `0/2` | `data/processed/order5_strategy_registry/candidates/false_controller_candidate_layer_after_postedge5_affine_round3_lowcpu_recheck_20260522_summary.json` |
| false.finmodel.setcheck.affine_mod_probe.mod17 | certificate_blocked | `4256474` | `none` | `data/processed/order5_strategy_registry/candidates/false_affine_mod17_direct_split_followup_20260522_summary.json` |
| current_residual_after_postedge6_candidate_triage_lowcpu | certificate_blocked | `4256474` | `0/2` | `data/processed/order5_strategy_registry/candidates/controller_current_residual_after_postedge6_candidate_triage_lowcpu_20260522_summary.json` |
| false.finmodel.setcheck.affine_mod_probe.mod17.a7.b11.c0.all_equations | certificate_blocked | `4256474` | `none` | `data/processed/order5_strategy_registry/candidates/false_affine_mod_round3_after_postedge5_falsemerge_mod8_23_truecheck_selection_lowcpu_recheck_20260522_summary.json` |
| false.finmodel.setcheck.affine_mod_probe.mod17.a7.b11.c0.all_equations | certificate_blocked | `4256474` | `none` | `data/processed/order5_strategy_registry/candidates/false_affine_mod_round3_after_postedge5_falsemerge_mod8_23_truecheck_selection_20260522_summary.json` |
| false.finmodel.setcheck.non_affine_all4x4_remaining_current_20260525.etp_refutation96 | certificate_blocked | `3646329` | `none` | `data/processed/order5_strategy_registry/candidates/false_accepted_handoff_joint_rescore_priority_plan_20260526_summary.json` |
| false.finmodel.setcheck.affine_mod_probe.mod17.a7.b11.c0.all_equations | certificate_blocked | `3646329` | `none` | `data/processed/order5_strategy_registry/candidates/false_accepted_handoff_joint_rescore_selection_20260526_summary.json` |

## tail candidates

| candidate | status | increment | smoke | path |
| --- | --- | ---: | --- | --- |
| false_affine_structured_after_top3_rank_20260519_summary | tail_candidate | `986598` | `none` | `data/processed/order5_strategy_registry/candidates/false_affine_structured_after_top3_rank_20260519_summary.json` |
| false_affine_structured_top30_after_order4_top2_current_rerank_20260519_summary | tail_candidate | `982772` | `none` | `data/processed/order5_strategy_registry/candidates/false_affine_structured_top30_after_order4_top2_current_rerank_20260519_summary.json` |
| true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.topbucket_probe.v1 | tail_candidate | `919560` | `none` | `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d14vc4_to_d14vc3_full_v11_20260521_summary.json` |
| true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.current_d14vc4_to_d14vc3.v1 | tail_candidate | `919560` | `50/50` | `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_current_d14vc4_to_d14vc3_full_v10_20260521_summary.json` |
| true.proof.templatecheck.opnorm.hconst_match_collapse.compiler_probe.v1 | tail_candidate | `915144` | `none` | `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_shape_top16_top13_top12_exact_combined_20260521_summary.json` |
| true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.topbucket_probe.v1 | tail_candidate | `879520` | `none` | `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_after_postedge_top60_top15_v17_20260522_summary.json` |
| true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.current_d14vc5_to_d23vc4.v1 | tail_candidate | `879520` | `50/50` | `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_latest_d14vc5_to_d23vc4_full_v12_20260522_summary.json` |
| true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.current_d14vc5_to_d14vc4.v1 | tail_candidate | `875696` | `50/50` | `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_latest_d14vc5_to_d14vc4_full_v12_20260522_summary.json` |
| true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.topbucket_probe.v1 | tail_candidate | `875696` | `none` | `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d14vc5_to_d14vc4_full_v13_20260522_summary.json` |
| true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.d14vc3_multitarget2.v1 | tail_candidate | `857440` | `100/100` | `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d14vc3_multitarget2_full_v11_20260521_summary.json` |

## 建议动作

1. `postedge7` 已被当前 registry/coverage 吸收；不要基于旧 postedge7 summary 重复合并。
2. 对主线候选只做 current profile delta rescore；不要直接相信旧 summary 的高分。
3. `affine_mod17` 只进入 certificate/smoke debug，不再扩大 false finite-model 广搜。
4. tail candidates 只在主线队列清空后批量处理，避免小增量频繁改 registry。
