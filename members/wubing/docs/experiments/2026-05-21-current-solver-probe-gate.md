# Current solver probe gate

日期：2026-05-21

## 目标

上一轮 `false.finmodel.predicatecheck.model_family.beam_after_k40.top80_min25k`
把 registry（策略注册表）确定性 false 覆盖提高了 `595957`，但 draft solver 在
`dev_fast` 上相对 current 没有 accepted count 增量。原因是 current solver 已经会动态
搜索很多有限反模型，registry 残差不等于 solver 残差。

本实验把候选策略准入改成 current solver first-message gate（首条消息探针）：
只有 current 没有在限定时间内直接输出目标 verdict 的候选，才继续投入 finite-model
挖掘、remote judge smoke 或 solver 集成。

## 新增工具

- 业务模块：`src/math_distill_stage2/solver_probe.py`
- 命令入口：`scripts/evaluator/probe_official_solver_first_message.py`
- focused tests：`tests/evaluator/test_solver_probe.py`

工具输入 candidate JSONL，可从以下形态构造官方 Solo problem：

- 直接包含 `problem`
- flat row：`eq1_id` / `eq2_id`，并从 `eq_size5.txt` 补全方程文本
- model-level row：`representative_pairs`，可用 `--representative-pair-key` 选择代表 pair

## 结果

已验证 false finite-model hits：

| 输入 | 结果 |
| --- | --- |
| `current_residual_after_top80_min25k_model_selector_probe_structured_le5_20260521_hits.jsonl` | `7/7` current 快速 false |
| `current_residual_after_top80_min25k_fin3_all_selector_probe_20260521_hits.jsonl` | `3/3` current 快速 false |
| `false_current_residual_after_k40_shape_20000_fin3_selector_hit_models_current_rerank_20260521.jsonl` 的 `new_order5_source_to_order5_target` representatives | `17/17` current 快速 false |

top80 registry residual sample 前 200 条：

- 输入：`current_residual_after_top80_min25k_shape_20000_seed20260521_residual_sample.jsonl`
- 输出：`artifacts/solver_distillation/2026-05-21/current_probe_top80_residual_sample200_solver_probe.jsonl`
- summary：`artifacts/solver_distillation/2026-05-21/current_probe_top80_residual_sample200_solver_probe_summary.json`
- `200` 条中，`5` 条 5 秒内首条输出 judge，包含 `3` false、`2` true
- `195` 条 5 秒首条消息超时
- `solver_uncovered_count = 197`，其中包含非 false 或慢路径样本

对 `197` 条 solver-uncovered sample 再做有限模型 selector：

- order-3 全枚举 `19683` 个模型：`0` hits
- 当前 registry manifest 中 `183` 个唯一模型：`0` hits

对同一批 `197` 条 sample 再做 mini egraph rewrite true search：

- 候选：`true.proof.templatecheck.egraph.rewrite_search.mini_bfs.v1`
- 参数：`max_steps=4`、`max_term_size=9`、`max_nodes=2000`
- 输出：`data/processed/order5_strategy_registry/candidates/true_egraph_solver_uncovered_top80_sample200_20260521_summary.json`
- `compiler_found_count = 0`

## 结论

1. false finite-model registry 长尾现在大量被 current solver 动态搜索覆盖，不能再只按
   registry union increment 决定 solver 集成。
2. 已有 top80/min25k 和旧 k40 rerank 的 finite-model hits 在 current solver 上都是快速
   false，不应 promote 相关 draft；这些候选最多有首条消息速度价值，没有 accepted count
   证据。
3. 真正 solver-uncovered 的 residual 样本暂未被 order-3 全枚举或现有 manifest 模型命中；
   mini egraph true search 也未命中。下一轮应优先做更强模型族、更强 proof template
   或更好的 residual 分层，而不是继续合并低阶 finite-model predicatecheck。

## 下一步

- 把 current solver first-message gate 作为 false 候选默认准入条件。
- 对候选 batch 先抽代表样本运行：

```bash
PYTHONPATH=src .venv/bin/python3 scripts/evaluator/probe_official_solver_first_message.py \
  --input <candidate.jsonl> \
  --output <probe.jsonl> \
  --summary <probe_summary.json> \
  --solver solvers/solo_official/current/solver.py \
  --expected-verdict false \
  --timeout-seconds 5 \
  --max-workers 16
```

- 只有 `solver_uncovered_count > 0` 且这些 uncovered rows 有 verified false certificate
  路径时，才进入 remote judge smoke 和 solver draft 集成。
