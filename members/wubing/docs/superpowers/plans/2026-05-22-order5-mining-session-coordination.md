# Order5 多 Session 策略挖掘协同方案

日期：2026-05-22

本文记录当前 Stage 2 order5 deterministic strategy（确定性策略）挖掘的多 session 分工、goal 使用方式和 registry（策略注册表）入库规则。后续新开 Codex App session 或 terminal Codex CLI session 时，先读本文，再读取最新机器状态文件。

> 注意：本文中的覆盖数字是 2026-05-22 快照。执行时必须重新读取 `data/processed/order5_strategy_registry/coverage_summary.json`、`mining_state.json` 和 `merge_review_queue.json`。canonical `coverage_summary.json` 覆盖全 order5 directed non-self pair space，必须包含 `order4_source_to_order4_target`；旧的 order4×order4 exclusion baseline 不再作为正式口径。

## 一句话结论

四个角色分工如下：

- **矿场总管**：管 baseline（基线）、merge queue（合并队列）、candidate -> registry 入库审批和 full summary。
- **真矿工**：挖 true proof-template candidates（真命题证明模板候选）。
- **反矿工**：挖 false candidates（假命题候选），当前主攻 `affine_mod17` certificate/smoke（证书/冒烟验证）阻塞。
- **地质师**：做 residual triage（残差分诊）、分桶、stale/subsumed（过期/已吸收）复核和调度建议。

一句话版：

```text
矿场总管管入库，真矿工挖 true，反矿工挖 false，地质师决定下一铲往哪儿挖。
```

## 当前机器状态入口

每个 session 每轮开始先读：

```bash
jq '{coverage_scope, includes_order4_source_to_order4_target, source_target_excluded_block_count, total_pairs, deterministic_false_covered, deterministic_true_covered, unresolved_estimate, conflict_count}' \
  data/processed/order5_strategy_registry/coverage_summary.json

jq '{baseline: .baseline.coverage, coordination, candidate_index: .candidate_index.status_counts}' \
  data/processed/order5_strategy_registry/mining_state.json

jq '{queue_counts, recommendation}' \
  data/processed/order5_strategy_registry/merge_review_queue.json
```

如果 `mining_state.json` 或 `merge_review_queue.json` 不存在或明显过期，由矿场总管刷新：

```bash
PYTHONPATH=src .venv/bin/python scripts/data/update_order5_strategy_mining_state.py
PYTHONPATH=src .venv/bin/python scripts/data/build_order5_strategy_merge_review_queue.py
```

2026-05-22 11:30 左右的事实：

| 指标 | 值 |
| --- | ---: |
| `deterministic_false_covered` | `2,369,622,194` |
| `deterministic_true_covered` | `1,364,538,580` |
| `unresolved_estimate` | `181,532,426` |
| `conflict_count` | `0` |

`postedge7` 已经被正式 registry / coverage summary 吸收，不要重复合并旧的 `postedge7` candidate summary。

## Goal 使用策略

### 必须使用 Goal 的角色

以下三个角色是持续推进型 session，适合长期 goal：

1. **真矿工**
2. **反矿工**
3. **地质师**

它们的共同边界：

- 只写 `data/processed/order5_strategy_registry/candidates/` 下的 candidate、audit、smoke、parking-lot 产物。
- 不修改：
  - `src/math_distill_stage2/order5_strategy_registry.py`
  - `data/processed/order5_strategy_registry/strategies.json`
  - `data/processed/order5_strategy_registry/coverage_summary.json`
  - `data/processed/order5_strategy_registry/setcheck_increment_history.jsonl`
  - `solver.py`
  - `submissions/solo_official/`

### 矿场总管白天不使用长期 Goal

白天人工在场时，矿场总管不挂长期 goal，默认由人工触发：

```text
总管，刷新 mining_state 和 merge_review_queue，按当前 baseline 给我下一批最值得 registry merge 的候选，不要修改 registry。
```

确认后再触发：

```text
总管，rescore 并合并 merge queue 里排名第一的 register_ready_main batch；合并前补 focused tests，合并后刷新 coverage_summary 和 merge queue。
```

原因：

- 矿场总管有正式 registry 写权限。
- 白天人工可以审核每个 batch 的边界。
- 避免总管长期 goal 和矿工 session 抢 `strategies.json`、`coverage_summary.json` 或 full summary。
- 如果需要夜间自动化，另开“矿场总管夜间模式”的窄权限 goal；白天不用。

## Merge Gate 审计脚本

矿场总管在任何正式 registry merge 前，先运行：

```bash
PYTHONPATH=src .venv/bin/python scripts/data/audit_order5_strategy_merge_gate.py --since-hours 12
```

这个脚本只做审计，不修改 registry。它检查两类风险：

1. 当前工作区是否存在 controller-only dirty paths（只有总管能修改的路径）。
2. 最近 Codex session logs 中是否有非当前总管 thread 对 protected paths 的写入痕迹。

Protected paths（受保护路径）包括：

- `data/processed/order5_strategy_registry/strategies.json`
- `data/processed/order5_strategy_registry/coverage_summary.json`
- `data/processed/order5_strategy_registry/setcheck_increment_history.jsonl`
- `data/processed/order5_strategy_registry/*_pair_indexes_YYYYMMDD.txt`
- `data/processed/order5_strategy_registry/mining_state.json`
- `data/processed/order5_strategy_registry/candidate_index.jsonl`
- `data/processed/order5_strategy_registry/candidate_index_summary.json`
- `data/processed/order5_strategy_registry/merge_review_queue.json`
- `src/math_distill_stage2/order5_strategy_registry.py`
- `tests/order5_strategy_registry/*`
- `submissions/solo_official/solver.py`

Candidate sessions 只允许写：

```text
data/processed/order5_strategy_registry/candidates/
```

如果脚本输出：

```json
{
  "merge_allowed": false,
  "recommendation": "stop_and_audit_non_controller_registry_writes_before_accepting_current_baseline"
}
```

总管必须先停下，报告 violation 和 affected paths；不要把新的 `coverage_summary.json` 静默当作可信 baseline。人工明确确认后，才可以继续接受当前 registry 状态并执行下一次 merge review。

### 夜间可以给矿场总管开保守 Goal

如果晚上到凌晨人工睡觉，但希望 registry 继续推进，可以给矿场总管开一个窄权限 goal。夜间总管只处理已有 merge queue，不做新策略挖掘；每轮最多合并一个 logical batch。

建议夜间 goal 见本文后面的“矿场总管夜间 Goal 模板”。

## 四个角色职责

### 矿场总管

职责：

1. 刷新 `mining_state.json`、`candidate_index.jsonl`、`candidate_index_summary.json`、`merge_review_queue.json`。
2. 判定候选是否 stale、subsumed、register-ready、needs-smoke、certificate-blocked 或 parking lot。
3. 对候选做 current baseline rescore，不信任旧 summary 的高分。
4. 只有候选通过 gate 后，才把 candidate 层提升到正式 registry 层。
5. 合并后运行 focused tests、刷新 `coverage_summary.json`、重排 merge queue、写审计文档。

矿场总管可以修改：

- `src/math_distill_stage2/order5_strategy_registry.py`
- `tests/order5_strategy_registry/` 下相关 focused tests
- `data/processed/order5_strategy_registry/strategies.json`
- `data/processed/order5_strategy_registry/coverage_summary.json`
- `data/processed/order5_strategy_registry/setcheck_increment_history.jsonl`，仅 setcheck 需要
- `docs/experiments/` 下审计记录

矿场总管不做：

- 不 broad mining（广撒网挖掘）。
- 不修改 `solver.py`。
- 不 promote，不同步 `submissions/solo_official/`。

### 真矿工

职责：

1. 只挖 true deterministic strategy candidates。
2. 当前主线是 `true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.*`，包括 `postedge*` 后续、top bucket、frontier / target extension 等。
3. 输出 candidate summary，包含 current union increment、conflict risk、after-merge projection、representative pairs、proof compiler、remote smoke。
4. 将 `>=1,000,000` 的主线候选交给矿场总管 review；`100,000..1,000,000` 进入 tail queue；低于 `100,000` 默认 parking lot。

真矿工不做：

- 不修改正式 registry。
- 不重复处理已合入的 `postedge7`。
- 不把 proofbank accepted pair 当作 pair-level known-proof table。

### 反矿工

职责：

1. 只挖 false deterministic strategy candidates。
2. 当前不再做 broad false finite-model / random / Z3 / endpoint 广搜。
3. 主攻 `false.finmodel.setcheck.affine_mod_probe.mod17` 的 certificate/smoke 阻塞。
4. 若新 false candidate 有 sample-to-exact 证据可能 `>=100,000` exact current union increment，才继续落盘候选。
5. 所有 remote smoke 小批代表样例优先 `max_workers=1`，记录 input/results/summary。

反矿工不做：

- 不修改正式 registry。
- 不扩大 `affine_mod17` 搜索范围，除非证书编码有实质新方案。
- 不把 Python 验证或抽样结果写成 judge accepted。

### 地质师

职责：

1. 做 current residual 的低成本分层抽样、shape bucket 分析和 candidate triage。
2. 判断下一块最高 ROI 应交给真矿工、反矿工，还是矿场总管。
3. 复核 `candidate_index` / `merge_review_queue` 中的 stale、duplicate、subsumed、still-promising、blocked。
4. 归档 negative evidence（负结果证据），避免矿工重复烧 CPU。

地质师不做：

- 不做 proofbank 大规模抽样。
- 不做 broad false finite-model / random / Z3 搜索。
- 不修改正式 registry。

## 白天触发矿场总管的时机

白天人工在场时，出现以下任一信号就触发矿场总管：

1. 矿工产出 `register_ready` 主线候选：
   - `exact current union increment >= 1,000,000`
   - remote smoke accepted
   - conflict 为 `0`
   - 非 stale/subsumed
2. merge queue 里累积 2-3 个同 family 候选。
3. `coverage_summary.json` 已刷新，baseline 发生变化。
4. 矿工报告：
   - `register-ready`
   - `needs total control review`
   - `main gate passed`
   - `remote smoke accepted`
   - `candidate ready for registry`
5. 人工准备离开电脑前，让矿场总管做只读整理：

```text
总管，刷新 mining_state 和 merge_review_queue，告诉我现在是否有可安全合并的 register_ready_main，不要修改 registry。
```

## Registry Merge Gate

候选进入正式 registry 前必须满足：

1. current baseline 下 exact union increment 明确。
2. 主线默认 `>=1,000,000`；tail 默认 `>=100,000` 且同 family batch 累计尽量接近或超过 `1,000,000`。
3. `conflict_count` 预计和实际复核均为 `0`。
4. remote judge smoke accepted，有 input/results/summary 路径。
5. true 候选 proof compiler / template 稳定。
6. false 候选 source 全满足、target 全反驳，且 certificate path 稳定。
7. focused tests 覆盖：
   - strategy key
   - cache / discoverability
   - certificate / proof path
   - representative pairs 或 coverage delta
8. 合并后必须刷新 `coverage_summary.json` 并重新生成 merge queue。

如果出现以下任一情况，总管停止，不继续合并：

- `conflict_count > 0`
- remote smoke rejected
- coverage summary 生成失败
- focused tests 失败
- active sessions 正在同时修改 registry
- 候选是否 stale/subsumed 不确定

## Goal 模板：真矿工

```text
/goal 在 /Users/zetyun2026/bing/projects/math-distill-equational-stage2/members/wubing 中继续 true deterministic strategy candidate-layer 工作，但不要做正式 registry merge。

当前总控 baseline 已含 postedge7，coverage_summary 当前 unresolved_estimate 约为 181,532,426。此 session 只写 data/processed/order5_strategy_registry/candidates/ 下的 true candidate/audit/smoke 产物，不修改 strategies.json、coverage_summary.json、solver.py，不 promote，不同步 submissions/solo_official。

优先任务：
1. 每轮开始先读取最新 data/processed/order5_strategy_registry/mining_state.json、merge_review_queue.json、candidate_index_summary.json、coverage_summary.json，确认 current baseline 和已合入策略，避免重复 postedge7 或旧 summary。
2. 继续 true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse family 的 candidate-layer 挖掘，优先探索 postedge8 / post-postedge7 residual buckets，或复核 merge_review_queue 中主线 true register-ready/needs-smoke 候选。
3. 不直接修改正式 registry；若发现候选满足 main gate，输出 candidate summary 交给总控 session review。主线候选默认要求 exact current union increment >= 1,000,000；tail 候选要求 >=100,000 且 proof compiler 稳定。
4. 每个 candidate 必须报告 exact/estimated current union increment、conflict risk、after_merge_projection、representative pairs、proof template/compiler、remote smoke 状态。remote smoke 使用 remote-http backend pool http://10.220.69.172:8888,http://10.220.69.153:8888，默认 max_workers=16，必要时降并发。
5. 对已被 current registry 吸收的旧 postedge/topbucket summary 标记 stale/subsumed，不重复合并；低于 100,000 的 true candidate 默认 parking lot。
6. 每轮结束写 candidate-layer summary，并明确“是否建议交给总控做 registry merge review”。
```

## Goal 模板：反矿工

```text
/goal 在 /Users/zetyun2026/bing/projects/math-distill-equational-stage2/members/wubing 中继续 false deterministic strategy candidate-layer 工作，但不要做正式 registry merge。

当前总控 baseline 已含 postedge7，coverage_summary 当前 unresolved_estimate 约为 181,532,426。此 session 只写 data/processed/order5_strategy_registry/candidates/ 下的 candidate/audit/smoke 产物，不修改 strategies.json、coverage_summary.json、solver.py，不 promote，不同步 submissions/solo_official。

优先任务：
1. 停止 broad false finite-model/random/Z3/endpoint 广搜，除非先有 current residual sample-to-exact 证据显示候选可能 >=100,000 exact current union increment。
2. 主攻 false.finmodel.setcheck.affine_mod_probe.mod17 的 certificate/smoke 阻塞：复核已有失败 summary，最小化 failing order5-source representative pair，比较 table/direct_split/affine_formula/Fin.ofNat 等证书编码，定位 remote judge rejected/timeout 的具体原因。
3. 所有 remote smoke 只做小批代表样例，使用 remote-http backend pool http://10.220.69.172:8888,http://10.220.69.153:8888，默认 max_workers=1，记录 input/results/summary。
4. 若发现新的 false candidate，必须报告 exact current union increment、true overlap/conflict、representative pairs、soundness evidence、remote smoke 状态；低于 100,000 默认 parking lot。
5. 每轮开始先读取最新 data/processed/order5_strategy_registry/mining_state.json、candidate_index_summary.json、coverage_summary.json；每轮结束写 candidate-layer audit summary，并说明是否应交给总控 session review。
```

## Goal 模板：地质师

```text
/goal 在 /Users/zetyun2026/bing/projects/math-distill-equational-stage2/members/wubing 中持续推进 Stage 2 order5 current residual 的 candidate-layer triage 和调度证据生产，不做正式 registry merge。

当前总控 baseline 已含 postedge7，coverage_summary 当前 unresolved_estimate 约为 181,532,426。此 session 只写 data/processed/order5_strategy_registry/candidates/ 下的 triage/audit/ranking/parking-lot 产物，不修改 strategies.json、coverage_summary.json、solver.py，不 promote，不同步 submissions/solo_official。

定位：
1. 这是 residual triage / strategy scout session，不是 true 专线，也不是 false 专线。
2. 每轮先读取最新 data/processed/order5_strategy_registry/mining_state.json、merge_review_queue.json、candidate_index_summary.json、coverage_summary.json。
3. 基于 current residual 做低成本分层抽样、shape bucket 分析、candidate_index stale/subsumed 复核、negative result 归档，判断最高 ROI 方向应交给 true session、false session，还是总控 merge review。
4. 不做 broad proofbank 抽样，不批量生成 Lean certificate；只有当某个 residual bucket 显示明显 true template 信号时，才少量生成 representative pairs 或 proof-template hints，交给 true session。
5. 不做 broad false finite-model/random/Z3 搜索；只有当 sample-to-exact evidence 显示可能 >=100,000 exact current union increment 时，才落 candidate hint，交给 false session。
6. 对 merge_review_queue 中 register_ready / needs_smoke_or_merge_review / tail / parking_lot 做 current baseline sanity review，标记 stale、duplicate、subsumed、still_promising、blocked。
7. 每轮输出：当前 unresolved_estimate、抽样/复核对象、最高 ROI 方向、建议交给哪个 session、产物路径、是否需要总控介入。
```

## Goal 模板：矿场总管夜间模式

```text
/goal 在 /Users/zetyun2026/bing/projects/math-distill-equational-stage2/members/wubing 中作为 Stage 2 order5 strategy registry 夜间总控，负责把已经满足门槛的 candidate-layer 策略审计后提升到正式 registry，但不做新的策略挖掘。

权限和边界：
1. 可以修改 src/math_distill_stage2/order5_strategy_registry.py、相关 focused tests、data/processed/order5_strategy_registry/strategies.json、coverage_summary.json、setcheck_increment_history.jsonl，以及必要的 docs/experiments 审计记录。
2. 不修改 solver.py，不 promote，不同步 submissions/solo_official。
3. 不做 broad true/false mining；只处理已有 data/processed/order5_strategy_registry/candidates/ 和 merge_review_queue.json 中的候选。
4. 每轮开始必须刷新 mining_state、candidate_index、merge_review_queue，并读取最新 coverage_summary；当前 baseline 以这些文件为准。
5. 每轮最多合并一个 logical batch，优先级为：
   a. register_ready_main 且 exact current union increment >= 1,000,000，remote smoke accepted，无 conflict；
   b. needs_rescore_or_smoke_main 中经 current profile rescore 仍 >= 1,000,000 且补齐 remote smoke accepted；
   c. tail candidates 只有在同 family batch 累计 >= 1,000,000 且实现简单、smoke accepted、conflict 0 时才合并。
6. 合并前必须补或更新 focused tests，覆盖 strategy key、cache/discoverability、certificate/proof path、coverage delta 或 representative pairs。
7. 合并后必须运行相关 focused tests、刷新 coverage_summary.json、重新生成 mining_state 和 merge_review_queue，并写 docs/experiments/YYYY-MM-DD-order5-strategy-nightly-controller.md 审计记录。
8. 如果出现 conflict_count > 0、remote smoke rejected、coverage_summary 生成失败、测试失败、active sessions 正在同时修改 registry、或不确定候选是否 stale/subsumed，立即停止，不继续合并，写 audit summary 说明阻塞。
9. 每轮结束报告：合并了什么、current increment、coverage 前后变化、smoke 状态、测试命令、产物路径、下一轮是否继续。
10. 每完成一次正式 registry merge 后暂停等待人工确认；如果只是审计或 rescore 未合并，可以继续下一轮。
```

## 新开 Session 启动清单

新开任意 session 时：

1. 读取 `AGENTS.md`。
2. 读取本文。
3. 读取 `skills/stage2-strategy-start/SKILL.md`，再按角色读取对应 skill：
   - 真矿工：`stage2-strategy-mine-true-template`
   - 反矿工：`stage2-strategy-mine-false-predicate` 或 `stage2-strategy-mine-setcheck`
   - 地质师：`stage2-strategy-explore` / `stage2-strategy-report`
   - 矿场总管：`stage2-strategy-explore` / `stage2-strategy-report`
4. 刷新或读取：
   - `coverage_summary.json`
   - `mining_state.json`
   - `merge_review_queue.json`
5. 执行角色内的 goal，不越权。

## 当前下一步

截至本文落盘时：

1. `postedge7` 已合入正式 registry，不重复合并。
2. 矿场总管下一步应处理 `merge_review_queue` 中的 `register_ready_main`，先对 top 候选做 current baseline rescore。
3. 真矿工继续 post-postedge7 true candidate 生产。
4. 反矿工主攻 `affine_mod17` certificate/smoke debug。
5. 地质师负责寻找下一块最高 ROI residual，并把结果分流给真矿工、反矿工或矿场总管。
