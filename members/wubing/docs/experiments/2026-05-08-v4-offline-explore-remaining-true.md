# 2026-05-08 v4 remaining true failures offline exploration

## 目标

从 `2026-05-08/v4` 的 `sample200` 剩余 17 个 true failures 中寻找下一轮
`d7` 的可实现 solver 提升方向。探索阶段只做 bounded offline probes（有界离线
探测），不修改 `solver.py`。

## 当前基线

- current version：`2026-05-08/v4`
- sample200：`183A / 17R / 0E`
- accepted true / false：`83 / 100`
- sample200 run：`artifacts/runs/2026-05-08/official-draft-d6-sample200-parallel-w8/`

剩余 17 个 failures 全部是 true proof miss：

- `true_3108_4642`
- `true_1167_2000`
- `true_1698_555`
- `true_1604_1822`
- `true_2860_3458`
- `true_1738_1258`
- `true_2654_2864`
- `true_2789_898`
- `true_2935_3138`
- `true_428_3725`
- `true_1500_498`
- `true_691_1976`
- `true_2771_2775`
- `true_2055_2656`
- `true_689_1350`
- `true_674_668`
- `true_1636_1839`

## Probe 1: grind variants

方法：

- 对 17 个剩余 true failures 尝试 `apply Classical.byContradiction; intro nh; grind`。
- 对代表题尝试更高参数 `grind (gen := 1000/2000/5000) (ematch := 1000/2000/5000)`。

结果：

- `apply Classical.byContradiction; intro nh; grind`：`0A / 17R / 0E`
- 高参数 `grind` 代表题：`0A / 4R / 0E`

结论：

- 直接把 d6 的 `grind` fallback 加强为反证式或更大参数没有收益。
- 不建议把这些 tactic variants 纳入 d7。

## Probe 2: deeper subexpr BFS

方法：

- 使用 run-local temporary solver，不修改 `solvers/solo_official/current/solver.py`。
- 只把默认 `try_subexpr_bfs_proof(...)` 调整为：

```python
try_subexpr_bfs_proof(
    problem,
    eq1_text,
    eq2_text,
    max_judge_calls=5,
    max_depth=7,
    time_limit=45,
)
```

- 代表题：
  - `true_3108_4642`
  - `true_1167_2000`
  - `true_1604_1822`
  - `true_674_668`

命令：

```bash
python scripts/evaluator/run_official_solo_history_parallel.py \
  --submission "$PWD/artifacts/runs/2026-05-08/official-probe-v4-bfs7-representative/submission" \
  --problem-set "$PWD/artifacts/runs/2026-05-08/official-probe-v4-bfs7-representative/problems.json" \
  --output-root "$PWD/artifacts/runs/2026-05-08" \
  --run-id official-probe-v4-bfs7-representative \
  --max-workers 4
```

结果：

- run dir：`artifacts/runs/2026-05-08/official-probe-v4-bfs7-representative/`
- `0A / 4R / 0E`
- 每题仍消耗 `1` 次 LLM，judge calls 为 `9-11`。

结论：

- 单纯提高现有 BFS 深度/时间，不是好的 d7 方向。
- 不建议把默认 BFS 调到 `max_depth=7`，会增加 wall time，但没有代表性收益。

## External proof source classification

17 个 pair 在 `external/equational_theories` 中都有已生成 theorem，但 proof
形态不适合直接放入 Stage 2 judge certificate：

- 15 个来自 `Generated/VampireProven/Proofs*.lean`，依赖 `superpose`、
  `mod_symm`、`subsumption` 等外部 proof automation。
- 2 个来自 `Generated/EquationSearch/theorems/Combined.lean`，依赖
  `SimpleRewrites`、`Subgraph`、`RewriteCombinations` 等外部 theorem chain。

代表统计：

| pair | source | proof lines | superpose | apply | nth_rewrite |
| --- | --- | ---: | ---: | ---: | ---: |
| 3108 -> 4642 | Vampire | 15 | 6 | 0 | 0 |
| 1167 -> 2000 | Vampire | 26 | 17 | 0 | 0 |
| 1604 -> 1822 | EquationSearch | 33 | 0 | 18 | 6 |
| 2935 -> 3138 | EquationSearch | 11 | 0 | 5 | 1 |
| 674 -> 668 | Vampire | 13 | 4 | 0 | 0 |
| 689 -> 1350 | Vampire | 13 | 4 | 0 | 0 |

## 结论

当前没有低风险、局部可验证的 d7 solver edit。

更合理的下一步是一个明确的策略分叉：

1. 实现小型 Vampire/superpose proof compiler，把外部 proof steps 转成
   judge 可接受的 `have`/`calc`/`congrArg`/`rw` 证书。
2. 实现 EquationSearch theorem-chain inliner，只针对 `SimpleRewrites` /
   `Subgraph` 等链路，递归展开成本地 proof template。
3. 暂停 deterministic proof compiler，转向 prompt/LLM proof synthesis，但 d5 的
   `MAX_LLM_ROUNDS=2` targeted run 已显示无收益，应谨慎。

按当前证据，优先级建议是 1，然后 2；这已经超出“微调现有模板”的范围，应先作为
策略分叉确认后再开 d7。
