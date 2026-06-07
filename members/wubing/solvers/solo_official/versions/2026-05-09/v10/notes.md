# 2026-05-09/v10 no-LLM Eq41 product compiler

当前从 `2026-05-09/d2` promote，基于 `2026-05-09/v9`。

## 结果

- remote dev_fast：`1648A / 352R / 0E`，相对 current baseline `+2`
- remote dev_main：`8227A / 1773R / 0E`，相对 current baseline `+8`
- test_locked shard sanity：`1634A / 366R / 0E`，相对 current 同 shard `+1`
- full test_locked gate：`40971A / 9029R / 0E`，相对 v9 full locked baseline `+21`
- LLM calls：`0`
- solver hash：`966cce8b1b508596154e881e3f7f90062414e575eab0c36ac50727d998bcb333`
- solver bytes：`253506`

## 核心改动

- 从 `Equation3992`, `Equation4156`, `Equation4174` 的已验证 proof body 推出 `Equation41`。
- 对 `4163`, `4186`, `4191`, `4193`, `4203` 使用小型本地 reduction 到上述 Eq41 seed。
- 用 `Eq41` 生成 `allprod : ∀ (a b c d : G), a ◇ b = c ◇ d`，再按当前题目的 `eq2` 编译最终目标。
- 证书自包含，不 import 外部 theorem，不使用明文 pair proof table。

## 约束说明

没有运行全量 22M sweep。`test_locked` 是 50,000 题；早期按用户“大规模数据只允许 shard 抽样或 targeted 验证”的限制，只跑固定 `i % 25 == 0` 的 2,000 题 shard。

用户随后将冻结规则更新为：`dev_fast`、`dev_main` 提升后，可以自动跑 full `test_locked` 作为 promotion gate。按该规则补跑 full `test_locked`：

- v9 baseline：`40950A / 9050R / 0E`
- v10 gate：`40971A / 9029R / 0E`
- delta：accepted `+21`，rejected `-21`，errors `0`
- accepted true：`15982 -> 16003`（`+21`）
- accepted false：`24968 -> 24968`（`+0`）
- judge calls：`132462 -> 132265`（`-197`）
- LLM calls：`0 -> 0`
- input sha256：`8a09561cecab0c8fa337db78c5c7876dfe472ac4708a85b4c9673c531a0dae7e`
- v9 run：`/workspace/artifacts/runs/2026-05-09/remote-v9-test-locked-full-w24-20260510-002`
- v10 run：`/workspace/artifacts/runs/2026-05-09/remote-v10-test-locked-full-w24-20260510-002`

该 full locked 结果只作为聚合冻结证据；不要用 locked 单题失败做下一轮训练目标。

`submissions/solo_official/solver.py` 未同步；最终官方提交导出单独处理。
