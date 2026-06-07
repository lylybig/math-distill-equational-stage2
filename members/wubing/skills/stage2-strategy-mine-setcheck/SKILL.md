---
name: stage2-strategy-mine-setcheck
description: Use when systematically mining finite-model setcheck strategies for the Stage 2 strategy registry, including enumerating finite magma tables, importing external solver table banks, ranking current union coverage increment, validating source/target sets, debugging certificate-blocked setcheck families, writing candidates, and preparing controller-reviewed judge-smoked registry updates.
---

# Stage2 Strategy Mine Setcheck

系统挖掘 `false.finmodel.setcheck.*` 策略。这个技能是 `stage2-strategy-explore` 的窄化工作流：重点是高效枚举有限模型、按当前 registry 的 union 增量排序，并把高价值候选转成可验证 registry 策略。

## Working Directory

All relative paths in this skill are relative to `members/wubing/`. If the shell
is at the team monorepo root, run `cd members/wubing` or set the command
`workdir` there before executing the commands below.

## Inputs

优先使用：

- 当前 registry：`src/math_distill_stage2/order5_strategy_registry.py`
- 当前 summary：`data/processed/order5_strategy_registry/coverage_summary.json`
- mining state：`data/processed/order5_strategy_registry/mining_state.json`
- merge queue：`data/processed/order5_strategy_registry/merge_review_queue.json`
- setcheck 增量历史：`data/processed/order5_strategy_registry/setcheck_increment_history.jsonl`
- 方程文件：`external/equational-theories-lean-stage2/examples/problems/eq_size5.txt`
- 有限模型工具：`FiniteMagma`、`enumerate_magmas`、`parse_equation`
- 覆盖工具：`SourceTargetSetsRule`、`_union_count_for_rules`、`DEFAULT_ORDER4_MAX_ID`
- 快速候选排名脚本：`scripts/data/rank_order5_setcheck_candidates.py`
- 快速候选排名模块：`src/math_distill_stage2/order5_setcheck_mining.py`
- 用户复制到当前 repo 的 external solver table bank / countermodel evidence：优先放在 `data/processed/order5_strategy_registry/candidates/`，文件名建议包含 `solver`、`countermodel`、`table_bank` 或 `proofbench_derived`

## Working Universe

默认挖掘目标是 current unresolved residual 中的 false 新增覆盖；执行前先读取 `data/processed/order5_strategy_registry/coverage_summary.json`，以最新 `coverage_summary.unresolved_estimate` 为当前残差规模，不在技能中保存旧覆盖数字。canonical summary 覆盖全 order5 directed non-self pair space，必须包含 `order4_source_to_order4_target`。快速查询：

```bash
jq '{coverage_scope, includes_order4_source_to_order4_target, source_target_excluded_block_count, total_pairs, deterministic_false_covered, deterministic_true_covered, unresolved_estimate, conflict_count}' \
  data/processed/order5_strategy_registry/coverage_summary.json
```

- 候选模型可以来自有限运算表枚举、seeded table 或外部 model bank，但 pair 覆盖评估必须使用当前 registry mask 和 current union increment。
- 外部 solver 产物只能作为 finite table/countermodel 来源；Z3/Mace4/PySAT/Kissat/CaDiCaL/Vampire/Prover9 的输出不是最终裁判，不能写成 judge accepted。proof trace、quant-inst 或 fake-target lemma 应路由到 `stage2-strategy-mine-true-template`，不要塞进 setcheck。
- `total_pairs` 只用于最终 coverage summary、分母和 conflict/union 全量复核；不要从 full pair space 随机扫描来找 setcheck 候选。
- 如果 Fin 3+ 搜索成本高，缩小到 current unresolved mask、top false unresolved shape bucket 或已有 candidate ranking；不要因全空间成本过高而停止。
- 当前 false 侧默认不再 broad random/Z3/endpoint 广搜；除非用户明确授权，优先处理已有 `merge_review_queue` 中的 certificate-blocked high ROI setcheck，例如 `affine_mod17`，或对已知 candidate ranking 做 current rescore。

## External Table Bank Mode

当输入来自 Z3 finite model、Mace4、PySAT/Kissat/CaDiCaL、Vampire FMB/countermodel、Prover9/Mace4 companion countermodel 或 proofbench-derived finite-table artifact 时，本技能只消费当前 repo 内已经存在或用户复制进来的文件；不要修改外部 repo。

稳定流水线：

```text
external solver evidence -> finite magma table extraction
-> table validation/canonical fingerprint -> deduped candidate file
-> rank_order5_setcheck_candidates.py current rescore
-> ROI gate -> representative remote Lean smoke
-> candidates JSONL/summary for controller review
```

table bank 行建议至少包含：

- `schema_version`
- `evidence_source`
- `solver`
- `solver_role`：`finite_model_search` 或 `countermodel_search`
- `source_artifact`
- `seed_pair`
- `model_table`
- `model_table_sha256`
- `canonicalization`
- `solver_status`

如果 artifact 只包含 pair-level result 而没有 finite table，先把它交给 `stage2-strategy-mine-false-predicate` 当 seed；不要直接尝试登记 setcheck strategy。如果 artifact 是 proof trace、quant-inst、`unsat` proof signal 或 fake-target lemma，路由到 `stage2-strategy-mine-true-template`。

## ROI Gate

- 主线候选默认要求 `exact_union_increment >= 1_000_000`。
- 如果连续两轮没有百万级候选，或当前 finite-model setcheck 明显进入长尾，可以切到 `100_000 <= exact_union_increment < 1_000_000` 的 tail 模式。
- tail 模式只合并 soundness 清楚、模型表稳定、certificate helper 现有能力可覆盖、judge smoke 路径稳定的候选。
- tail 模式优先按同一模型来源或同一 family batch，使单轮累计新增覆盖尽量达到 `1_000_000`；避免为了很小的单表增量频繁修改 registry。
- `exact_union_increment < 100_000` 的候选默认进入 parking lot，不合并；只有作为更大 setcheck/model-family 的必要 seed 时继续追踪。
- 无论主线还是 tail，新增覆盖都必须以 current registry 的 union increment 为准，不能用 raw coverage 或 `coverage_count` 代替。

## Mining Loop

1. 默认先用快速候选排名脚本，不要手写临时 Python ranking：

```bash
PYTHONPATH=src .venv/bin/python scripts/data/rank_order5_setcheck_candidates.py \
  --candidate-file external/equational_theories/data/smallest_magma_examples.txt \
  --order 3 \
  --top-k 20 \
  --exact-check-top 3 \
  --output-jsonl data/processed/order5_strategy_registry/setcheck_candidate_rankings.jsonl
```

2. `--order 2` 且没有 `--candidate-file` 时会全枚举 Fin 2；Fin 3 及以上优先用候选文件、seeded 表或明确范围，不要默认全枚举。
3. 外部 table bank 先做表结构校验、`model_table_sha256` 去重和 provenance 保留；必要时再用同构 canonical form 合并展示，但落盘必须保留一个具体表。
4. ranking 脚本一次性读取并解析全部方程；不要在候选模型循环里反复调用 `_finmodel_sets`，因为它会重复解析 62k 条方程。
5. ranking 脚本对每个候选表计算：
   - `source_ids`：模型满足的方程。
   - `target_ids`：模型反驳的方程。
   - 不设置 order4×order4 `excluded_blocks`；canonical strategy coverage 必须覆盖全 order5 directed non-self pair space。
   - `coverage_count = rule.coverage_count()`。
   - `increment`：用 current registry 的 source/target membership mask 精确计算当前 union 新增覆盖，语义等价于 `new_union - current_union`。
   - `representative_pairs`：新增覆盖的 order4->order4、order4->order5、order5->order4、order5->order5，以及一个与旧策略重叠的 pair。
6. 只有 top-K 候选需要慢速复核；用 `--exact-check-top N` 调 `_union_count_for_rules` 复核前 N 个候选即可，不要对全部候选跑慢速 inclusion-exclusion。
7. 按 `increment` 降序排序；并列时看 `coverage_count`、模型阶数、表的稳定字符串。
8. 对置换同构或明显重复候选可以合并展示，但落盘时必须记录一个具体运算表。
9. 如果最佳增量低于当前 ROI Gate，先报告 ROI，并考虑是否进入 tail 模式、转向 predicatecheck 或暂停请求人工决策；不要机械新增低价值策略。

## Registry Update

选定候选后：

1. 正式 registry update 只由总控 session 执行。合并前先运行 merge gate 审计：

```bash
PYTHONPATH=src .venv/bin/python scripts/data/audit_order5_strategy_merge_gate.py --since-hours 12
```

   如果 `merge_allowed=false`，停止合并并报告 violation。
2. 先补 focused tests，固定新 strategy key、model family、source/target 小样例、summary union/overlap 口径和 certificate helper。
3. 再改 `order5_strategy_registry.py`，新增表常量、strategy key、`_model_family` 分支、`finmodel_false_judge_code` helper 或专用 answer helper。
4. 策略命名优先使用可解释 family，例如：
   - `false.finmodel.setcheck.fin2_constant.all_equations`
   - `false.finmodel.setcheck.fin2_left_projection.all_equations`
   - `false.finmodel.setcheck.fin2_right_projection.all_equations`
   - 其他表再使用稳定的 explicit/table 名称。
5. 用 `PYTHONPATH=src .venv/bin/python scripts/data/summarize_order5_strategy_coverage.py` 重新生成 JSON；这是落盘后的全量 registry 复核，不用于批量候选 ranking。随后刷新 `mining_state.json` 和 `merge_review_queue.json`。
6. 将本次 strategy 的 current union increment 落盘到：

```text
data/processed/order5_strategy_registry/setcheck_increment_history.jsonl
```

   每个新增 `false.finmodel.setcheck.*` strategy 必须有一行，至少包含：
   - `strategy_id`、`strategy_key`、`priority`、`model_family`、`model_table`
   - `raw_coverage`
   - `current_increment`
   - `union_before`、`union_after`
   - `model_source_count`、`model_target_count`、`model_verified`
   - `official_smoke`，judge smoke 之前可为 `null`，smoke accepted 后必须回填
   - `provenance`，例如 `ranking_exact_current_union_increment` 或 `recomputed_from_current_registry_priority_order_using_membership_masks`

   如果 history 文件不存在，先按当前 registry false strategy priority 顺序用与 ranking 相同的 source/target membership mask 逻辑重建历史；不要用 raw `coverage_count` 代替 `current_increment`。
7. 做 representative remote official judge smoke，默认用 `remote-http`/`remote-judge-v2` 指向 `http://10.220.69.172:8890`。至少覆盖：
   - 新增覆盖的 order4 source -> order4 target，如果存在。
   - 新增覆盖的 order4 source -> order5 target。
   - 新增覆盖的 order5 source -> order4 target。
   - 新增覆盖的 order5 source -> order5 target。
   - 一个与既有策略重叠的 pair，如果存在。
8. 跑相关测试：`tests/data/test_order5_strategy_registry.py`、`tests/order5_strategy_registry/` 中相邻 focused tests 和相邻 data/counterexample tests。

## Hard Constraints

- Do not edit `solver.py`；不 promote，不同步到 `submissions/solo_official/`。
- 非总控 mining session 不修改正式 registry、`coverage_summary.json`、`setcheck_increment_history.jsonl`、`mining_state.json`、`candidate_index*.json` 或 `merge_review_queue.json`；只写 `candidates/` 下候选产物。
- 不把单策略 `coverage_count` 当作新增覆盖；新增量只看 current union increment。
- 不修改外部 repo；只消费当前 repo 内的 external solver table/evidence artifact。
- 不把 Z3/Mace4/PySAT/Vampire/Prover9 的 solver status 当作 official judge smoke；只有 remote Lean judge accepted 的代表 pair 才能写成 accepted。
- 不落地缺少 `setcheck_increment_history.jsonl` history row 的新增 setcheck strategy。
- 不把慢速 `_union_count_for_rules` 放进候选枚举主循环；ranking 主循环必须使用 `rank_order5_setcheck_candidates.py` 或同等 mask increment 逻辑。
- 不把脚本验证、抽样或候选排名说成 judge 验证；只有 official judge accepted 的 pair 才能写成 judge smoke 通过。
- 不使用本地 Docker/Lean 做批量 certificate 预检或 judge smoke；Stage 2 judge 验证默认必须走 remote backend，除非用户单独明确要求排查本地环境。
- 不运行无界 Fin 3+ 搜索；长搜索必须先报告范围和预计成本。
- 不修改 official runner result JSON 或原始数据快照。

## Report Back

报告候选 leaderboard、选中策略、运算表、solver provenance/table fingerprint、source/target 数量、coverage、union increment、`setcheck_increment_history.jsonl` 记录、overlap/conflict、judge smoke pair 和测试命令。最后给出下一轮 top candidate，而不是泛泛说“继续探索”。
