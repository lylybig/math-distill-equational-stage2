# Order5 strategy merge review queue

## 一句话结论

当前不建议继续广撒网挖掘；先完成 `postedge7` 总控复核，再对 register-ready 与 needs-smoke 队列做 current baseline rescore。

## 当前 baseline

- `total_pairs`: `3915693200`
- `deterministic_false_covered`: `2384904817`
- `deterministic_true_covered`: `1386445377`
- `unresolved_estimate`: `144343006`
- `conflict_count`: `0`
- active goal sessions: `0`

## 队列计数

- `postedge7_controller_review`: `2`
- `register_ready_main`: `0`
- `needs_rescore_or_smoke_main`: `17`
- `certificate_blocked_high_roi`: `29`
- `tail_candidates`: `349`
- `parking_lot`: `1480`
- `needs_metadata_review`: `1156`
- `stale_or_subsumed`: `362`

## postedge7 总控复核

| candidate | status | increment | smoke | path |
| --- | --- | ---: | --- | --- |
| current_residual_postedge7_key_collision_audit | certificate_blocked | `6246718` | `none` | `data/processed/order5_strategy_registry/candidates/false_candidate_index_ge100k_false_like_consolidated_route_audit_20260528_summary.json` |
| false.finmodel.setcheck.non_affine_all4x4_remaining_current_20260525.etp_refutation659 | certificate_blocked | `4909293` | `none` | `data/processed/order5_strategy_registry/candidates/false_high_increment_nonmerged_candidate_index_table_substrate_scan_20260527_summary.json` |

## 主线 register-ready

无。

## 主线需 rescore/smoke

| candidate | status | increment | smoke | path |
| --- | --- | ---: | --- | --- |
| true.proof.templatecheck.opnorm.hconst_combined.plus_hstep_default_sandwich_d14vc4_v17_tail | needs_smoke_or_merge_review | `7958382` | `none` | `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_plus_hstep_d14vc4_v17_tail_combined_20260527_summary.json` |
| true.proof.templatecheck.opnorm.hconst_combined.match_all_plus_default_sandwich_all | needs_smoke_or_merge_review | `7894300` | `none` | `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_combined_match_all_default_sandwich_all_20260527_summary.json` |
| true.proof.templatecheck.opnorm.hconst_combined.match_all_plus_default_sandwich_ge25 | needs_smoke_or_merge_review | `6985734` | `none` | `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_combined_match_all_default_sandwich_ge25_20260527_summary.json` |
| true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.all_components | needs_smoke_or_merge_review | `6649067` | `none` | `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_all_components_20260527_summary.json` |
| true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.ge25_tail_batch | needs_smoke_or_merge_review | `5405956` | `none` | `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_ge25_tail_batch_20260527_summary.json` |
| false.finmodel.setcheck.non_affine_all4x4_remaining_current_20260525.etp_refutation659 | needs_smoke_or_merge_review | `4909293` | `none` | `data/processed/order5_strategy_registry/candidates/false_candidate_index_high_priority_status_residual_crosswalk_20260528_summary.json` |
| false.finmodel.setcheck.non_affine_all4x4_remaining_current_20260525.etp_refutation659 | needs_smoke_or_merge_review | `4909293` | `none` | `data/processed/order5_strategy_registry/candidates/false_non_affine_all4x4_remaining_current_batch_selection_full80_20260526_summary.json` |
| true.proof.templatecheck.opnorm.hconst_combined.match_all_plus_default_sandwich_ge100k | needs_smoke_or_merge_review | `3973135` | `none` | `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_combined_match_all_default_sandwich_20260527_summary.json` |
| true.proof.templatecheck.opnorm.hconst_combined.match_ge10_plus_default_sandwich_ge100k | needs_smoke_or_merge_review | `3664651` | `none` | `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_combined_match_ge10_default_sandwich_20260527_summary.json` |
| false.accepted_packets.current_false_rescore_20260526 | needs_smoke_or_merge_review | `3652618` | `none` | `data/processed/order5_strategy_registry/candidates/false_accepted_packets_falseonly_rescore_current_closure_audit_20260527_summary.json` |

## 高 ROI 但证书阻塞

| candidate | status | increment | smoke | path |
| --- | --- | ---: | --- | --- |
| true.proof.templatecheck.recursive_anchor.binary_grind_seedpool_20260519.any_target.v1 | certificate_blocked | `364058742` | `none` | `data/processed/order5_strategy_registry/candidates/true_template_candidates_20260519_recursive_anchor_binary_grind_summary.json` |
| current_residual_postedge7_key_collision_audit | certificate_blocked | `6246718` | `none` | `data/processed/order5_strategy_registry/candidates/false_candidate_index_ge100k_false_like_consolidated_route_audit_20260528_summary.json` |
| false.finmodel.setcheck.non_affine_all4x4_remaining_current_20260525.etp_refutation659 | certificate_blocked | `4909293` | `none` | `data/processed/order5_strategy_registry/candidates/false_high_increment_nonmerged_candidate_index_table_substrate_scan_20260527_summary.json` |
| false_affine_round3_lowcpu_mod17_legacy_closure_audit_20260527_summary | certificate_blocked | `4256474` | `none` | `data/processed/order5_strategy_registry/candidates/false_affine_round3_lowcpu_mod17_legacy_closure_audit_20260527_summary.json` |
| false.finmodel.setcheck.affine_mod_probe.mod17.a7.b11.c0.all_equations | certificate_blocked | `4256474` | `none` | `data/processed/order5_strategy_registry/candidates/false_high_fin_mod17_current_truecheck_selection_20260525_summary.json` |
| candidate_layer_audit_only | certificate_blocked | `4256474` | `none` | `data/processed/order5_strategy_registry/candidates/false_affine_mod17_remote_artifact_access_audit_20260522_summary.json` |
| candidate_layer_false_affine_round3_lowcpu_recheck | certificate_blocked | `4256474` | `0/2` | `data/processed/order5_strategy_registry/candidates/false_controller_candidate_layer_after_postedge5_affine_round3_lowcpu_recheck_20260522_summary.json` |
| false.finmodel.setcheck.affine_mod_probe.mod17 | certificate_blocked | `4256474` | `none` | `data/processed/order5_strategy_registry/candidates/false_affine_mod17_direct_split_followup_20260522_summary.json` |
| current_residual_after_postedge6_candidate_triage_lowcpu | certificate_blocked | `4256474` | `0/2` | `data/processed/order5_strategy_registry/candidates/controller_current_residual_after_postedge6_candidate_triage_lowcpu_20260522_summary.json` |
| false.finmodel.setcheck.affine_mod_probe.mod17.a7.b11.c0.all_equations | certificate_blocked | `4256474` | `none` | `data/processed/order5_strategy_registry/candidates/false_affine_mod_round3_after_postedge5_falsemerge_mod8_23_truecheck_selection_lowcpu_recheck_20260522_summary.json` |

## tail candidates

| candidate | status | increment | smoke | path |
| --- | --- | ---: | --- | --- |
| false_affine_structured_after_top3_rank_20260519_summary | tail_candidate | `986598` | `none` | `data/processed/order5_strategy_registry/candidates/false_affine_structured_after_top3_rank_20260519_summary.json` |
| false_affine_structured_top30_after_order4_top2_current_rerank_20260519_summary | tail_candidate | `982772` | `none` | `data/processed/order5_strategy_registry/candidates/false_affine_structured_top30_after_order4_top2_current_rerank_20260519_summary.json` |
| true.proof.templatecheck.rollup.ready_tail.hinst_varroot_adjacent_plus_hconst_probe87_143.v1 | tail_candidate | `965087` | `131/131` | `data/processed/order5_strategy_registry/candidates/true_template_candidates_20260528_ready_tail_varroot_hconst87_143_rollup_v28_rescore_summary.json` |
| true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.topbucket_probe.v1 | tail_candidate | `919560` | `none` | `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d14vc4_to_d14vc3_full_v11_20260521_summary.json` |
| true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.current_d14vc4_to_d14vc3.v1 | tail_candidate | `919560` | `50/50` | `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_current_d14vc4_to_d14vc3_full_v10_20260521_summary.json` |
| true.proof.templatecheck.opnorm.hconst_match_collapse.compiler_probe.v1 | tail_candidate | `915144` | `none` | `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_shape_top16_top13_top12_exact_combined_20260521_summary.json` |
| false.finmodel.setcheck.non_affine_all4x4_remaining_current_20260525.etp_refutation826 | tail_candidate | `881290` | `none` | `data/processed/order5_strategy_registry/candidates/false_postcanonical_joint_after_top5_tail_plus_handoff_unseen16_greedy_rescore_20260527_summary.json` |
| false_postcanonical_joint_min1m_oldhigh_mod17_nonmod17_top5_packet_20260527_summary | tail_candidate | `880960` | `none` | `data/processed/order5_strategy_registry/candidates/false_postcanonical_joint_min1m_oldhigh_mod17_nonmod17_top5_packet_20260527_summary.json` |
| true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.topbucket_probe.v1 | tail_candidate | `879520` | `none` | `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_after_postedge_top60_top15_v17_20260522_summary.json` |
| true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.current_d14vc5_to_d23vc4.v1 | tail_candidate | `879520` | `50/50` | `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_latest_d14vc5_to_d23vc4_full_v12_20260522_summary.json` |

## 建议动作

1. 先确认 `postedge7` full summary 是否已被正式 registry/coverage 吸收。
2. 对主线候选只做 current profile delta rescore；不要直接相信旧 summary 的高分。
3. `affine_mod17` 只进入 certificate/smoke debug，不再扩大 false finite-model 广搜。
4. tail candidates 只在主线队列清空后批量处理，避免小增量频繁改 registry。
