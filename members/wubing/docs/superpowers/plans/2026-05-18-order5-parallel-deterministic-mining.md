# Order5 并行确定性策略挖掘落盘文档

日期：2026-05-18

> 注意：本文中的具体覆盖数字是 2026-05-18 快照，只用于理解当时决策背景。后续执行 true/false session、总控合并或覆盖报告前，必须重新读取 `data/processed/order5_strategy_registry/coverage_summary.json`，不要复用本文写死的旧数字。

## 一句话结论

在 2026-05-18 快照中，order5 strategy registry（策略注册表）已经把 `3,915,693,200` 个有向非自反 pair 压到 `957,323,435` 个 unresolved（未解决）pair。下一阶段应并行推进 true template mining（真命题模板挖掘）和 false predicate mining（假命题谓词挖掘），但由一个总控 session 统一合并、复核 union increment（并集新增覆盖）和 conflict（冲突）。

## 快照事实

来源：

- `data/processed/order5_strategy_registry/coverage_summary.json`
- `data/processed/order5_strategy_registry/strategies.json`
- `data/processed/order5_strategy_registry/setcheck_increment_history.jsonl`
- `data/processed/order5_paircheck_bank/merged_v1/summary.json`
- 官方 Stage 2 API 和 `SAIRcompetition/equational-theories-lean-stage2` 仓库核对结果

该快照核心指标：

| 指标 | 当前值 |
| --- | ---: |
| `total_pairs` | `3,915,693,200` |
| `deterministic_false_covered` | `2,334,245,819` |
| `deterministic_true_covered` | `624,123,946` |
| `unresolved_estimate` | `957,323,435` |
| `conflict_count` | `0` |
| false strategies | `59` |
| true strategies | `10` |
| paircheck bank registry-ready rows | `78` |

默认挖掘宇宙：

- 后续 true / false session 默认从 `coverage_summary.unresolved_estimate` 这个 current unresolved residual 继续挖；执行时必须查询最新 `coverage_summary.json`。
- `total_pairs` 只作为覆盖率分母、最终 `coverage_summary` 重算和 conflict/union 全局复核口径，也以执行时的 JSON 为准。
- 子 session 不应从 full pair space 随机枚举或抽样来生成候选；如果成本过高，应缩到 current unresolved mask、top shape bucket、paircheck/proofbank cluster 或候选 ranking。

Residual cluster（残差聚类）入口：

- 机器可读报告：`data/processed/order5_strategy_registry/residual_cluster_report_20260518.json`
- 人读分析：`docs/experiments/2026-05-18-order5-residual-cluster-analysis.md`
- 生成脚本：`scripts/data/build_order5_residual_cluster_report.py`

该报告是 true / false 子 session 的共同优先输入。它聚合 current unresolved shape buckets、cheap true filter、Fin3 selector probe、paircheck predicate probe 和 setcheck long-tail ranking，用于确定下一轮 ROI。

官方规则口径：

- Stage 2 得分边界是 Lean 4 certificate（证书）被 deterministic Lean judge 接受。
- 当前规则没有明文要求每题必须调用 LLM。
- Solo 提交仍是单文件 `solver.py`；本项目当前硬约束按官方 repo config 使用 `500000` bytes。
- 批量 official judge / Lean certificate 预检默认走 remote simple-api backend pool：`http://10.220.69.172:8888,http://10.220.69.153:8888`；172 是 32 核 primary backend，默认从 16 并发起步，确认稳定后再试 24，153 作为 fallback。

## 为什么要并行

false 侧已经靠 `false.finmodel.setcheck.*` 吃掉最大块覆盖，但最新 setcheck candidate ranking（候选排序）显示新增量进入长尾：

- 当前高候选 top increment 约 `68,462`、`62,509`、`61,350`。
- 继续无差别枚举 finite magma table（有限岩浆运算表）很难再产生亿级或千万级增量。
- paircheck bank 直接作为 explicit pair（显式 pair）只能增加几十到几万行，真正价值是反推 `predicatecheck`（谓词覆盖策略）。

true 侧仍有大块潜力：

- `true.proof.templatecheck.singleton_collapse.any_target.v1` raw coverage 为 `580,746,162`。
- `true.proof.templatecheck.singleton_seedbank_specialization.any_target.v1` raw coverage 为 `512,994,698`。
- true 策略常见形态是 `source_all_targets`，一旦新增几千个 source，就可能产生千万级到亿级覆盖。

因此下一步不是 true 或 false 二选一，而是：

1. true session 挖大块 proof template。
2. false session 把 paircheck / finite-model hits 升格为 predicatecheck。
3. 总控 session 统一验证 union、conflict 和 registry 接入。

## 总控 Session 职责

本 session 作为总控，不直接参与两个方向的细节搜索，主要负责：

1. 维护本文档和当前事实口径。
2. 分配 true / false session 的写入边界。
3. 接收候选产物，统一跑 coverage summary（覆盖汇总）、conflict check（冲突检查）和 remote judge smoke（远程官方验证器冒烟）。
4. 只把通过 gate 的候选合并进正式 registry。
5. 决定何时从 strategy registry 切换到 solver integration（求解器集成）。

总控可以读取所有方向产物，但只有总控可以修改：

- `data/processed/order5_strategy_registry/strategies.json`
- `data/processed/order5_strategy_registry/coverage_summary.json`
- `data/processed/order5_strategy_registry/setcheck_increment_history.jsonl`
- `src/math_distill_stage2/order5_strategy_registry.py`

除非用户明确要求，任何 session 都不修改：

- `submissions/solo_official/solver.py`
- `solvers/solo_official/current/solver.py`
- official runner result JSON
- 原始 data snapshot

## True Session 边界

目标：挖掘 `true.proof.templatecheck.*`，减少 unresolved 中的 true 大块候选。

优先输入：

- `data/processed/order5_strategy_registry/residual_cluster_report_20260518.json`
- `data/processed/order5_strategy_registry/current_false_unresolved_after_bank_shape_sample_50000_seed20260521.jsonl`
- `data/processed/order5_strategy_registry/current_unresolved_after_bank_top_shape_buckets_with_targeted_seed_filter_seed20260521.json`
- `data/processed/order5_strategy_registry/current_unresolved_after_bank_top3_shape_synthesis_targets_seed20260521_summary.json`
- `data/processed/proof_banks/gpt_true_certificates/`
- `src/math_distill_stage2/order5_strategy_registry.py`

优先方向：

1. `singleton_collapse` 扩展。
2. `singleton_seedbank_specialization` 的 source 条件压缩。
3. `term_shape_anchor.product` 扩展。
4. projection normalizer（投影正规化器）。
5. law instance（定律实例化）族。

输出路径建议：

```text
data/processed/order5_strategy_registry/candidates/true_template_candidates_YYYYMMDD_<label>.jsonl
data/processed/order5_strategy_registry/candidates/true_template_candidates_YYYYMMDD_<label>_summary.json
```

候选 JSONL 最少字段：

```json
{
  "schema_version": 1,
  "candidate_key": "true.proof.templatecheck.<name>",
  "verdict": true,
  "coverage_kind": "source_all_targets",
  "source_ids": [1, 2, 3],
  "target_condition": "any_target",
  "estimated_raw_coverage": 0,
  "estimated_union_increment": null,
  "proof_template": "short description",
  "representative_pairs": [[1, 2]],
  "soundness_status": "candidate"
}
```

True session 不做：

- 不改 false strategy。
- 不写正式 `strategies.json`。
- 不把 proofbank accepted pair 直接做 known-proof table。
- 不把未 remote judge accepted 的样例写成 judge 通过。

## False Session 边界

目标：挖掘 `false.finmodel.predicatecheck.*` 或高增量 `false.finmodel.setcheck.*`，优先把 paircheck bank 和 finite-model hits 升格为可泛化规则。

优先输入：

- `data/processed/order5_strategy_registry/residual_cluster_report_20260518.json`
- `data/processed/order5_paircheck_bank/merged_v1/registry_ready_bank.jsonl`
- `data/processed/order5_paircheck_bank/medium_batch_001/verified_bank.jsonl`
- `data/processed/order5_strategy_registry/predicate_bucket_probe_from_paircheck_v1.json`
- `data/processed/order5_strategy_registry/current_high_setcheck_candidate_rankings_seed20260521.jsonl`
- `data/processed/order5_strategy_registry/current_false_unresolved_after_bank_shape_buckets_50000_seed20260521.json`
- `src/math_distill_stage2/order5_setcheck_mining.py`
- `src/math_distill_stage2/order5_strategy_registry.py`

优先方向：

1. 从 paircheck bank 反推 source feature × target feature predicate。
2. 对 predicate bucket 进行全量 source/target set 验证。
3. 对每个候选计算 exact union increment，而不是 raw coverage。
4. 只保留百万级以上高价值候选；低于百万级的 setcheck 候选先进入 parking lot（暂存区）。
5. 如果单个模型在 predicate bucket 内命中稳定，再考虑登记 `false.finmodel.predicatecheck.*`。

输出路径建议：

```text
data/processed/order5_strategy_registry/candidates/false_predicate_candidates_YYYYMMDD_<label>.jsonl
data/processed/order5_strategy_registry/candidates/false_predicate_candidates_YYYYMMDD_<label>_summary.json
```

候选 JSONL 最少字段：

```json
{
  "schema_version": 1,
  "candidate_key": "false.finmodel.predicatecheck.<name>",
  "verdict": false,
  "model_table": [[0, 0], [1, 1]],
  "source_predicate": "description",
  "target_predicate": "description",
  "source_count": 0,
  "target_count": 0,
  "estimated_raw_coverage": 0,
  "estimated_union_increment": null,
  "representative_pairs": [[1, 2]],
  "python_verified": false,
  "remote_judge_smoke": null
}
```

False session 不做：

- 不改 true strategy。
- 不写正式 `strategies.json`。
- 不把 paircheck bank 行数当作新增覆盖。
- 不继续无界 Fin 3+ 或 Fin 4+ 枚举；大搜索必须先给范围和预计成本。

## 共享 Gate

候选进入正式 registry 前，必须满足：

1. `estimated_union_increment` 或 exact union increment 明确，不使用 raw coverage 冒充新增覆盖。
2. `conflict_count` 保持 `0`。
3. 对 false finite model 候选，Python 验证必须通过：source 全满足，target 全反驳。
4. 对 representative pairs，remote official judge smoke 必须使用 backend pool，记录 `base_url`、`run_id` 和 status。
5. 文档或 summary 中只在 accepted 证据存在时写 “judge 验证通过”。
6. 候选如果低于 `1,000,000` union increment，默认不合入正式 registry，除非它是后续 predicatecheck 的关键 seed。

## Session Prompt：True

把下面内容复制给新的 Codex session：

```text
请读取 docs/superpowers/plans/2026-05-18-order5-parallel-deterministic-mining.md。
请同时读取 data/processed/order5_strategy_registry/residual_cluster_report_20260518.json 和 docs/experiments/2026-05-18-order5-residual-cluster-analysis.md。

你只负责 true deterministic strategy mining，不修改 solver.py，不修改正式 registry JSON。

请优先使用 `stage2-strategy-mine-true-template`。

目标：从 order5 unresolved top shape buckets 中挖掘 true.proof.templatecheck.* 策略，优先找千万级或百万级 union increment。请优先研究 singleton_collapse、singleton_seedbank_specialization、term_shape_anchor.product、projection_normalizer、law_instance 这些方向。

输出候选到：
data/processed/order5_strategy_registry/candidates/true_template_candidates_YYYYMMDD_<label>.jsonl
以及对应 summary JSON。

每个候选必须报告：candidate_key、source 条件、target 条件、raw coverage、估算或精确 union increment、proof template 生成方式、代表 pair、soundness evidence、下一步 remote judge smoke 建议。

不要修改 false registry，不做 paircheck/setcheck，不把 proofbank accepted pair 直接做 known-proof table，不把未 judge accepted 的样例称为 judge 通过。
```

## Session Prompt：False

把下面内容复制给新的 Codex session：

```text
请读取 docs/superpowers/plans/2026-05-18-order5-parallel-deterministic-mining.md。
请同时读取 data/processed/order5_strategy_registry/residual_cluster_report_20260518.json 和 docs/experiments/2026-05-18-order5-residual-cluster-analysis.md。

你只负责 false deterministic strategy mining，不修改 solver.py，不修改正式 registry JSON。

请优先使用 `stage2-strategy-mine-false-predicate`。

目标：从 paircheck bank、finite model hits、shape buckets 中挖掘 false.finmodel.predicatecheck.* 或高增量 setcheck。优先把 paircheck bank 反推为 predicatecheck；不要继续低 ROI、无界枚举 setcheck。

输出候选到：
data/processed/order5_strategy_registry/candidates/false_predicate_candidates_YYYYMMDD_<label>.jsonl
以及对应 summary JSON。

每个候选必须报告：candidate_key、model table、source predicate、target predicate、source_count、target_count、raw coverage、精确或估算 union increment、conflict check、representative pairs、remote judge smoke 建议。

不要修改 true proofbank/template，不把 paircheck 行数当新增覆盖，不把未 judge accepted 的证据写成 accepted。
```

## 合并节奏

建议节奏：

1. True / False 两个 session 各自产出第一批候选和 summary。
2. 总控只读候选文件，先做 schema / duplicate / conflict 检查。
3. 总控按 exact union increment 排序，优先合入 `>=10,000,000` 的候选。
4. 第二优先级合入 `1,000,000` 到 `10,000,000` 且代表样例 remote judge accepted 的候选。
5. 低于 `1,000,000` 的候选进入 parking lot，作为后续聚类或 LLM prompt evidence，不立即污染 registry。

## 风险提示

- top shape bucket 中已有一部分会被 cheap true filter 吃掉；false session 必须在 true 候选之后重算 conflict 或使用总控提供的最新 true mask。
- setcheck 的 raw coverage 可能很大，但 current union increment 很小；报告必须使用 union increment。
- paircheck bank 的价值不是行数，而是能否反推出可全量验证的 predicate。
- LLM calls 应等 true / false 两侧确定性筛选后再进入，目标是更小、更高密度、更带 evidence 的 residual 集合。
