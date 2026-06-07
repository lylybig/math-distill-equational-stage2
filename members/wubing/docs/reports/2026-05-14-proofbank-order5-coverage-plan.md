# 2026-05-14 Proofbank 与 Order5 Coverage 调整计划

## 一句话结论

当前 order5 strategy registry 的 true coverage（真命题覆盖）已经主要由可模板化的 singleton / product-anchor 策略支撑；proofbank 后续扩容应从“让 Codex 猜长证明”调整为“registry 模板或 external olean 先产证、官方 judge 再确认”的高精度路线。

## 当前覆盖状态

来源文件：`data/processed/order5_strategy_registry/coverage_summary.json`。

- `total_pairs`: `3915693200`
- `raw_false_union_covered`: `2157176426`
- `deterministic_false_covered`: `2157176426`
- `raw_true_union_covered`: `621431928`
- `deterministic_true_covered`: `621431928`
- `same_verdict_overlap`: `3327355345`
- `conflict_count`: `0`
- `unresolved_estimate`: `1137084846`

true coverage 的 active strategy 重点：

- `true.proof.templatecheck.singleton_collapse.any_target.v1`: `580746162`
- `true.proof.explicitbank.singleton_seedbank.any_target.v1`: `31719336`
- `true.proof.templatecheck.singleton_seedbank_specialization.any_target.v1`: `61528566`
- `true.proof.templatecheck.term_shape_anchor.product.any_product_target.v1`: `18306480`

这说明 true proofbank 的高价值增量不应只盯 order4 dev failure。更直接的增量方向是把这些已验证策略覆盖到的 true pair 转成官方 judge accepted certificate，尤其是 order5 source/target 参与的 pair。

## Proofbank 现状

合并本轮扩容后，`data/processed/proof_banks/gpt_true_certificates/bank_summary.json` 为：

- `attempt_count`: `3353`
- `accepted_count`: `2957`
- `problem_count`: `3235`
- `latest_problem_count`: `3235`

结构检查：

```text
python scripts/lean_certificates/proof_bank_check.py --bank data/processed/proof_banks/gpt_true_certificates
ok: true
errors: []
```

按来源看，当前高质量来源明显集中在 external / seedbank：

- `external_olean_harvest`: `1734` attempts, `1727` accepted, yield `0.996`
- `singleton_seed_harvest`: `532` attempts, `531` accepted, yield `0.998`
- `gpt55_high_signal_codex`: `305` attempts, `286` accepted, yield `0.938`
- `nightly_continuous_codex`: `762` attempts, `401` accepted, yield `0.526`
- `initial_manual_codex`: `20` attempts, `12` accepted, yield `0.600`

本轮实际扩容：

- `proofbank-20260513-train-high-signal-gpt55-102`: `3` attempts, `1` accepted, `2` rejected。
- `proofbank-20260514-external-olean-harvest-probe`: `200` attempts, `200` accepted，已合并。

质量审计对 `proofbank-20260514-external-olean-harvest-probe` 的 decision 为 `continue`。

## 调整原则

1. 优先扩 external olean / registry template 可产证候选。
   - 这类候选已经有编译产物或确定性模板，官方 judge 只做最终边界确认。
   - 本轮 200/200 accepted，明显优于近期 Codex 猜证批次。

2. Codex 生成改为补洞，不再作为主扩容通道。
   - `proofbank-20260513-train-high-signal-gpt55-102` 的两个 `singleton_seedbank_specialization` 候选被 official judge 判 `incorrect`。
   - 对 specialization 长证明，应该优先调用 `singleton_seedbank_specialization_true_judge_code` 这类 registry 代码生成器，而不是让 Codex 自行展开。

3. 采样要和 order5 coverage 目标对齐。
   - `singleton_collapse` 覆盖最大，应优先生成 order5 source -> order5/order4 target 的 judge smoke 和 bank 证据。
   - `singleton_seedbank` 与 `singleton_seedbank_specialization` 是 proofbank 到 solver template 的主要桥，继续保留高优先级。
   - `term_shape_anchor.product` 覆盖量较小但结构不同，应单独保留配额，避免 proofbank 只强化 singleton 家族。

4. 继续保留官方 judge accepted 作为唯一 accepted 边界。
   - templatecheck / explicitbank 是候选生成依据。
   - 进入 proofbank 的 accepted 仍必须来自 official judge `accepted` evidence。

## 下一轮执行计划

短期批次建议：

1. 继续 external olean harvest，每批 `200` 条。
   - 命令骨架：
     ```bash
     python scripts/lean_certificates/proof_bank_harvest_external_olean.py \
       --run-id proofbank-20260514-external-olean-harvest-012 \
       --limit 200 \
       --summary-only
     ```
   - 然后用 remote official judge import、dry-run merge、write merge、check。

2. 新增 registry-template proofbank 生成入口。
   - 从 `strategies.json` 选择 true strategy 的 source/target pair。
   - 用 `singleton_collapse_true_judge_code`、`singleton_seedbank_true_judge_code`、`singleton_seedbank_specialization_true_judge_code`、`product_anchor_true_judge_code` 生成 raw response。
   - 每批按策略分层，例如 `80/40/40/40`，并记录 manifest 中的 `strategy_id`、source/target order 类别、coverage bucket。

3. 对 Codex proof generation 降权。
   - 只用于 registry template 尚不能覆盖、或 external olean 缺失但 ETP 路径很短的候选。
   - 每批继续保持 1-3 个 prompt item，避免低质量长批次污染 attempts。

## Gate

继续扩容必须满足：

- `proof_bank_check.py` 通过。
- 每批 accepted yield 高于 `0.95`；若低于该线，暂停该来源并分析 error kind。
- 不使用 `test_locked` individual failures。
- 不修改 `solver.py`，不把未 judge accepted 的 template 证据写成 accepted certificate。
