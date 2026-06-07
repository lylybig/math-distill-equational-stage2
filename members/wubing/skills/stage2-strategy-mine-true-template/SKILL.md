---
name: stage2-strategy-mine-true-template
description: Use when mining true deterministic Stage 2 order5 proof-template strategies, including opnorm/hconst match-collapse, singleton/product/projection/law-instance template coverage, external solver proof evidence, top unresolved shape buckets, proofbank strategy-gate evidence, candidate JSONL output, and union-increment estimates before controller registry integration.
---

# Stage2 Strategy Mine True Template

挖掘 `true.proof.templatecheck.*` 策略。这个技能只负责 true deterministic strategy candidate（真命题确定性策略候选）的发现、验证思路和候选落盘；不修改 `solver.py`，不直接写正式 registry。

## Working Directory

All relative paths in this skill are relative to `members/wubing/`. If the shell
is at the team monorepo root, run `cd members/wubing` or set the command
`workdir` there before executing the commands below.

## Inputs

优先读取：

- 当前协同文档：`docs/superpowers/plans/2026-05-22-order5-mining-session-coordination.md`
- residual cluster report：`data/processed/order5_strategy_registry/residual_cluster_report_20260518.json`
- residual cluster analysis：`docs/experiments/2026-05-18-order5-residual-cluster-analysis.md`
- 当前 summary：`data/processed/order5_strategy_registry/coverage_summary.json`
- 当前 registry：`data/processed/order5_strategy_registry/strategies.json`
- mining state：`data/processed/order5_strategy_registry/mining_state.json`
- merge queue：`data/processed/order5_strategy_registry/merge_review_queue.json`
- top shape buckets：`data/processed/order5_strategy_registry/current_unresolved_after_bank_top_shape_buckets_with_targeted_seed_filter_seed20260521.json`
- top3 synthesis targets：`data/processed/order5_strategy_registry/current_unresolved_after_bank_top3_shape_synthesis_targets_seed20260521_summary.json`
- proof bank：`data/processed/proof_banks/gpt_true_certificates/`
- 用户复制到当前 repo 的 external solver proof evidence：优先放在 `data/processed/order5_strategy_registry/candidates/`，文件名建议包含 `solver`、`proof_trace`、`quant_inst`、`prover9`、`vampire`、`cvc5`、`eprover` 或 `proofbench_derived`
- 业务逻辑：`src/math_distill_stage2/order5_strategy_registry.py`

## Candidate Families

优先挖这些 true template：

- `true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.*`
- `true.proof.templatecheck.opnorm.hconst_match_collapse.*`
- `true.proof.templatecheck.singleton_collapse.*`
- `true.proof.templatecheck.singleton_seedbank_specialization.*`
- `true.proof.templatecheck.term_shape_anchor.product.*`
- `true.proof.templatecheck.projection_normalizer.*`
- `true.proof.templatecheck.law_instance.*`
- `true.proof.templatecheck.evidence_guided.hinst_grind.*`
- `true.proof.templatecheck.evidence_guided.local_lemma.*`
- `true.proof.templatecheck.evidence_guided.calc_transfer.*`

不要把 proofbank accepted pair 直接扩成 pair-level known-proof table。目标是抽象出可系统生成 certificate 的 source/target 条件。

当前状态要点：

- 每轮先读 `mining_state.json` 和 `merge_review_queue.json`；不要重复处理已经被正式 registry 吸收的 candidate，例如已吸收的 `postedge7`。
- 主线优先从 `opnorm.hconst_default_sandwich_match_collapse` 的 frontier/top bucket/target extension 找 batch，而不是重新 broad search。
- `recursive_anchor.binary_grind_seedpool_20260519` 这类高 ROI 但 certificate-blocked 候选，需要先补 proof compiler、proofbank strategy-gate evidence 或 remote smoke 证据；不要仅凭旧 summary 进入 registry 合并。
- 如果输入包含 Z3/CVC5 quant-inst、Prover9/Ivy、Vampire/E proof trace 或 proofbench-derived true pattern，先按本技能的 External Proof Evidence 流程把 solver 信号转成 candidate template；不要把 solver status 直接写成 solved。

## Working Universe

默认挖掘目标是 current unresolved residual 里的 true 大块；执行前先读取 `data/processed/order5_strategy_registry/coverage_summary.json`，以最新 `coverage_summary.unresolved_estimate` 为当前残差规模，不在技能中保存旧覆盖数字。canonical summary 覆盖全 order5 directed non-self pair space，必须包含 `order4_source_to_order4_target`。快速查询：

```bash
jq '{coverage_scope, includes_order4_source_to_order4_target, source_target_excluded_block_count, total_pairs, deterministic_false_covered, deterministic_true_covered, unresolved_estimate, conflict_count}' \
  data/processed/order5_strategy_registry/coverage_summary.json
```

- 优先从 residual cluster report、`current_*unresolved*` 样本、top unresolved shape bucket、proofbank cluster 和当前 registry mask 中找 source/target 条件。
- `total_pairs` 只用于估算分母、最终 summary 和 conflict/union 复核；不要从 full pair space 随机抽样生成 true template。
- 如果 proof template 搜索成本高，先缩到 top bucket、source family 或 proof body cluster，再输出候选给总控计算 union increment。

## External Proof Evidence

当用户提供 proofbench-derived、Z3、CVC5、Prover9/Ivy、Vampire 或 E prover 线索时，先把 artifact 分类成 `proof_trace`、`quant_inst`、`fake_target_lemma` 或 `countermodel_trace`：

- `proof_trace`、`quant_inst`、`fake_target_lemma` 只进入 true-template mining。提取的是可泛化 source/target 条件、局部 lemma 和 Lean certificate surface。
- `countermodel_trace` 不证明 true；如果有 finite table，路由到 `stage2-strategy-mine-setcheck` 或 `stage2-strategy-mine-false-predicate`。
- 外部 solver 的 `unsat`、`proved`、`counter-sat` 或 `model found` 都只是 evidence；最终仍需要 representative remote Lean judge smoke。

优先把 evidence-guided true 候选压缩成这些 certificate surface：

- `hinst_grind`：显式 `have h_i := h ...` 加 `grind`。
- `local_lemma`：先证明 left-zero、projection、square constancy、all-products-equal 等强局部 lemma，再证明目标。
- `calc_transfer`：把 Prover9/Ivy、Vampire 或 E 的等式步骤翻译成 `.symm`、`.trans`、`congrArg` 和显式 `calc`。

## Coverage Reporting Requirement

每个候选必须同时报告当前 residual 搜索口径和全局计分口径：

- `estimated_raw_coverage` 或 `raw_coverage`：基于 `coverage_summary.total_pairs` 全空间/全局分母的覆盖口径。
- `estimated_union_increment` 或 `exact_union_increment`：结合当前 `strategies.json` / `coverage_summary.json` 后的新增解决量。
- `after_merge_projection`：如果候选合入，`deterministic_true_covered`、总 deterministic covered 和 `unresolved_estimate` 会变成多少。
- 不允许只报告 residual sample hit rate、top bucket sample count 或 proofbank cluster 命中率；这些只能作为候选发现信号，不能替代 union increment。

## ROI Gate

- 主线候选默认要求 `exact_union_increment >= 1_000_000`。
- 如果连续两轮没有百万级候选，或 true template 挖掘明显进入长尾，可以切到 `100_000 <= exact_union_increment < 1_000_000` 的 tail 模式。
- tail 模式只保留 proof template 简单、certificate compiler 稳定、soundness 清楚、remote judge smoke 路径明确的候选。
- tail 模式优先按同一 proof family batch，使单轮累计新增覆盖尽量达到 `1_000_000`；不要把零散 proofbank accepted pair 当作 pair-level known-proof table 合并。
- `exact_union_increment < 100_000` 的候选默认进入 parking lot，不合并；只有作为更大 proof compiler/template family 的必要 seed 时继续追踪。
- 无论主线还是 tail，新增覆盖都必须以 current registry 的 union increment 为准，不能用 raw coverage、proofbank 命中数或 sample hit rate 代替。

## Workflow

1. 先说明候选属于哪个 true template family，以及它试图覆盖哪些 source/target 条件。
2. 从 unresolved top shape bucket、proofbank accepted cluster 或 external proof evidence 中取样，找共同 source feature、target feature、局部 lemma 和 proof body 形态。
3. 如果来自 external proof evidence，先记录 `evidence_source`、`solver`、`proof_signal_kind`、`source_artifact` 和候选 `lean_certificate_surface`；不要从 solver 输出直接跳到 judge accepted。
4. 估算 raw coverage，并尽量使用当前 registry mask 或总控提供的脚本计算 union increment；不能把 raw coverage 写成新增覆盖，并按 ROI Gate 标记主线、tail 或 parking lot。
5. 生成代表性 pair：至少包含 order4 source -> order4 target、order4 source -> order5 target、order5 source -> order4 target、order5 source -> order5 target 中适用的类别。
6. 如需 remote judge smoke，只生成代表输入或小批建议；默认不在 true mining 子 session 里大规模跑 judge。smoke 结果必须写清楚是 official judge accepted、失败还是未运行。
7. 候选落盘到：

```text
data/processed/order5_strategy_registry/candidates/true_template_candidates_YYYYMMDD_<label>.jsonl
data/processed/order5_strategy_registry/candidates/true_template_candidates_YYYYMMDD_<label>_summary.json
```

候选行至少包含：

- `schema_version`
- `candidate_key`
- `verdict=true`
- `coverage_kind`
- `source_ids` 或 `source_predicate`
- `target_condition`
- `estimated_raw_coverage`
- `estimated_union_increment`
- `after_merge_projection`
- `proof_template`
- `evidence_source` / `solver` / `proof_signal_kind` / `source_artifact`（如果来自 external proof evidence）
- `template_generalization_rule`
- `lean_certificate_surface`
- `local_precheck_status`
- `representative_pairs`
- `soundness_status`
- `remote_judge_smoke`

## Hard Constraints

- Do not edit `solver.py`；不 promote，不同步到 `submissions/solo_official/`。
- 不直接修改 `strategies.json`、`coverage_summary.json`、`setcheck_increment_history.jsonl` 或 `order5_strategy_registry.py`；正式合并由总控 session 做。
- 不修改 `mining_state.json`、`candidate_index*.json` 或 `merge_review_queue.json`；这些由总控刷新。
- 不修改 false strategy、paircheck bank 或 setcheck bank。
- 不把 proofbank accepted pair 当作 known-proof table。
- 不修改外部 repo；只消费用户复制或当前 repo 已存在的 external solver proof artifacts。
- 不把 Z3/CVC5/Prover9/Vampire/E 的 solver status 当作最终裁判；只有 remote official Lean judge accepted 才能写成 judge smoke 通过。
- 不把抽样成功或未 judge 的证书说成 judge accepted。
- 不使用本地 Docker/Lean 做批量 certificate 预检；需要 judge smoke 时走 remote backend。

## Report Back

报告 candidate file、summary file、候选 family、source/target 条件、raw coverage、union increment 口径、代表 pair、proof template 证据、冲突风险，以及下一步由总控执行的最小复核动作。
