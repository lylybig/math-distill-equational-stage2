# 2026-04-30 Cheatsheet v3 小样本实验

## 目标

基于 v2 失败报告继续约束英文运行版 cheatsheet，重点处理：

- `|>` 把等式命题当作 carrier term（载体项）使用。
- true proof 中 `simp`/`simpa` 递归爆栈。
- false certificate（反例证书）中 premise 无法通过 exhaustive `cases ... <;> rfl` 的伪反模型。
- `simp [op] at bad` 后继续 `cases bad` 导致 `No goals to be solved`。

本轮同时引入两份 cheatsheet：

- `cheatsheets/mini/current/stage2_judge_json_certificate.en.md`：mini 英文运行版，供 evaluator 使用。
- `cheatsheets/mini/current/stage2_judge_json_certificate.zh.md`：mini 中文人工复查版，不作为模型输入。

## 代码组织变更

- 错误归因核心逻辑下沉到 `src/math_distill_stage2/error_analysis/`。
- 新增分层入口 `scripts/error_analysis/analyze_stage2_run.py`。
- 新增分层入口 `scripts/evaluator/run_stage2_evaluator.py`、`scripts/evaluator/run_stage2_smoke.py`。
- 新增分层入口 `scripts/cheatsheets/version_cheatsheet.py`。
- 根 `scripts/` 不再保留旧兼容命令，新实验统一使用领域子目录入口。

## 运行

- smoke：`artifacts/runs/2026-04-30/stage2-evaluator-smoke-cheatsheet-v3`
- train-mini：`artifacts/runs/2026-04-30/stage2-evaluator-train-mini-cheatsheet-v3`
- dev-mini：未运行

未运行 dev-mini 的原因：train-mini 已显著低于 v2，继续跑 dev-mini 不能产生可接受候选，且会额外消耗模型请求。

## 指标对比

| run | accuracy | f1 | mean parse success | request success | verdict accuracy | lean strict pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| train-mini-v2 | 0.30 | 0.2222 | 0.70 | 0.70 | 0.7143 | 0.30 |
| train-mini-v3 | 0.10 | 0.00 | 0.50 | 0.60 | 1.00 | 0.10 |
| smoke-v3-candidate | 0.20 | 0.00 | 0.60 | 0.60 | 1.00 | 0.20 |

## 失败分析产物

每个已运行目录均已落盘：

- `analysis.md`
- `errors.jsonl`
- `failure_taxonomy.json`

train-mini-v3 的主要失败：

- request failure：4/10
- parse failure：1/10
- `lean_semantic_failure`：3
- `lean_forbidden_pattern`：1

## 决策

不发布 v3。

原因：虽然 parsed 样本的 verdict accuracy 到 1.00，但 parse success、request success、Lean strict pass 和 final accuracy 均不达标；尤其 train-mini-v3 的 final accuracy 从 v2 的 0.30 降到 0.10。

## 下一步

- 回滚或弱化 v3 中让 prompt 过长、格式稳定性下降的规则，保留 `|>` 禁令和英文/中文双文件结构。
- 对 false certificate 不应继续要求模型“心算”反模型；下一轮应考虑把 offline evidence 总结成更短、更明确的 false 证书模式，但仍不能在评估时传逐题 evidence。
- 在下一轮 mini 评估中考虑开启一次失败复跑，单独记录 request-noise-adjusted metrics（请求噪声调整指标）。
