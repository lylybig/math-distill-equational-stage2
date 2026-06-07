# Public Eval With Order-2 Countermodels

日期：2026-04-29

## 目标

把 `search_countermodels.py` 生成的 size-2 countermodels（2 元反模型）接回 public eval harness（公开集实验编排器），统计 ETP 直接有限反例和本地搜索反模型的合并覆盖率。

## 输入

- `data/processed/public_problem_index.jsonl`
- `data/processed/etp/etp_implications.jsonl`
- `data/processed/etp/etp_facts.jsonl`
- `artifacts/runs/2026-04-29/000001-countermodel-search-order2-full/countermodels.jsonl`

## 方法

运行：

```bash
python scripts/public_eval/run_public_eval.py \
  --countermodels artifacts/runs/2026-04-29/000001-countermodel-search-order2-full/countermodels.jsonl \
  --run-id 2026-04-29-000002-public-eval-with-order2-countermodels \
  --created-at-utc 2026-04-29T00:00:02Z
```

机器产物写入：

```text
artifacts/runs/2026-04-29/000002-public-eval-with-order2-countermodels/
```

## 结果

公开集总数：`1669`

正例：

- `819/819` 有 ETP implication path（蕴含路径）覆盖。
- 未覆盖正例：`0`

负例：

- 负例总数：`850`
- ETP 直接 finite fact（有限事实）覆盖：`60`
- 本地 size-2 countermodel（2 元反模型）覆盖：`438`
- 合并负例覆盖：`498/850`
- 未覆盖负例：`352`

按子集拆分：

- `normal`：负例覆盖 `456/500`，未覆盖 `44`
- `hard1`：负例覆盖 `9/45`，未覆盖 `36`
- `hard2`：负例覆盖 `11/100`，未覆盖 `89`
- `hard3`：负例覆盖 `22/205`，未覆盖 `183`

## 结论

size-2 反模型已经把负例覆盖从 `60/850` 提升到 `498/850`。这一步证明了 harness + countermodel bank（反模型库）的闭环有效。当前剩余问题集中在 `hard2` 和 `hard3`，下一步需要更高阶搜索或使用 ETP 全量 outcome 数据分流。

## 下一步

1. 为已找到的 size-2 反模型生成 Lean `Fin 2` counterexample certificate（反例证书）。
2. 对剩余 `352` 个未覆盖负例尝试 order-3 搜索，但要先做耗时预算和并行策略。
3. 接入 ETP 全量 `outcomes.json.zip`，判断剩余问题中哪些已知需要更复杂反模型或无限模型。
