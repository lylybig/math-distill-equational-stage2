# Countermodel Search MVP

日期：2026-04-29

## 目标

实现第一版 finite magma countermodel search（有限岩浆反模型搜索），读取 public eval harness 导出的 `uncovered_negatives.jsonl`，为缺少有限反例的负例搜索小阶 magma 运算表。

## 输入

- `data/processed/public_problem_index.jsonl`
- `artifacts/runs/2026-04-29/000000-public-eval-mvp/uncovered_negatives.jsonl`

## 方法

先运行受限样本：

```bash
python scripts/counterexample/search_countermodels.py --max-order 2 --max-problems 20 --run-id 2026-04-29-000000-countermodel-search-mvp --created-at-utc 2026-04-29T00:00:00Z
```

再运行完整 size-2 搜索：

```bash
python scripts/counterexample/search_countermodels.py --max-order 2 --run-id 2026-04-29-000001-countermodel-search-order2-full --created-at-utc 2026-04-29T00:00:01Z
```

搜索器枚举 order `1..max_order` 的所有 magma table（岩浆运算表），检查是否满足 `Equation 1` 且不满足 `Equation 2`。

## 结果

受限样本：

- 搜索前 `20` 个未覆盖负例。
- 找到 `17` 个 size ≤ 2 反模型。
- 未解决 `3` 个。

完整 size-2 搜索：

- 搜索 `790` 个未覆盖负例。
- 找到 `438` 个 size ≤ 2 反模型。
- 未解决 `352` 个。

按子集拆分，找到的反模型：

- `normal`：`428`
- `hard1`：`6`
- `hard2`：`0`
- `hard3`：`4`

未解决负例：

- `normal`：`44`
- `hard1`：`36`
- `hard2`：`89`
- `hard3`：`183`

## 结论

size-2 反模型搜索非常有效，能把公共集负例缺口从 `790` 降到 `352`。这说明后续应优先把 countermodel bank（反模型库）接入 public eval harness 和 Lean 证书生成，而不是马上跳到复杂搜索。

## 下一步

1. 为搜索出的 size-2 table 生成 Lean `Fin 2` counterexample certificate（反例证书）。
2. 对剩余 `352` 个未解决负例尝试 order 3 或接入 ETP 全量 outcome 数据做分流。

## 后续更新

已在 `2026-04-29-public-eval-with-order2-countermodels.md` 中完成合并评测：ETP 直接有限反例 + size-2 本地反模型使负例覆盖达到 `498/850`。
