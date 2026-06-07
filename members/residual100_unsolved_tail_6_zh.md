# residual-100-v1 仍未解决的 6 个等式蕴含

更新时间：2026-06-01

判定边界：本项目按官方远程 Stage 2 judge 的结果计数；只有 `accepted` 才视为已解决。当前审计记录显示，以下 6 个问题的 official acceptance 仍为 0。

数据来源：

- 问题表：`data/residual-100-v1/problems.jsonl`
- tail 状态：`.codex/skills/stage2-proofbench-solver/references/tail_status.json`
- 审计命令：`uv run python -m proofbench_tools.audit_attempts --format text --ids 0007 0012 0022 0040 0041 0049`

| ID | Equation IDs | 源等式 | 目标等式 | 当前倾向 |
| --- | --- | --- | --- | --- |
| `residual100_v1_0007` | `5295 => 35556` | `x = y * (z * (y * (y * (x * y))))` | `x = ((x * (y * z)) * (z * y)) * z` | true-proof 或 hard unknown |
| `residual100_v1_0012` | `9392 => 26593` | `x = y * ((x * z) * (z * (x * y)))` | `x = (y * ((z * w) * u)) * (y * u)` | true-proof 或 hard unknown |
| `residual100_v1_0022` | `18137 => 31679` | `x = (y * x) * (z * ((x * z) * z))` | `x = (y * ((z * z) * (x * w))) * w` | true-proof 或 hard unknown |
| `residual100_v1_0040` | `33436 => 35962` | `x = (y * (((z * z) * y) * x)) * y` | `x = ((y * (z * x)) * (w * w)) * y` | likely false 或 very hard countermodel |
| `residual100_v1_0041` | `34889 => 26354` | `x = ((y * y) * ((x * z) * x)) * z` | `x = (y * ((z * y) * y)) * (w * x)` | true-proof 或 hard unknown |
| `residual100_v1_0049` | `42784 => 48381` | `x * y = y * (x * ((z * y) * x))` | `x * y = (z * (z * w)) * (x * w)` | true-proof 或 hard unknown |

备注:

- 这里的“未解决”不是数学上的真假结论，而是指尚无官方 judge `accepted` 的 true/false 证书。
- `residual100_v1_0040` 当前更偏向 false 或需要高阶/无限反模型；其余 5 个当前记录更偏向 true-proof 或 hard unknown。
- `residual100_v1_0041` 有 fake-target lemma 被接受过，但 official target 仍未 accepted，因此仍列为未解决。
