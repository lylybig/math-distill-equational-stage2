---
name: stage2-strategy-start
description: Use when starting or continuing Stage 2 strategy registry work, including routing between controller merge-review work, parallel true/false deterministic mining, setcheck/predicatecheck exploration, proofbank strategy gates, and registry coverage reporting.
---

# Stage2 Strategy Start

Stage 2 strategy registry（策略注册表）的总入口。这个技能只负责分流和保持边界：需要并行 true/false 挖掘时转专用 mining skill，需要继续扩大覆盖时转探索，需要给人汇报时转报告。

## Working Directory

All relative paths in this skill are relative to `members/wubing/`. If the shell
is at the team monorepo root, run `cd members/wubing` or set the command
`workdir` there before executing the commands below.

## Route

- 用户说“继续找 setcheck”“finite model setcheck”“枚举模型”“挖掘下一个 setcheck 策略”时，使用 `stage2-strategy-mine-setcheck`。
- 用户说“external solver evidence”“proofbench-derived”“Z3/Prover9/Vampire/E/CVC5 proof trace”“quant-inst”“Ivy transfer”“fake-target lemma”“挖 true 确定性策略”时：如果证据是 proof trace、quant-inst 或局部 lemma 信号，使用 `stage2-strategy-mine-true-template`。
- 用户说“countermodel table”“table bank”“Z3/Mace4/PySAT/Kissat/CaDiCaL finite model”“有限反例表导入”时：若目标是单表 setcheck 或候选表 rescore，使用 `stage2-strategy-mine-setcheck`；若目标是从多个模型/证据反推 predicate 或 model family，使用 `stage2-strategy-mine-false-predicate`。
- 用户说“true 策略”“true template”“证明模板”“singleton/product/projection/law-instance”“挖 true 确定性策略”时，使用 `stage2-strategy-mine-true-template`。
- 用户说“false predicate”“predicatecheck”“paircheck 升格”“从 paircheck bank 反推”“false 确定性策略但不是 setcheck”时，使用 `stage2-strategy-mine-false-predicate`。
- 用户说“总控”“merge queue”“合并队列”“刷新 mining_state”“审计”“合并 registry”时，使用 `stage2-strategy-explore` 的 controller workflow。
- 用户说“并行挖掘 true false”“两个 session”“current residual”“当前残差”“落盘文档”时，先读取当前协同文档 `docs/superpowers/plans/2026-05-22-order5-mining-session-coordination.md`；必要时再参考历史背景计划 `docs/superpowers/plans/2026-05-18-order5-parallel-deterministic-mining.md`。再按任务分别使用 `stage2-strategy-mine-true-template`、`stage2-strategy-mine-false-predicate` 或 `stage2-strategy-mine-setcheck`；总控合并时使用 `stage2-strategy-explore`。
- 用户说“继续找”“下一步”“增加策略”“paircheck”“覆盖更多 pair”“更新 registry JSON”但没有明确 true template、false predicate 或 setcheck 挖掘时，使用 `stage2-strategy-explore`。
- 用户说“报告”“总结”“当前状态”“覆盖率”“给团队/领导看”“registry summary”时，使用 `stage2-strategy-report`。
- 用户同时要求挖掘和报告时，先用对应 mining/explore 技能得到最新 verified registry 结果，再用 `stage2-strategy-report` 生成报告。
- 用户问 proof bank 是否还要继续、或者某个 true strategy candidate 需要 accepted singleton seed 证据时，切到 `stage2-proofbank-start` 的 targeted strategy-gate workflow；不要继续无边界 strategy mining，也不要静默合并 registry。
- 如果用户只说“策略继续推进”或“下一步应该做什么”，默认选择 `stage2-strategy-explore`；如果上下文正在连续挖掘 true template、false predicate 或 setcheck，沿用对应专用技能。

## Boundaries

- Do not edit `solver.py`；不 promote，不同步到 `submissions/solo_official/`。
- 不复制子技能细节；执行前读取并遵守目标子技能的 `SKILL.md`。
- 并行模式下，子 session 默认只写 `data/processed/order5_strategy_registry/candidates/` 下的候选产物；正式 registry 合并由总控 session 处理。
- external solver artifacts 只作为当前 repo 的 candidate-layer input；proof trace 走 true-template，finite table/countermodel 走 setcheck 或 false-predicate。不要修改外部 repo，也不要把 solver status 当作最终 solved。
- 当前白天协同模式下，总控 session 不使用长期 Goal；由人工显式触发总控刷新、审计或合并。
- 每轮开始先读取当前机器状态，不要沿用旧覆盖数字或旧队列判断：

```bash
jq '{coverage_scope, includes_order4_source_to_order4_target, source_target_excluded_block_count, total_pairs, deterministic_false_covered, deterministic_true_covered, unresolved_estimate, conflict_count}' \
  data/processed/order5_strategy_registry/coverage_summary.json
jq '{baseline: .baseline.coverage, coordination, candidate_index: .candidate_index.status_counts}' \
  data/processed/order5_strategy_registry/mining_state.json
jq '{queue_counts, recommendation}' \
  data/processed/order5_strategy_registry/merge_review_queue.json
```

- 如果 `mining_state.json` 或 `merge_review_queue.json` 不存在或明显过期，总控刷新：

```bash
PYTHONPATH=src .venv/bin/python scripts/data/update_order5_strategy_mining_state.py
PYTHONPATH=src .venv/bin/python scripts/data/build_order5_strategy_merge_review_queue.py
```

- 总控在正式 registry 合并前必须先运行 merge gate 审计，确认没有非总控 session 的 protected write 痕迹，也没有未解释的 controller-only dirty paths：

```bash
PYTHONPATH=src .venv/bin/python scripts/data/audit_order5_strategy_merge_gate.py --since-hours 12
```

- 若审计输出 `merge_allowed=false`，先停止合并并报告 violation；不要静默接受新的 `strategies.json` / `coverage_summary.json` baseline。
- 如果 `merge_review_queue.json` 显示 `register_ready_main=0` 且 `needs_rescore_or_smoke_main=0`，默认下一步不是直接合并 registry，而是处理 `certificate_blocked_high_roi`、`needs_metadata_review` 或 tail batch 分诊。
- 默认挖掘宇宙是 current unresolved residual；执行前必须读取 `data/processed/order5_strategy_registry/coverage_summary.json`，以最新 `coverage_summary.unresolved_estimate` 为当前残差规模，不在技能中保存旧覆盖数字。canonical `coverage_summary.json` 的语义是全 order5 directed non-self pair space，必须包含 `order4_source_to_order4_target`。快速查询：

```bash
jq '{coverage_scope, includes_order4_source_to_order4_target, source_target_excluded_block_count, total_pairs, deterministic_false_covered, deterministic_true_covered, unresolved_estimate, conflict_count}' \
  data/processed/order5_strategy_registry/coverage_summary.json
```

- `total_pairs` 只作为分母、最终 coverage summary 和 conflict/union 校验使用。
- 如果候选搜索成本过高，先缩到 current unresolved sample、top unresolved shape bucket 或当前 registry mask 上继续；不要因为 full pair space 成本过高而直接停止 strategy mining。
- 不把 proof bank 证书生成当作 strategy registry 探索。只有用户明确要求 true certificate bank，或 active strategy gate 明确需要 source-level accepted certificate evidence 时，才切到 `stage2-proofbank-*`。
- 不把 solver run 分析当作 strategy registry 报告。只有用户明确要求 solver baseline/run/version 时，才切到 `stage2-train-*` 或 `stage2-report-solver-baseline`。

## Report Back

先说明选择了哪个子技能和原因，然后按该子技能的输出规则汇报结果。
