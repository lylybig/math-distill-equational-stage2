---
name: stage2-strategy-report
description: Use when creating or updating Chinese-first Stage 2 strategy registry reports, order5 coverage summaries, merge queue and mining-state briefs, active strategy briefs, soundness evidence summaries, coverage deltas, or next-strategy recommendations.
---

# Stage2 Strategy Report

把 Stage 2 strategy registry（策略注册表）的离线结果整理成人能快速判断的中文报告。这个技能只报告策略覆盖和验证证据；不要顺手修改 `solver.py`。

## Working Directory

All relative paths in this skill are relative to `members/wubing/`. If the shell
is at the team monorepo root, run `cd members/wubing` or set the command
`workdir` there before executing the commands below.

## Source Of Truth

优先使用已有产物，不要为了写报告默认重算：

- `data/processed/order5_strategy_registry/strategies.json`
- `data/processed/order5_strategy_registry/coverage_summary.json`
- `data/processed/order5_strategy_registry/mining_state.json`
- `data/processed/order5_strategy_registry/candidate_index_summary.json`
- `data/processed/order5_strategy_registry/candidates/*_candidates_*.jsonl`
- `data/processed/order5_strategy_registry/merge_review_queue.json`
- `data/processed/order5_strategy_registry/setcheck_increment_history.jsonl`
- `src/math_distill_stage2/order5_strategy_registry.py`
- 相关测试、summary 脚本、judge smoke 日志或当前会话记录

`coverage_summary.json` 是唯一 canonical 覆盖口径：全 order5 directed non-self pair space，包含 `order4_source_to_order4_target`。报告前确认 `coverage_scope == "all_order5_directed_nonself"`、`includes_order4_source_to_order4_target == true` 且 `source_target_excluded_block_count == 0`；不再引用旧的排除 order4×order4 baseline。

如果用户要求最新报告，或 state/queue JSON 看起来过期，先运行：

```bash
PYTHONPATH=src .venv/bin/python scripts/data/update_order5_strategy_mining_state.py
PYTHONPATH=src .venv/bin/python scripts/data/build_order5_strategy_merge_review_queue.py
```

如果 coverage summary 看起来过期，再运行：

```bash
PYTHONPATH=src .venv/bin/python scripts/data/summarize_order5_strategy_coverage.py
```

## Report Shape

默认把 Markdown 报告写到：

```text
docs/reports/YYYY-MM-DD-order5-strategy-registry-summary.md
```

建议章节：

1. 一句话结论
2. 当前 registry 状态
3. Active strategies
4. Soundness evidence（可靠性证据）
5. Coverage metrics（覆盖指标）
6. Overlap/conflict/canonical selection
7. Merge queue / mining state（合并队列和挖掘状态）
8. 最近变化
9. 下一步策略建议

核心指标至少包括：

- `total_pairs`
- `coverage_scope`
- `includes_order4_source_to_order4_target`
- `source_target_excluded_block_count`
- `raw_false_union_covered`
- `deterministic_false_covered`
- `deterministic_true_covered`
- `same_verdict_overlap`
- `conflict_count`
- `unresolved_estimate`
- 每个 active strategy 的 `strategy_id`、`priority`、`coverage_count`、`source_count`、`target_count`、`model_verified`、`supersedes_strategy_ids`
- 对 `false.finmodel.setcheck.*` 策略，优先从 `setcheck_increment_history.jsonl` 报告 `current_increment`、`union_before`、`union_after` 和 `official_smoke`
- 对 external solver evidence 候选，区分 `proof_trace` / `quant_inst` / `fake_target_lemma` / `finite_model` / `countermodel`，并报告它处于 candidate、local precheck、remote judge smoke pending、accepted 或 rejected 哪一层。
- merge queue 至少报告 `register_ready_main`、`needs_rescore_or_smoke_main`、`certificate_blocked_high_roi`、`tail_candidates`、`parking_lot`、`needs_metadata_review`、`stale_or_subsumed`
- mining state 至少报告 active goal session 数、candidate status counts，以及当前 recommendation

## Output Rules

- 中文优先，代码符号、路径、Lean theorem 名称和 JSON 字段保持原文。
- 对覆盖量使用 union/deterministic 口径；不要把多个策略的 `coverage_count` 简单相加后当作剩余量依据。
- 对 merge queue 使用 current baseline 口径；不要把旧 candidate summary 的高分写成可直接合并结论。
- 只在有明确 accepted 证据时说 “judge 验证通过”；否则写成 “数学/脚本验证” 或 “待 judge smoke”。
- 不把 Z3/CVC5/Mace4/PySAT/Prover9/Vampire/E 的 solver status 写成 solved；报告为 evidence layer，并说明还需要转成 true template 或 false setcheck/predicate candidate。
- 新报告族需要索引时，更新 `docs/reports/README.md`；只有新增顶层文档类别时才更新 `docs/README.md`。

## Hard Constraints

- 不编辑 `solver.py`，不 promote，不同步到 `submissions/solo_official/`。
- 不修改 official runner result JSON 或日志。
- 不生成 PDF，除非用户单独明确要求。
- 不把未验证候选策略写成已覆盖事实。
