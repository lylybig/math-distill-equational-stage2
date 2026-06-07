# Order5 continuous deterministic strategy goal

日期：2026-05-19

本文是长期 goal（目标）指令文件。goal objective（目标描述）只需要引用本文，不要把全文塞进 goal objective。

## Objective

在 `/Users/zetyun2026/bing/projects/math-distill-equational-stage2/members/wubing` 持续探索、验证、合并 Stage 2 order5 deterministic strategies（确定性策略），尽可能降低 `data/processed/order5_strategy_registry/coverage_summary.json` 中的 `unresolved_estimate`。canonical `coverage_summary.json` 覆盖全 order5 directed non-self pair space，必须包含 `order4_source_to_order4_target`。

不要设置固定日期 checkpoint（检查点）；不要因为到 2026-05-20 早上而暂停或总结。除非用户明确要求停止、汇报、暂停或切换方向，否则一直继续执行：

```text
发现策略 -> 验证策略 -> 合并策略 -> 重算覆盖 -> 读取新 residual -> 下一轮探索
```

## Startup

每次进入或恢复这个 goal 时：

1. 先读取项目规则：
   - `AGENTS.md`
   - `skills/stage2-strategy-start/SKILL.md`
2. 使用 `stage2-strategy-start` 作为总入口，并按任务需要使用：
   - `stage2-strategy-explore`
   - `stage2-strategy-mine-true-template`
   - `stage2-strategy-mine-false-predicate`
   - `stage2-strategy-mine-setcheck`
   - `stage2-info-competition`，仅在需要核对官方资料时使用
3. 先读取这些事实来源：
   - `docs/superpowers/plans/2026-05-18-order5-parallel-deterministic-mining.md`
   - `data/processed/order5_strategy_registry/coverage_summary.json`
   - `data/processed/order5_strategy_registry/strategies.json`
4. 每轮都重新读取最新 `coverage_summary.json`，不复用旧的 unresolved 数字。

## Current Context

当前已知起点大约是：

- `unresolved_estimate=581753415`
- `conflict_count=0`

但执行时必须以文件最新值为准。

当前工作区可能已有未提交改动。必须保留并尊重这些改动，不要 reset、checkout 或覆盖：

- `src/math_distill_stage2/order5_strategy_registry.py`
- `tests/order5_strategy_registry/test_model_family_predicatecheck.py`
- `tests/order5_strategy_registry/test_product_collapse_strategy.py`

每轮开始先运行或检查：

```bash
git status --short
jq '{coverage_scope, includes_order4_source_to_order4_target, source_target_excluded_block_count, total_pairs, deterministic_false_covered, deterministic_true_covered, unresolved_estimate, conflict_count}' data/processed/order5_strategy_registry/coverage_summary.json
```

## Hard Boundaries

除非用户明确改变边界，否则必须遵守：

1. 不修改 `solver.py`。
2. 不 promote。
3. 不同步 `submissions/solo_official`。
4. 不修改 official runner result JSON 或原始数据快照。
5. 不提交 git commit，除非用户明确要求。
6. 不使用本地 Docker/Lean 做批量预检。
7. Stage 2 judge smoke（官方验证器冒烟）默认使用 `remote-http` backend pool：
   - primary：`http://10.220.69.172:8888`（32 核，优先用于当前挖掘 smoke）
   - fallback：`http://10.220.69.153:8888`
   - CLI 优先显式传 `--remote-judge-base-url http://10.220.69.172:8888` 或把 pool 写成 `http://10.220.69.172:8888,http://10.220.69.153:8888`，避免默认健康检查总是选中 153。
   - 172 上的小批量 smoke 默认从 `--remote-judge-max-workers 16` 或 `--max-workers 16` 起步；机器空闲且 certificate 体积不大时可试 `24`。除非确认内存/队列稳定，不直接开满 32。

## Main Loop

每一轮执行以下闭环：

1. 发现新的 deterministic strategy candidate（确定性策略候选）。
2. 验证 soundness（可靠性）：
   - false 策略必须做 finite model（有限模型）、setcheck、predicatecheck 或 model-family 的全量/确定性验证。
   - true 策略必须有 proof template、proof adapter、proofbank import 或代表样例 remote judge accepted 证据。
3. 计算 `raw coverage` 和 `current union increment`。
   - 不要把 raw coverage 冒充新增覆盖。
   - 新增覆盖必须以 union increment 为准。
4. 生成 representative pairs（代表 pair），尽量覆盖：
   - order4 source -> order4 target
   - order4 source -> order5 target
   - order5 source -> order4 target
   - order5 source -> order5 target
   - 与旧策略 overlap 的 pair
5. 对代表 pair 跑 remote-http official judge smoke。
6. 若候选通过 gate，允许作为总控正式更新 registry 相关文件，包括：
   - `src/math_distill_stage2/order5_strategy_registry.py`
   - `data/processed/order5_strategy_registry/strategies.json`
   - `data/processed/order5_strategy_registry/coverage_summary.json`
   - `data/processed/order5_strategy_registry/setcheck_increment_history.jsonl`，仅 setcheck 需要
7. 合并后运行 focused tests 和 coverage summary 重算。
8. 读取新的 `coverage_summary.unresolved_estimate`，继续下一轮。

## Merge Gate

正式合并前必须满足：

1. schema 检查通过。
2. duplicate、supersedes、priority 关系清楚。
3. exact 或可信 estimated union increment 明确。
4. `conflict_count` 必须保持 `0`。
5. false 策略的模型或 predicate 验证通过。
6. true 策略至少有代表样例 remote judge accepted。
7. 大 true 候选如果 proof adapter 未通过，不合入正式 registry。
8. focused tests 通过。
9. `coverage_summary.json` 只能由脚本重算生成，不能手工编辑。
10. 每次正式合并前后记录：
    - `before_unresolved`
    - `after_unresolved`
    - `delta`
    - `conflict_count`
    - 测试命令
    - remote smoke 证据

如果 coverage summary 全量重算过慢，先用候选级 exact/estimated increment 做筛选；但正式宣布 unresolved 降低前，必须完成正式 summary 重算。

## Priorities

优先级按 ROI（投入产出）和可靠性排序：

1. P0：确认当前 registry 改动和 focused tests 状态，必要时补最小测试。
2. P1：攻克 `true.proof.templatecheck.etp_order5_eq2_singleton.any_target.v1` 的 proof adapter/import 问题；目标是让代表 pair remote judge smoke accepted。
3. P2：继续 `false.finmodel.predicatecheck` model-family 挖掘，优先找 exact/estimated `union_increment >= 1,000,000` 的候选。
4. P3：继续 true product、projection、law-instance、constancy、match-collapse、rewrite-normal-form 等模板。
5. P4：裸 setcheck 只作为 seed 或 parking lot，不做无界 Fin3/Fin4/Fin5 枚举。

## External Reference Lane

外部资料不是主线。只有当前没有更好的 deterministic strategy 时，才 bounded（有界）参考更多资料找灵感。

优先参考：

- official Stage 2 repo
- `examples/solo/TUTORIAL.md`
- official demo solvers，例如 opnorm
- contributor network / Zulip 本地快照
- teorth equational theories blueprint
- `external/equational_theories`
- 其它网络资料

外部资料只能作为 strategy lead（策略线索）。必须本地复现，转成 source predicate、target predicate、proof generator 或 countermodel generator，并通过验证后，才能进入 registry。

不做无边界泛读；每次资料分析都要产出候选线索或明确判定“暂无可用策略”。

## Skill Updates

如果发现现有 `stage2-strategy-*` 技能影响挖掘质量，或缺少稳定重复流程，可以小步更新对应 `SKILL.md`。

技能更新要求：

1. 修改范围尽量小。
2. 中文优先，保留必要英文术语。
3. 更新后运行：

```bash
pytest tests/skills/test_stage2_skills.py -q
```

禁止：

1. 重命名技能目录。
2. 做无关技能迁移。
3. 顺手大改不相关技能。

## Coverage Triage

覆盖门槛是 triage priority（分诊优先级），不是绝对禁止：

1. `>=100M`：最高优先级，先解决 soundness/proof adapter。
2. `>=10M`：主线合并候选。
3. `>=1M`：正常合并门槛。
4. `100K-1M`：parking lot；如果实现成本低、零冲突、smoke accepted，可批量合入。
5. `<100K`：默认只作为 seed、回归测试或更大模板证据。

最终以 soundness、union increment、实现成本和 conflict 风险综合判断。

## Long-Run Guardrails

长跑期间必须防止重复、跑偏或卡死：

1. 每轮开始先检查 `git status`、最新 `coverage_summary.json`、最近 `candidates/*_summary.json`。
2. 避免重复探索已证伪或已合并方向。
3. 同一策略方向如果连续 2-3 轮没有产生正 union increment、remote smoke 进展或可执行的新 adapter 方案，就切换到下一个优先级 lane。
4. 所有重要负结果必须简短落盘到 `candidates/` summary 或 `docs/experiments/`，记录：
   - `candidate_key`
   - 失败原因
   - 验证命令
   - 是否可作为 future seed
5. 禁止无界搜索。
6. 任何预计超过 30 分钟的大搜索，必须先缩到 sample、top bucket、cache 或 ranking，并明确输出文件。
7. 如果一个长命令卡住或收益不明，停止它，记录原因，切换到更小范围或下一策略 lane。
8. 保持文件改动边界清楚，避免混入无关重构。

## Running Ledger

维护一个 running ledger（运行账本）。每次正式合并或证伪重要候选时，在 `data/processed/order5_strategy_registry/candidates/` 下写一个 controller review 或 summary JSON。

账本至少记录：

- before/after unresolved
- delta
- 文件改动
- 验证命令
- remote smoke 结果
- 测试结果
- 失败候选与失败原因

不要只依赖聊天记录。

## Rollback Rules

如果某个正式 registry 合并导致 `conflict_count != 0`、测试失败或 summary 不一致：

1. 只回退本轮自己新增的策略/代码。
2. 不 reset。
3. 不 checkout 覆盖用户已有改动。
4. 回退后记录失败原因和后续处理建议。

## Goal Vs Automation

goal 是目标约束和持续追踪，不一定等同于后台定时任务。

如果当前会话或 goal 机制不能真正无人值守持续执行，优先保持当前 thread 活跃继续跑；不要把“已设置 goal”误当成已经有后台定时任务。

如果需要自动唤醒或定时继续，应由用户另行明确要求创建 automation。

## Reporting

默认不设置固定时间汇报，不因为日期变化暂停。

每完成实质性一轮，可以在本地候选 summary 或实验记录中简短记录：

- 最新 `unresolved_estimate`
- 新候选文件
- union increment
- `conflict_count`
- remote judge smoke 结果
- 测试结果
- 下一轮最小动作

用户主动查看或询问状态时，再汇报当前进展；汇报后继续探索。
