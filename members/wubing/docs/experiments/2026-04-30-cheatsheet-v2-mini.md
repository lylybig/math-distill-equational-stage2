# 2026-04-30 Cheatsheet v2 小样本实验

## 目标

基于 `train-mini-v1` 和 `dev-mini-v1` 的失败分析，更新 `cheatsheets/mini/current/stage2_judge_json_certificate.en.md`，再用 smoke、train-mini、dev-mini 顺序验证是否值得冻结为新版本。

## 输入

- 当前候选 cheatsheet：`cheatsheets/mini/current/stage2_judge_json_certificate.en.md`
- 基线版本：`cheatsheets/mini/versions/v2026-04-30-dev-mini-v1/stage2_judge_json_certificate.en.md`
- smoke run：`artifacts/runs/2026-04-30/stage2-evaluator-smoke-v3`
- train run：`artifacts/runs/2026-04-30/stage2-evaluator-train-mini-v2`
- dev run：`artifacts/runs/2026-04-30/stage2-evaluator-dev-mini-v2`

## 修改要点

- 强化 `op` 只能二元调用，禁止 `op a b c`、`op (op a b) c d`。
- 要求用自定义 `Carrier`，避免重定义 Lean 内置 `Bool`。
- 明确 finite model（有限模型）必须通过所有变量的 exhaustive `cases ... <;> rfl`。
- 补充 Lean 语法约束：pattern 参数用逗号，分支用 `=>`。

## 指标对比

| run | accuracy | f1 | mean parse success | request success | verdict accuracy | lean strict pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| dev-mini-v1 | 0.10 | 0.10 | 0.80 | 0.80 | 0.8125 | 0.10 |
| dev-mini-v2 | 0.05 | 0.0952 | 0.60 | 0.60 | 0.75 | 0.05 |
| train-mini-v2 | 0.30 | 0.2222 | 0.70 | 0.70 | 0.7143 | 0.30 |

## 失败分析产物

每个 run 目录均已落盘：

- `analysis.md`
- `errors.jsonl`
- `failure_taxonomy.json`

`dev-mini-v2` 的主要失败：

- request failure：8/20
- `lean_semantic_failure`：6
- `lean_simp_loop_failure`：2
- `wrong_verdict`：3

## 决策

不发布 `v2026-04-30-dev-mini-v2`。

原因：`dev-mini-v2` 的 final accuracy、Lean 严格通过率、request success、verdict accuracy 均低于 `dev-mini-v1`。虽然 `train-mini-v2` 提升到 3/10，但 dev 集没有复现提升，不能作为冻结版本。

## 下一步

- 优先处理 false 证书的 finite model 真实性：当前模型仍会输出 premise 不能 `rfl` 的伪反模型。
- 在 cheatsheet 中进一步禁止 `|>`、过度 `simp`，并要求 true proof 不使用递归展开式 `simp`。
- 在下一轮 dev-mini 前考虑启用失败复跑，降低 API 请求错误对小样本判断的干扰。
