# Order5 strategy merge review queue

## 一句话结论

`postedge7` 已从待合并队列移除；当前没有 register-ready 或 needs-rescore/smoke 主线候选。

## 2026-05-22 总控追加复核

- 旧 `register_ready_main` 6 个 v9/v10 候选用 v26 current profile 重算后全部当前增量为 `0`、冲突为 `0`。
- `d14vc5_post_topbucket_multitarget20`、`d14vc5_multitarget11`、`d14vc4_multitarget8` 三组历史主线候选用 v26 current profile 复核后当前增量均为 `0`，分别吸收 8、7、6 个同族子候选。
- `top16_top13_top12_top08` shape-batch pair-index cache 用 v26 exact delta 复核：raw `1251792`，same-true overlap `1251792`，当前增量 `0`、冲突 `0`。
- legacy hconst mainline wrapper 与 `lmrm` mainline 用 v25/v26 复核后均已归入 stale/subsumed；`postedge2_top60_extension.current_v26_rescore` 自身也标记 `closed_fresh_subsumed`，不是新可合并增量。
- 当前主线队列已清到 `register_ready_main=0`、`needs_rescore_or_smoke_main=0`；剩余高 ROI 项都是证书/seedgate/smoke 阻塞或 metadata review，不建议合并。

## 当前 canonical baseline

2026-05-26 复查更新：正式 baseline 改为全 order5 directed non-self pair space，包含 `order4_source_to_order4_target`；下面队列叙述仍是 2026-05-22 历史快照。

- `total_pairs`: `3915693200`
- `deterministic_false_covered`: `2383452378`
- `deterministic_true_covered`: `1376984345`
- `unresolved_estimate`: `155256477`
- `conflict_count`: `0`
- active goal sessions: `0`

## 队列计数

- `postedge7_controller_review`: `0`
- `register_ready_main`: `0`
- `needs_rescore_or_smoke_main`: `0`
- `certificate_blocked_high_roi`: `12`
- `tail_candidates`: `232`
- `parking_lot`: `636`
- `needs_metadata_review`: `621`
- `stale_or_subsumed`: `166`

## postedge7 总控复核

无。

## 主线 register-ready

无。

## 主线需 rescore/smoke

无。

## 高 ROI 但证书阻塞

### 总控阻塞复核

- `recursive_anchor.binary_grind_seedpool` 的 `364058742` 是 seedpool/finite-model prioritization signal，不是可合并 deterministic registry 证书；下一步只能走 targeted proofbank seedgate。
- `affine_mod17` 系列当前最高 `4256474`，true-overlap/current increment gate 曾通过，但 order5-source representative remote smoke 仍失败或不完整：direct_split 只通过 easy order4-source tier，关键 order5-source tier `0/1` rejected，lowcpu recheck `0/2`。
- `false_controller_to_date_after_postedge2_register_merge_audit` 是 audit wrapper：它写明 no additional register append，唯一 eligible smoke package 已注册，剩余项低于 gate 或受 mod17 阻塞影响。
- raw selection/rank summary 只保留为证据，不作为独立 register candidate。
- 总控 artifact：`data/processed/order5_strategy_registry/candidates/controller_certificate_blocked_high_roi_triage_20260522_summary.json`。
- recursive-anchor 追加 proofbank audit：top100 seed 中 `92` 个已有 accepted proofbank evidence，`8` 个已尝试未 accepted；accepted 92-source all-target rule 在 v26 下 raw `5756900`，same-true overlap `5756900`，当前增量 `0`、冲突 `0`。artifact：`data/processed/order5_strategy_registry/candidates/controller_recursive_anchor_proofbank_top100_v26_audit_20260522_summary.json`。

| candidate | status | increment | smoke | path |
| --- | --- | ---: | --- | --- |
| true.proof.templatecheck.recursive_anchor.binary_grind_seedpool_20260519.any_target.v1 | certificate_blocked | `364058742` | `none` | `data/processed/order5_strategy_registry/candidates/true_template_candidates_20260519_recursive_anchor_binary_grind_summary.json` |
| candidate_layer_audit_only | certificate_blocked | `4256474` | `none` | `data/processed/order5_strategy_registry/candidates/false_affine_mod17_remote_artifact_access_audit_20260522_summary.json` |
| candidate_layer_false_affine_round3_lowcpu_recheck | certificate_blocked | `4256474` | `0/2` | `data/processed/order5_strategy_registry/candidates/false_controller_candidate_layer_after_postedge5_affine_round3_lowcpu_recheck_20260522_summary.json` |
| false.finmodel.setcheck.affine_mod_probe.mod17 | certificate_blocked | `4256474` | `none` | `data/processed/order5_strategy_registry/candidates/false_affine_mod17_direct_split_followup_20260522_summary.json` |
| current_residual_after_postedge6_candidate_triage_lowcpu | certificate_blocked | `4256474` | `0/2` | `data/processed/order5_strategy_registry/candidates/controller_current_residual_after_postedge6_candidate_triage_lowcpu_20260522_summary.json` |
| false.finmodel.setcheck.affine_mod_probe.mod17.a7.b11.c0.all_equations | certificate_blocked | `4256474` | `none` | `data/processed/order5_strategy_registry/candidates/false_affine_mod_round3_after_postedge5_falsemerge_mod8_23_truecheck_selection_lowcpu_recheck_20260522_summary.json` |
| false.finmodel.setcheck.affine_mod_probe.mod17.a7.b11.c0.all_equations | certificate_blocked | `4256474` | `none` | `data/processed/order5_strategy_registry/candidates/false_affine_mod_round3_after_postedge5_falsemerge_mod8_23_truecheck_selection_20260522_summary.json` |
| false.finmodel.predicatecheck.model_family.beam_after_k40.etp_refutation492__etp_refutation496__etp_refutation493.source_any_target_all_refuted | certificate_blocked | `3071381` | `8/23` | `data/processed/order5_strategy_registry/candidates/false_controller_to_date_after_postedge2_register_merge_audit_20260522_summary.json` |
| false_affine_mod17_register_gate_audit | certificate_blocked | `3071381` | `8/23` | `data/processed/order5_strategy_registry/candidates/false_affine_mod17_register_gate_audit_20260522_summary.json` |
| false.finmodel.setcheck.affine_mod_probe.mod17.a7.b11.c0.all_equations | certificate_blocked | `3071381` | `none` | `data/processed/order5_strategy_registry/candidates/false_affine_mod_after_false_post_frontier_z3_merge_mod12_19_truecheck_selection_20260522_summary.json` |

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

1. 主线 merge queue 已清空；下一步只处理 certificate-blocked、metadata review 或 tail batch，不直接合并 registry。
2. 对主线候选只做 current profile delta rescore；不要直接相信旧 summary 的高分。
3. `affine_mod17` 只进入 certificate/smoke debug，不再扩大 false finite-model 广搜。
4. tail candidates 只在主线队列清空后批量处理，避免小增量频繁改 registry。
