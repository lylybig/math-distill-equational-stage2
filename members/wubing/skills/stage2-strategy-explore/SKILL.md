---
name: stage2-strategy-explore
description: Use when exploring, validating, or controller-reviewing Stage 2 strategy registry coverage, including order5 pair-space strategies, merge queue refresh, merge gate audit, external solver proof/countermodel evidence triage, finite-model setcheck/paircheck/predicatecheck counterexamples, coverage union/conflict/canonical priority, and registry JSON updates before solver integration.
---

# Stage2 Strategy Explore

离线探索 Stage 2 strategy registry（策略注册表）。这个技能只处理策略资产本身：发现、验证、命名、落盘、统计覆盖和冲突；不要把探索结果直接写进 `solver.py`。

## Working Directory

All relative paths in this skill are relative to `members/wubing/`. If the shell
is at the team monorepo root, run `cd members/wubing` or set the command
`workdir` there before executing the commands below.

## Scope

优先使用这些事实来源：

- 业务逻辑：`src/math_distill_stage2/order5_strategy_registry.py`
- 注册表：`data/processed/order5_strategy_registry/strategies.json`
- 汇总：`data/processed/order5_strategy_registry/coverage_summary.json`
- mining state：`data/processed/order5_strategy_registry/mining_state.json`
- candidate index：`data/processed/order5_strategy_registry/candidate_index_summary.json`
- merge queue：`data/processed/order5_strategy_registry/merge_review_queue.json`
- pair space：`data/processed/order5_pair_space/manifest.json`
- order5 方程：`external/equational-theories-lean-stage2/examples/problems/eq_size5.txt`

策略命名保持语义可读：

- `false.finmodel.setcheck.*`：一个有限模型上，全部 source 方程成立、全部 target 方程不成立。
- `false.finmodel.paircheck.*`：有限模型验证具体 pair，而不是全 source/target 集合。
- `false.finmodel.predicatecheck.*`：有限模型加可判定谓词筛选覆盖集合。
- `true.proof.templatecheck.*`：Lean proof template 可系统生成 true certificate。
- `true.proof.explicitbank.*`：已验证 certificate bank 命中。

如果任务是系统性挖掘 finite-model setcheck 候选，优先转用 `stage2-strategy-mine-setcheck`。如果任务是专门挖 true proof template，或输入是 Z3/CVC5 quant-inst、Prover9/Ivy、Vampire/E proof trace、fake-target lemma、proofbench-derived true pattern，优先转用 `stage2-strategy-mine-true-template`。如果任务是从 paircheck bank、finite-model hits 或 external countermodel evidence 反推 false predicatecheck，优先转用 `stage2-strategy-mine-false-predicate`。如果任务涉及 external solver table bank、countermodel table、Z3/Mace4/PySAT/Kissat/CaDiCaL finite model 产物，优先转 `stage2-strategy-mine-setcheck` 或 `stage2-strategy-mine-false-predicate`；本技能只做总控分流、schema/registry 集成、候选复核和合并审计。当前总控默认先刷新/读取 `mining_state.json` 和 `merge_review_queue.json`，再决定是 rescore、smoke、合并、分诊还是报告。

## Controller State

总控每轮开始先读取当前状态；不要沿用历史覆盖数字、旧 summary 的高分或过期 merge queue：

```bash
jq '{coverage_scope, includes_order4_source_to_order4_target, source_target_excluded_block_count, total_pairs, deterministic_false_covered, deterministic_true_covered, unresolved_estimate, conflict_count}' \
  data/processed/order5_strategy_registry/coverage_summary.json
jq '{baseline: .baseline.coverage, coordination, candidate_index: .candidate_index.status_counts}' \
  data/processed/order5_strategy_registry/mining_state.json
jq '{queue_counts, recommendation}' \
  data/processed/order5_strategy_registry/merge_review_queue.json
```

如果状态缺失或过期，先刷新：

```bash
PYTHONPATH=src .venv/bin/python scripts/data/update_order5_strategy_mining_state.py
PYTHONPATH=src .venv/bin/python scripts/data/build_order5_strategy_merge_review_queue.py
```

白天协同模式下，总控 session 不使用长期 Goal；由人工显式触发刷新、审计或合并。若 `register_ready_main=0` 且 `needs_rescore_or_smoke_main=0`，默认不要直接合并 registry；改做 `certificate_blocked_high_roi`、`needs_metadata_review` 或 tail candidates 分诊。

## Parallel Candidate Mode

并行 true/false 挖掘时，默认使用候选模式：

- 子 session 只写 `data/processed/order5_strategy_registry/candidates/` 下的 candidate JSONL 和 summary JSON。
- 子 session 不直接修改 `strategies.json`、`coverage_summary.json`、`setcheck_increment_history.jsonl` 或 `order5_strategy_registry.py`。
- external solver artifacts 只能作为 candidate-layer input；proof trace/quant-inst/fake-target lemma 进入 true-template candidate review，finite table/countermodel 进入 false setcheck/predicate candidate review，总控不从 solver status 直接合并 registry。
- 总控 session 读取候选产物后，统一做 schema、duplicate、union increment、conflict、canonical priority 和 remote judge smoke 复核。
- 总控合并前，必须确认 `conflict_count` 保持 `0`，且新增覆盖使用 union increment 口径，不使用 raw coverage 冒充。
- 并行落盘文档优先读取：`docs/superpowers/plans/2026-05-22-order5-mining-session-coordination.md`。

## Working Universe

默认挖掘宇宙是 current unresolved residual；执行前先读取 `data/processed/order5_strategy_registry/coverage_summary.json`，以最新 `coverage_summary.unresolved_estimate` 为当前残差规模，不在技能中保存旧覆盖数字。canonical `coverage_summary.json` 的语义是全 order5 directed non-self pair space，必须包含 `order4_source_to_order4_target`；若该字段缺失或 `source_target_excluded_block_count != 0`，先重算 registry，不把它作为新 baseline。快速查询：

```bash
jq '{coverage_scope, includes_order4_source_to_order4_target, source_target_excluded_block_count, total_pairs, deterministic_false_covered, deterministic_true_covered, unresolved_estimate, conflict_count}' \
  data/processed/order5_strategy_registry/coverage_summary.json
```

- `total_pairs` 只作为分母、最终 `coverage_summary.json`、union/conflict 全局复核和对外报告口径使用。
- candidate mining 优先使用 residual cluster report、当前 registry mask、`coverage_summary.unresolved_estimate`、`current_*unresolved*` 样本、top unresolved shape bucket 和已验证 pair/proof clusters。
- 允许用 full pair space 做最终 summary 重算，但不要从 full pair space 随机生成候选或因为全空间成本过高而停止。
- 如果成本过高，先做 residual/top bucket 分层采样、predicate 压缩或 source/target mask 过滤，再把候选交给总控复核。

## ROI Gate

- 总控合并默认优先 `exact_union_increment >= 1_000_000` 的候选。
- 如果连续两轮没有百万级候选，或当前 strategy family 明显进入长尾，可以进入 `100_000 <= exact_union_increment < 1_000_000` 的 tail 模式。
- tail 模式只合并 soundness 清楚、实现成本低、judge smoke 路径稳定的候选，并优先按同一 family batch，使单轮累计新增覆盖尽量达到 `1_000_000`。
- `exact_union_increment < 100_000` 的候选默认进入 parking lot；只有作为更大 true/false family 的必要 seed，或解释重要 residual bucket 时才继续追踪。
- ROI Gate 只控制合并/扩跑优先级，不禁止早期探索；所有候选仍必须报告 raw coverage、union increment、冲突风险和验证状态。

## Workflow

1. 先说明候选策略属于哪一类，以及预期覆盖的是 true 还是 false。
2. 对 finite model setcheck，先判断是否应转 `stage2-strategy-mine-setcheck`；若只是验证一个指定模型，则全量扫描方程集合，确认 source 全成立、target 全不成立，并记录 source/target 数量和失败样例。
3. 计算 raw coverage、union coverage、same-verdict overlap、conflict 和 canonical selection；允许一个 pair 命中多个 raw strategy，不要把各策略覆盖量简单相加，并按 ROI Gate 标记主线、tail 或 parking lot。
4. 使用三层 registry 语义：
   - raw layer：`find_covering_strategies` 可返回多个策略。
   - union layer：`coverage_summary` 统计并集、重叠、冲突和 unresolved。
   - canonical layer：`find_canonical_strategy` 用 `priority` 再用 `strategy_id` 选一个确定策略。
5. 并行候选模式下，先把候选落到 `candidates/`，不要直接写正式 registry；总控复核通过后再进入下一步。
6. 正式 registry merge 前必须运行 merge gate 审计：

```bash
PYTHONPATH=src .venv/bin/python scripts/data/audit_order5_strategy_merge_gate.py --since-hours 12
```

   如果输出 `merge_allowed=false`，停止合并并报告 violation；不要静默接受新的 `strategies.json` / `coverage_summary.json` baseline。
7. 修改 schema、规则或统计逻辑时，先补 focused test，再改实现；只改 JSON 数据时，也要跑相关 summary/test 做回归。
8. 用 `PYTHONPATH=src .venv/bin/python scripts/data/summarize_order5_strategy_coverage.py` 重新生成 registry 汇总，再刷新 mining state 和 merge queue。
9. 只做代表性 remote official judge smoke：默认用 `remote-http`/`remote-judge-v2` 指向 `http://10.220.69.172:8890`。覆盖第一条、非平凡 source/target、被旧策略覆盖的样例；不要把探索变成大规模 judge 跑。
10. 如果新策略完全包含旧策略，优先让旧策略 inactive 或从 active registry 移除，并在新策略记录 `supersedes_strategy_ids` 或 legacy 字段。

## Hard Constraints

- 不编辑 `solver.py`，不 promote，不同步到 `submissions/solo_official/`。
- 不把 heuristic、抽样通过或未 judge 的证书说成确定通过。
- 不修改外部 repo；只消费当前 repo 内已有或用户复制进来的 external solver artifacts。
- 不把 Z3/CVC5/Mace4/PySAT/Vampire/Prover9/E 输出当作最终 solved；solver evidence 必须先转 candidate，再过 current union、conflict gate 和 remote Lean judge smoke。
- 不使用本地 Docker/Lean 做批量 certificate 预检或 official judge smoke；本机资源有限，Stage 2 judge 验证默认必须走 remote backend，除非用户单独明确要求排查本地环境。
- 不运行无界、长时间、付费或云端批量任务，除非用户明确要求。
- 不修改 official run result JSON 或原始数据快照。
- 并行候选模式下，不让 true/false 子 session 直接改正式 registry；正式合并必须由总控 session 做。
- 总控合并前不跳过 merge gate；不把非总控 session 的 protected write 当成可信 baseline。
- 不在普通探索中批量重命名既有技能；技能迁移必须单独处理。

## Report Back

回复时给出候选策略、验证命令、source/target 或 pair 数量、union/deterministic 覆盖变化、冲突数量、judge smoke 结果、改动文件，以及下一步最小候选策略。
