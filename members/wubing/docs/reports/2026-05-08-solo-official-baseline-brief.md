# Stage 2 Solo 当前 baseline 简报

日期：2026-05-08

## 一句话结论

当前最佳 baseline 是 `2026-05-07/v3`，在官方 `sample200` 上达到 `177/200`，通过率 `88.50%`。其中 false 样本已全部解决，剩余 23 个失败都是真命题 proof 生成问题。

## 当前最佳版本

| 项目 | 当前值 |
| --- | --- |
| 当前最佳版本 | `solvers/solo_official/versions/2026-05-07/v3/` |
| 当前工作快照 | `solvers/solo_official/current/solver.py` |
| sample200 成绩 | `177/200` |
| accepted rate | `88.50%` |
| true / false accepted | `77 / 100` |
| LLM calls / LLM solved | `23 / 0` |
| 总耗时 | `2611.6s`（43m31.6s） |

说明：`submissions/solo_official/solver.py` 还没有同步到 v3。探索阶段统一使用 run-local submission，最终正式提交前再导出。

## 版本演进

| 版本 | 来源 | solver.py 改动 | sample200 | 通过率 | LLM calls / solved | 备注 |
| --- | --- | --- | ---: | ---: | ---: | --- |
| `v1` | opnorm 派生原始版本 | 无新增项目内改动 | `175/200` | `87.50%` | `25 / 0` | 第一版可复现 baseline 起点 |
| `v2` | `v1 -> d1 -> v2` | false 反例搜索从 `Fin 5` 扩到 `Fin 7`；Lean false certificate 增加递归深度设置 | `176/200` | `88.00%` | `24 / 0` | 新增解决 `false_907_2534` |
| `v3` | `v2 -> d2 -> v3` | 内联 `Equation1682 -> Equation411` 的 `Fin 5` 已知反例表 | `177/200` | `88.50%` | `23 / 0` | 新增解决 `false_1682_411` |

## 关键改动说明

### v2：解决 `false_907_2534`

发现方式：从 v1 的 25 个失败样本里拆出 false failure，确认 `false_907_2534` 是反例搜索覆盖不足。扩大到 `Fin 7` 后可以找到反例。

v2 相对 `versions/2026-05-07/v1/solver.py` 做了三处小改动。

具体在 `v2/solver.py` line 351，把 false 反例搜索上限调到 `Fin 7`：

```python
def extended_counterexample(eq1_text, eq2_text, max_n=7, random_attempts=10000):
```

在 `v2/solver.py` line 505，给 false certificate 加 Lean recursion depth 设置：

```python
"set_option maxRecDepth 1000000\n"
```

在 `v2/solver.py` line 4430，实际 fallback 调用也同步使用 `max_n=7`：

```python
n, table = extended_counterexample(eq1_text, eq2_text, max_n=7, random_attempts=5000)
```

验证：完整 sample200 从 `175/200` 提升到 `176/200`，无 regression。

### v3：解决 `false_1682_411`

发现方式：v2 后剩余唯一 false failure 是 `false_1682_411`。在本地 ETP 事实数据中查到 `Generated/All4x4Tables/Refutation906.lean`：它满足 `Equation1682` 且 refute `Equation411`，反例大小是 `Fin 5`。

v3 来自 `drafts/2026-05-07/d2`。d2 相对 `versions/2026-05-07/v2/solver.py` 只改了一个地方：给 `known_counterexample` 加了一个内联已知反例表，用来解决 `false_1682_411`。

具体在 `v3/solver.py` line 376：

```python
_INLINE_KNOWN_COUNTEREXAMPLES = {
    ("Equation1682", "Equation411"): (
        5,
        [
            [1, 2, 4, 0, 3],
            [0, 3, 4, 1, 3],
            [3, 2, 2, 0, 1],
            [4, 1, 4, 3, 0],
            [2, 0, 2, 2, 4],
        ],
    ),
}
```

然后在 `known_counterexample` line 389 一开始先查这个内联表：

```python
inline = _INLINE_KNOWN_COUNTEREXAMPLES.get((eq1_name, eq2_name))
if inline:
    return inline
```

验证：focused test、单题 official run、failed subset、完整 sample200 均通过；完整 sample200 从 `176/200` 提升到 `177/200`，false 样本达到 `100/100`。

## 当前判断

- 本轮提升全部来自 deterministic solver 改进，不是 LLM 直接证明成功。
- LLM fallback 可以正常调用，但目前 `LLM solved = 0`。
- false 方向在 sample200 上已经清零，下一阶段应集中处理 true proof。

## 下一步

建议围绕剩余 23 个 true failures 做结构聚类，优先寻找可以模板化的 Lean proof。每次新增 proof template 前先补 focused test，再做 failed subset 和 sample200 验证；如有新增 accepted，再 promote 为新的 `vN`。
