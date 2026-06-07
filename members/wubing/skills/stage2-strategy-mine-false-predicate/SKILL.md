---
name: stage2-strategy-mine-false-predicate
description: Use when mining false deterministic Stage 2 order5 predicatecheck or high-ROI false certificate-blocked strategies from paircheck banks, finite-model hits, external solver evidence, shape buckets, affine_mod17 probes, and model feature probes, while writing candidate JSONL instead of directly modifying the registry.
---

# Stage2 Strategy Mine False Predicate

挖掘 `false.finmodel.predicatecheck.*` 策略。这个技能面向 setcheck 长尾之后的 false 侧扩展：从 paircheck bank、finite-model hits 和 shape buckets 反推 source/target predicate（谓词条件），再验证是否能形成大块 deterministic false coverage（确定性假命题覆盖）。

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
- paircheck bank：`data/processed/order5_paircheck_bank/merged_v1/registry_ready_bank.jsonl`
- paircheck probes：`data/processed/order5_strategy_registry/predicate_bucket_probe_from_paircheck_v1.json`
- false shape buckets：`data/processed/order5_strategy_registry/current_false_unresolved_after_bank_shape_buckets_50000_seed20260521.json`
- setcheck candidate ranking：`data/processed/order5_strategy_registry/current_high_setcheck_candidate_rankings_seed20260521.jsonl`
- 用户复制到当前 repo 的 external solver evidence/table bank：优先放在 `data/processed/order5_strategy_registry/candidates/`，文件名建议包含 `solver`、`countermodel`、`table_bank` 或 `proofbench_derived`
- 业务逻辑：`src/math_distill_stage2/order5_setcheck_mining.py`、`src/math_distill_stage2/order5_strategy_registry.py`

## Candidate Families

优先挖这些 false strategy：

- certificate/smoke debug for `false.finmodel.setcheck.affine_mod_probe.mod17`
- `false.finmodel.predicatecheck.<feature_family>.*`
- 从 external solver evidence/table bank 提炼出的 `false.finmodel.predicatecheck.model_family.*`
- 高增量 `false.finmodel.setcheck.*`，但只有 union increment 达到主线门槛时才继续。
- `false.finmodel.paircheck.*` 只作为 seed/evidence，不作为大覆盖主目标。

当前状态要点：

- 每轮先读 `mining_state.json` 和 `merge_review_queue.json`；不要把旧 summary 的高分当作 current baseline。
- 当前 false 侧默认不再做 broad false finite-model、random、Z3 或 endpoint 广搜；主线是修通 `affine_mod17` certificate/smoke 阻塞，或从已有 paircheck/model hits 反推高 ROI predicate。
- 用户提供的 Z3/Mace4/PySAT/Vampire/Prover9 产物只算 bounded evidence；它们不是 broad search 授权，也不是最终裁判。proof trace、quant-inst 或 fake-target lemma 应路由到 `stage2-strategy-mine-true-template`。
- 新 false candidate 若没有可能达到 `>=100_000` exact current union increment，默认只记录 negative evidence 或 parking lot，不继续扩跑。
- remote smoke 小批代表样例优先低并发，记录 input、results、summary；Python 验证或抽样结果不能写成 judge accepted。

## Working Universe

默认挖掘目标是 current unresolved residual 中的 false 新增覆盖；执行前先读取 `data/processed/order5_strategy_registry/coverage_summary.json`，以最新 `coverage_summary.unresolved_estimate` 为当前残差规模，不在技能中保存旧覆盖数字。canonical summary 覆盖全 order5 directed non-self pair space，必须包含 `order4_source_to_order4_target`。快速查询：

```bash
jq '{coverage_scope, includes_order4_source_to_order4_target, source_target_excluded_block_count, total_pairs, deterministic_false_covered, deterministic_true_covered, unresolved_estimate, conflict_count}' \
  data/processed/order5_strategy_registry/coverage_summary.json
```

- 优先用 residual cluster report、paircheck bank、finite-model hits、`current_*unresolved*` 样本、false unresolved shape bucket 和当前 registry mask 反推 predicate。
- `total_pairs` 只用于分母、最终 summary 和 conflict/union 全量复核；不要从 full pair space 随机抽样来挖 predicate。
- 如果 predicate 验证成本高，先做 source/target feature 分层、bucket-level 验证和 mask increment 估算，再把高价值候选落盘。

## External Solver Evidence

当用户提供 proofbench-derived、Z3、Mace4、PySAT/Kissat/CaDiCaL、Vampire 或 Prover9 线索时，只在当前 repo 内消费已复制/已提供的 artifact；不要修改外部 repo，也不要把外部 solver 的 `sat`、`unsat`、`proved`、`model found` 写成 solved 或 judge accepted。

false 侧优先提取 finite magma table。Prover9/Vampire/E/CVC5 的 proof、unsat 或 quant-inst 信号应转 `stage2-strategy-mine-true-template` 做 true-template evidence；只有能导出 countermodel/table 时才进入 false candidate 主流水线。

标准流水线：

```text
solver evidence -> table normalize/dedup -> source/target full setcheck
-> current union increment -> true-overlap/conflict gate
-> representative pairs -> remote Lean judge smoke -> candidate JSONL/summary
```

建议 evidence JSONL 字段：

- `schema_version`
- `evidence_source`
- `solver`
- `solver_role`：`finite_model_search` 或 `countermodel_search`
- `source_artifact`
- `seed_pair`
- `model_table`
- `model_table_sha256`
- `canonicalization`
- `solver_command_hash` 或 `stdout_sha256`
- `solver_status`
- `python_verified`

如果 evidence 只能给 pair-level counterexample，不要直接作为大覆盖策略；先作为 seed，尝试反推 source/target predicate 或 model family，再按 current union increment 过门。如果 evidence 是 proof trace、quant-inst、`unsat` proof signal 或 fake-target lemma，停止 false mining 分支并转 true-template。

## Coverage Reporting Requirement

每个候选必须同时报告当前 residual 搜索口径和全局计分口径：

- `estimated_raw_coverage` 或 `raw_coverage`：基于 `coverage_summary.total_pairs` 全空间/全局分母的覆盖口径。
- `estimated_union_increment` 或 `exact_union_increment`：结合当前 `strategies.json` / `coverage_summary.json` 后的新增解决量。
- `after_merge_projection`：如果候选合入，`deterministic_false_covered`、总 deterministic covered 和 `unresolved_estimate` 会变成多少。
- 不允许只报告 residual sample hit rate、false_uncovered_pair_capacity、paircheck hit count 或 model hit rate；这些只能作为候选发现信号，不能替代 union increment。

## ROI Gate

- 主线候选默认要求 `exact_union_increment >= 1_000_000`。
- 如果连续两轮没有百万级候选，或候选明显进入长尾，可以切到 `100_000 <= exact_union_increment < 1_000_000` 的 tail 模式。
- tail 模式只保留 soundness 清楚、实现成本低、judge smoke 路径稳定的候选；优先按同一 predicate/model family batch，使单轮累计新增覆盖尽量达到 `1_000_000`。
- `exact_union_increment < 100_000` 的候选默认进入 parking lot，不合并；只有作为更大 false family 的必要 seed，或能解释重要 residual bucket 时才继续追踪。
- 无论主线还是 tail，新增覆盖都必须以 current registry 的 union increment 为准，不能用 raw coverage 或 sample hit rate 代替。

## Workflow

1. 从 paircheck bank 或 finite-model hits 里找共同 source feature × target feature × model table 组合。
2. 如果输入来自 external solver evidence，先规范化表、去重并记录 provenance；不能从 solver 输出直接跳到 judge accepted。
3. 对候选 predicate 做全量 source/target set 验证：source 全满足模型，target 全被模型反驳。
4. 计算 raw coverage 和 current union increment；新增覆盖必须以 union increment 为准。
5. 按 ROI Gate 决定主线、tail 或 parking lot；低于当前模式门槛的候选只落盘为候选证据，不直接进入合并。
6. 生成 representative pairs，优先覆盖 order4 source -> order4 target、order4 source -> order5 target、order5 source -> order4 target、order5 source -> order5 target。
7. remote judge smoke 只做代表样例，必须走 `remote-http`/`remote-judge-v2` 到 `http://10.220.69.172:8890`；certificate-blocked 候选先把失败原因、Lean code、官方 judge 输出和下一步编码方案落盘。
8. 候选落盘到：

```text
data/processed/order5_strategy_registry/candidates/false_predicate_candidates_YYYYMMDD_<label>.jsonl
data/processed/order5_strategy_registry/candidates/false_predicate_candidates_YYYYMMDD_<label>_summary.json
```

候选行至少包含：

- `schema_version`
- `candidate_key`
- `verdict=false`
- `model_table`
- `source_predicate`
- `target_predicate`
- `evidence_source` / `solver` / `source_artifact`（如果来自 external solver evidence）
- `model_table_sha256`
- `source_count`
- `target_count`
- `estimated_raw_coverage`
- `estimated_union_increment`
- `after_merge_projection`
- `representative_pairs`
- `python_verified`
- `remote_judge_smoke`

## Hard Constraints

- Do not edit `solver.py`；不 promote，不同步到 `submissions/solo_official/`。
- 不直接修改 `strategies.json`、`coverage_summary.json`、`setcheck_increment_history.jsonl` 或 `order5_strategy_registry.py`；正式合并由总控 session 做。
- 不修改 `mining_state.json`、`candidate_index*.json` 或 `merge_review_queue.json`；这些由总控刷新。
- 不修改 true strategy、proofbank 或 true template candidates。
- 不把 paircheck bank 行数当作新增覆盖；paircheck 的价值是反推 predicate。
- 不修改外部 repo；只消费用户复制或当前 repo 已存在的 external solver artifacts。
- 不把 Z3/Mace4/PySAT/Vampire/Prover9 输出当成最终裁判；只有 official judge accepted 才能写成 judge smoke 通过。
- 不运行无界 Fin 3+ / Fin 4+ / Fin 5+ 搜索；长搜索必须先报告范围和预计成本。
- 不把 Python 验证、抽样或候选排名说成 judge 验证；只有 official judge accepted 才能写成 judge smoke 通过。
- 不使用本地 Docker/Lean 做批量 certificate 预检；需要 judge smoke 时走 remote backend。

## Report Back

报告 candidate file、summary file、predicate、model table、source/target 数量、raw coverage、union increment、conflict 风险、representative pairs、remote judge smoke 状态，以及下一步由总控执行的最小复核动作。
