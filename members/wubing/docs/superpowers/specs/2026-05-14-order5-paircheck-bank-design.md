# Order5 Paircheck Bank 设计

## 一句话结论

先建设 `false.finmodel.paircheck.bank` 离线证据库，用有限模型逐 pair 验证当前 order5 registry 的 unresolved false 候选；候选发现和数学检查在本地执行，所有 Stage 2 official judge（官方验证器）证书预检和 smoke 必须走远程 judge backend，不再默认使用本机 Docker/Lean。

## 背景

当前 `data/processed/order5_strategy_registry/coverage_summary.json` 中：

- `total_pairs`: `3915693200`
- `deterministic_false_covered`: `2213756500`
- `deterministic_true_covered`: `621461374`
- `unresolved_estimate`: `1080475326`
- `conflict_count`: `0`

现有 `false.finmodel.setcheck.*` 已覆盖大块 false pair，但最新候选排名显示新增 setcheck 增量已经很低。下一步需要把“单个有限模型只验证具体 pair”的稀疏证据沉淀成 paircheck bank（逐 pair 反模型证据库），再从 bank 中反推更大 predicatecheck/setcheck 模式。

## 目标

1. 生成可复现的 order5 unresolved candidate pair 样本。
2. 用有限 magma table（有限岩浆运算表）验证 `eq1` 成立且 `eq2` 不成立，形成 `false.finmodel.paircheck.*` 证据。
3. 保存 Python 验证、Lean certificate（Lean 证书）生成、remote official judge smoke 的完整来源。
4. 后续接入 strategy registry 时，使用 explicit pair coverage（显式 pair 覆盖）统计 union increment 和 conflict。

## 非目标

- 不编辑 `solver.py`，不 promote，不同步到 `submissions/solo_official/`。
- 不把未 judge 的证据写成 accepted。
- 不把 paircheck bank 伪装成 source × target setcheck 覆盖。
- 不全量物化 10.8 亿 unresolved pair。
- 不使用本地 Docker/Lean 做批量证书预检。

## 远程 Judge 规则

项目级规则是：Stage 2 official judge 或 Lean certificate 批量预检必须走 remote backend。

默认 backend pool：

```text
remote-http simple-api: http://10.220.69.153:8888,http://10.220.69.172:8888
```

调用前对 backend pool 做 `/health` 检查，优先使用健康服务；显式 `--base-url` 可固定到单个 backend。允许替代：

```text
remote-ssh judge host
```

本机只做轻量 Python 计算、JSON 生成和 raw Lean code 生成；除非用户明确要求排查本地 judge 环境，否则不运行本地 Docker/Lean 批量验证。

## 数据目录

建议新增：

```text
data/processed/order5_paircheck_bank/
  candidate_pairs.jsonl
  model_pool.jsonl
  countermodels.jsonl
  verified_bank.jsonl
  official_smoke_results.jsonl
  bank_summary.json
```

`candidate_pairs.jsonl` 记录从 registry unresolved 中采样出的 pair：

```json
{"pair_index":0,"eq1_id":1,"eq2_id":2,"stratum":"order4_source_to_order5_target"}
```

`countermodels.jsonl` 记录 Python 验证通过的有限模型：

```json
{"pair_index":0,"eq1_id":1,"eq2_id":2,"order":2,"table":[[0,0],[1,1]],"python_verified":true}
```

`verified_bank.jsonl` 记录进入 bank 的稳定证据：

```json
{
  "strategy_key":"false.finmodel.paircheck.bank",
  "pair_index":0,
  "eq1_id":1,
  "eq2_id":2,
  "order":2,
  "table_sha256":"...",
  "python_verified":true,
  "lean_code_sha256":"...",
  "remote_official_smoke":null
}
```

## 采样策略

从 `Order5StrategyRegistry` 当前 union 视角筛选：

- 无 false covering strategy。
- 无 true covering strategy。
- 无 conflict。
- 排除 self pair。

第一阶段按 stratum 分层：

- `order4_source_to_order4_target`
- `order4_source_to_order5_target`
- `order5_source_to_order4_target`
- `order5_source_to_order5_target`

2026-05-26 起，正式 registry/coverage summary 的 canonical 口径包含 `order4_source_to_order4_target`；paircheck bank 采样、去重和 representative smoke 也应把它作为正式 stratum，而不是旧的排除口径。

## 模型池策略

第一批模型池来源：

1. 当前 registry 中已落地的 `false.finmodel.setcheck.*` table。
2. `external/equational_theories/data/smallest_magma_examples.txt`。
3. `external/equational_theories/data/interesting_finite_magmas/`。
4. 历史 official smoke accepted 的 Fin 4/5/7 table。

对每个模型只全量评估一次 `eq_size5.txt`，缓存 `source_ids` 和 `target_ids`。对 candidate pair 只做 membership check：

```text
eq1_id in source_ids and eq2_id in target_ids
```

如果某个模型产生明显大块新增覆盖，优先转 `stage2-strategy-mine-setcheck` 升格为 setcheck；只有稀疏但确定的命中进入 paircheck bank。

## 验证层级

1. Python 验证：`FiniteMagma.satisfies(eq1) and not FiniteMagma.satisfies(eq2)`。
2. Lean code 生成：remote official judge smoke 使用 `JudgeProblem` 风格的 `finmodel_false_judge_code(table)`；旧的 `finite_magma_counterexample_certificate(eq1_id, eq2_id, table)` 只用于需要离线 pure/equational_theories asset 时，不作为默认 smoke 路径。
3. Remote official judge smoke：用 remote backend 验证代表样本，记录 accepted/rejected/error。

只有第 3 层 accepted 的样本才能写成 “official judge accepted”。第 1/2 层只能写成 Python/Lean 预检通过或待 remote judge。

## Registry 接入

已在 `src/math_distill_stage2/order5_strategy_registry.py` 增加 `ExplicitPairsRule`，用于表达稀疏 paircheck bank 覆盖：

```python
def covers(eq1_id: int, eq2_id: int) -> bool:
    return pair_index in explicit_pair_indexes
```

新增策略命名：

```text
false.finmodel.paircheck.bank.v1
```

coverage summary 已支持 `SourceTargetSetsRule` 与 `ExplicitPairsRule` 混合 union：source-target 规则仍走现有优化计数，explicit pair 只枚举 bank 中的稀疏 pair。paircheck bank 的新增覆盖不能直接等于 bank 行数，必须扣除已有 false union 和 true conflict。

## MVP Gate

第一阶段目标：

- 采样 `100k-500k` unresolved candidate pairs。
- 产出 `>=10000` 条 Python verified paircheck countermodels，若达不到则扩大模型池或改为 targeted search。
- remote official judge smoke 至少 `100` 条，优先覆盖不同 stratum、不同 table order、不同模型来源。
- `conflict_count` 保持 `0`。
- 生成 `bank_summary.json`，报告命中率、table 分布、stratum 分布、和当前 registry union increment 估算。

## 测试计划

- focused tests：unresolved sampler 不返回已覆盖 pair。
- focused tests：model membership 命中与 `FiniteMagma.satisfies` 逐 pair 验证一致。
- focused tests：`verified_bank.jsonl` schema、dedupe、table hash 稳定。
- registry 接入阶段再补 `ExplicitPairsRule` 的 coverage count、union、conflict 和 canonical priority 测试。

## 下一步

1. 实现 `scripts/data/build_order5_paircheck_bank.py` 和对应 `src/math_distill_stage2/order5_paircheck_bank.py`。
2. 用小样本生成 `candidate_pairs.jsonl` 与 `countermodels.jsonl`。
3. 生成 remote judge smoke 输入，并通过 `remote-http` 验证。
4. 根据 `bank_summary.json` 判断是否进入 registry 接入，或先扩大模型池。

remote smoke 命令：

```bash
PYTHONPATH=src python scripts/lean_certificates/verify_order5_paircheck_remote_smoke.py \
  --input data/processed/order5_paircheck_bank/official_smoke_input.jsonl \
  --output data/processed/order5_paircheck_bank/official_smoke_results.jsonl \
  --summary data/processed/order5_paircheck_bank/official_smoke_summary.json \
  --base-urls http://10.220.69.153:8888,http://10.220.69.172:8888 \
  --max-workers 1 \
  --no-cache
```
