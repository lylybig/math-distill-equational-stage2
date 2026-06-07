# Order5 策略覆盖注册表设计

## 背景

`order5_pair_space` 已经把 order<=5 的有向非自反 pair 宇宙压缩成隐式空间：

- `law_count = 62576`
- `pair_count = 3915693200`
- `pair_index <-> (eq1_id, eq2_id)`

下一步需要把“某个 pair 是否已经被确定性策略覆盖”变成可查询、可统计、可复现的系统。目标是持续缩小 3.9B pair 中需要 LLM 或新 theorem mining 处理的剩余空间。

## 目标

构建一个离线 `strategy coverage registry`（策略覆盖注册表），用于：

1. 给定 `pair_index`，查询哪些确定性策略覆盖它。
2. 统计每个策略覆盖多少 pair。
3. 统计多个策略的 union coverage（并集覆盖）和 verdict conflict（判定冲突）。
4. 从未覆盖 pair 中采样，作为后续 true/false 挖掘对象。

第一版不修改 `solver.py`，不改变官方提交目录，只服务于离线分析和下一步策略选择。

## 非目标

- 不生成 3.9B 行 `pair_index -> strategy_id` 全量表。
- 不在 registry 中重复保存 equation text。
- 不把未验证的启发式规则登记为正式 deterministic coverage。
- 不把 solver 版本号当作策略主键；solver 可以调用多个策略，但策略 id 应独立稳定。

## 命名

文档中使用“覆盖规则（coverage rule）”作为主名。它表示一个布尔规则：

```python
def covers(eq1_id: int, eq2_id: int) -> bool:
    ...
```

若 `covers(...)` 返回 `True`，表示该 pair 被该策略覆盖，可以使用对应 deterministic verdict/certificate 处理。

`coverage predicate` 翻译成“覆盖谓词”也准确，但项目文档和代码更偏工程实现，优先使用 `coverage_rule`。

## 策略标识

策略使用可读稳定字符串 id：

```text
<verdict>.<family>.<variant>.v<version>
```

例子：

```text
false.spine_left_zero_nonleft.base.v1
false.finite_model_bank.v12.v1
true.singleton_collapse.eq2.v1
true.anchor_h_instantiated_grind.v12.v1
```

推荐数据结构：

```json
{
  "strategy_key": "false.spine_left_zero_nonleft.base",
  "strategy_version": 1,
  "strategy_id": "false.spine_left_zero_nonleft.base.v1",
  "verdict": false,
  "coverage_kind": "source_target_sets",
  "certificate_family": "spine_isolation_left_zero"
}
```

版本规则：

- 新增策略：新增 `strategy_id`。
- 覆盖范围变化：升 `strategy_version`。
- 实现修 bug 但覆盖语义不变：保留策略版本，更新实现哈希或 notes。
- verdict 变化：不能原地更新，必须新增 id，并将旧策略标记为 deprecated。
- 多策略合并：新增 aggregate strategy，不删除旧策略。

## 覆盖规则类型

第一版只实现小而稳定的覆盖规则类型：

### `source_target_sets`

适用于形如：

```text
eq1_id in source_ids
eq2_id in target_ids
eq1_id != eq2_id
```

覆盖数量可用公式计算：

```python
count = len(source_ids) * len(target_ids) - len(source_ids & target_ids)
```

单个 pair 查询为两个 set membership 检查，平均 O(1)。

### `source_all_targets`

适用于形如：

```text
eq1_id in source_ids
eq2_id != eq1_id
```

覆盖数量：

```python
count = len(source_ids) * (law_count - 1)
```

这是 true collapse/singleton 类策略的候选表达方式。

### `explicit_pairs`

适用于稀疏策略或小规模验证集，只保存少量 `pair_index`。第一版可先支持查询和计数，不用于大策略。

## 重叠和冲突

一个 pair 可以被多个覆盖规则覆盖。

处理原则：

- 多个策略给出同一 verdict：允许，统计 union 时去重。
- 多个策略给出不同 verdict：标记为 conflict，不能进入 deterministic coverage。
- 输出 certificate 时需要 canonical strategy priority，但第一版 registry 只记录和报告候选策略，不决定 solver 输出优先级。

## 数据流

```text
eq_size5.txt
  -> equation feature extractor
  -> strategy coverage rule
  -> strategy registry
  -> coverage summary / pair query / unresolved sampler
```

第一版先复用现有 spine feature 逻辑，登记一个 false 策略：

```text
false.spine_left_zero_nonleft.base.v1
```

它的覆盖规则：

```text
eq1 是 left-zero source
eq2 是 non-left target
eq1_id != eq2_id
```

后续 true 策略只有在 certificate family 已经可靠时再登记为正式 coverage。

## 输出

### Strategy Manifest

建议路径：

```text
data/processed/order5_strategy_registry/strategies.json
```

内容包括每个策略的 id、verdict、coverage kind、输入文件哈希、source/target 统计和 deprecated 状态。

### Coverage Summary

建议路径：

```text
data/processed/order5_strategy_registry/coverage_summary.json
```

至少包含：

- `coverage_scope`，canonical 值为 `all_order5_directed_nonself`
- `includes_order4_source_to_order4_target`，canonical 值为 `true`
- `source_target_excluded_block_count`，canonical 值为 `0`
- `total_pairs`
- `strategy_counts`
- `deterministic_true_covered`
- `deterministic_false_covered`
- `same_verdict_overlap`
- `conflict_count`
- `unresolved_estimate`

第一版可以只精确统计单策略 coverage；多策略 union 在只有一个策略时自然等于单策略。第二版再扩展多策略 union。

## API 草案

```python
registry = build_default_order5_strategy_registry(equations_path)

registry.find_covering_strategies(pair_index)
registry.coverage_summary()
registry.sample_uncovered(size, seed)
```

返回示例：

```json
{
  "pair_index": 123456789,
  "eq1_id": 1974,
  "eq2_id": 9901,
  "covering_strategies": [
    {
      "strategy_id": "false.spine_left_zero_nonleft.base.v1",
      "verdict": false
    }
  ]
}
```

## 错误处理

- `pair_index` 越界：抛出 `ValueError`。
- self pair：在默认 pair space 中视为非法。
- 策略覆盖规则出现 true/false 冲突：summary 中报告 conflict，不把该 pair 算入 deterministic covered。
- 策略输入文件哈希变化：manifest 中记录 hash，后续复现时显式暴露差异。

## 测试计划

新增 focused tests：

1. `source_target_sets` 覆盖数量公式正确处理交集和 self pair。
2. 单个 `pair_index` 能查到正确策略。
3. 未覆盖 pair 返回空策略列表。
4. 同 verdict overlap 不重复计数。
5. 不同 verdict overlap 报告 conflict。
6. CLI 能输出 coverage summary，不生成全量 pair 表。

## 第一版实施范围

建议新增：

```text
src/math_distill_stage2/order5_strategy_registry.py
tests/data/test_order5_strategy_registry.py
scripts/data/summarize_order5_strategy_coverage.py
```

第一版只实现：

- `source_target_sets`
- spine left-zero false 策略
- 单 pair 查询
- 单策略 coverage summary
- manifest/summary 输出

不实现：

- true 策略登记
- roaring bitmap
- SQLite
- solver 集成
- 大规模 unresolved 精确枚举

## 后续扩展

第二版再加入：

- true collapse/singleton coverage rule
- 多策略 union 精确统计
- unresolved random sampler
- explicit pair list 和压缩 bitmap
- solver strategy priority 规则
