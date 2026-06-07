# Weekly 2026-W22 - Stage2 Projects Summary

> Date: 2026-05-29

## 本周关键结论

本周 `math-distill-equational-stage2` 的 order5 未解决估计量从
`179,644,523` 降到 `134,001,266`，净降 `45,643,257`，约 `25.4%`。
当前覆盖口径保持 `conflict_count = 0`。

`math-distill-stage2-proofbench` 侧，Codex 自动解题在 100 题样本上已达到
`94/100` accepted；1000 题样本目前达到 `718/1000` accepted，剩余 `282`
题。

## math-distill-equational-stage2

### 未解决估计量

| 指标 | 数值 |
| --- | ---: |
| 周初可比 baseline | `179,644,523` |
| 5/29 最新 registry | `134,001,266` |
| 净下降 | `45,643,257` |
| 下降比例 | `25.4%` |

当前最新覆盖口径：

| 指标 | 数值 |
| --- | ---: |
| total pairs | `3,915,693,200` |
| deterministic true covered | `1,394,597,946` |
| deterministic false covered | `2,387,093,988` |
| conflict count | `0` |

### 主要策略

true 侧继续扩展 `opnorm hconst-default-sandwich / match-collapse` 系列，
包括 postedge tail、plus-hstep tail、one-sided constancy recursive NF 等，
把旧 true tail 证书模式转成可 registry 化的 pair-index/source-target
策略。

这些 true 策略名的含义：

| 策略名 | 含义 |
| --- | --- |
| `postedge tail` | `hconst-default-sandwich` 主线合并后的尾部扩展。做法是从 current residual 的 shape/frontier 里继续挑仍有 sample hit 的 source-target bucket，按 postedge6/7/8 这样的轮次追加小批量 pair-index cache。它不是新证明原理，而是同一个 hconst sandwich proof compiler 在主线之后的 tail mining。 |
| `plus-hstep tail` | `hconst` 只能表达“某个变量不影响结果”的局部常值性；`hstep` 允许中间再使用普通 source equation 实例做一步子项改写。因此 plus-hstep tail 是把 hconst-default-sandwich 和 hstep-default-sandwich 组合起来，覆盖纯 hconst 折叠够不到的一小段 true tail。 |
| `one-sided constancy recursive NF` | 从 source 推出“一侧参数无关”的局部引理，例如 RHS 不依赖左参数或右参数，然后递归地把表达式规约到一个 normal form。`row_constancy_recursive_nf` / `column_constancy_recursive_nf` 分别对应右参数或左参数被省略时的行/列常值性。 |

false 侧重点是 finite-model setcheck/predicatecheck，尤其是 `Fin17 / mod17
affine`。本周通过 source-first 代表样本选择突破了原先的 smoke 阻塞，
后续又 revive 了仍有 current-new 覆盖的 `mod17` rows，带来约
`2,189,171` graph-new false coverage，且 `0` conflict。

### 蕴含图的作用

本周建成并使用 columnar implication graph store，将策略挖掘从旧 summary
分数驱动，升级为 current exact delta / conflict 驱动。它不是直接自动生成
证明的模块，而是 current coverage oracle 和 strategy mining 调度器。

对 true strategy mining，蕴含图的作用主要有四点：

1. 快速判断 true 候选是否仍有新增覆盖。true 策略通常产出 pair-index
   cache；蕴含图可以 preview `newly_set_count`、`already_set_count` 和
   `conflict_count`，避免继续优化已经 stale 的 true tail。
2. 给 true mining 找 frontier。对某个 source，可以查看这一行还有多少
   unknown，以及哪些 target 仍未解决。unknown 很少的 source 适合交给
   prover、Z3 proof-guided、hinst/grind 模板继续冲。
3. 帮助发现 true 策略族的形状集中区。通过 exact-unknown sample、row
   summary、source/target shape bucket，可以定位 true residual 集中在哪些
   source/target 形态上，减少盲扫。
4. 控制 true 策略合并风险。对 true strategy，合并前要确认新增覆盖大、
   false conflict 为 0，并有 Lean certificate/proof compiler 证据。蕴含图
   负责前两项的快速精确检查，remote smoke 负责证书可信度。

因此，蕴含图对 true 策略挖掘的价值主要体现在 current-exact residual 定位
和候选增量验证：它不替代 proof compiler，但显著提高了 true 策略选题效率
和合并可靠性。

对 false strategy mining，蕴含图的作用同样关键，但对象从 pair-index true
cache 变成 finite-model/source-target rectangles：

1. 快速重算 finite model 的 current-new false 覆盖。false setcheck 策略通常
   是“某个有限模型满足一批 source、反驳一批 target”，天然形成 source-target
   rectangle。蕴含图可以在当前 false/true 层上 preview 这个 rectangle 还能新
   增多少 false pair。
2. 检查 true 冲突。false candidate 即使 coverage 大，也必须确认不会打到当前
   true 层；`conflict_count = 0` 才能继续 smoke 或进入 merge review。
3. 区分主线包和 tail 包。比如本周 `mod17` accepted packet 还有约 `2.19M`
   graph-new false 覆盖，适合作为主线 revival；而 `non_affine_all4x4 full80`
   只剩约 `795k` current-new false 覆盖，应降级为 tail 或等待组合。
4. 防止重复挖旧模型。很多旧高分 affine/high-fin/all4x4 候选在当前图上已经
   graph-covered；蕴含图能把这些候选标成 stale/subsumed，避免继续消耗 remote
   smoke 和人工 review。
5. 指导 fresh false residual mining。当 tail pack 距离主线 gate 还差一段时，
   可以从 exact-unknown 层重新抽样，优先搜索仍未被 true/false 覆盖的区域，
   而不是继续扩大旧模型池。

所以 false 侧的总结是：蕴含图把 finite-model 挖掘从“模型看起来大”改成
“当前 exact false 增量大、true 冲突为 0、证书路径可过 judge”的闭环。

## math-distill-stage2-proofbench

### 100 题样本

`residual-100-v1`：

| 指标 | 数值 |
| --- | ---: |
| accepted | `94/100` |
| accepted rate | `94%` |
| true accepted | `79` |
| false accepted | `15` |
| remaining | `6` |

未解题：`0007`、`0012`、`0022`、`0040`、`0041`、`0049`。

### 1000 题样本

`residual-1000-v1` 创建于 2026-05-29，来源是 columnar graph exact-unknown
层。

| 指标 | 数值 |
| --- | ---: |
| accepted | `718/1000` |
| accepted rate | `71.8%` |
| true accepted | `651` |
| false accepted | `67` |
| remaining | `282` |

ledger 中 accepted 记录为 `719`，但按 problem id 去重后是 `718`。

### route kind 说明

`route kind` 是周报聚合口径，表示 accepted certificate 的生成路线类型；
它不是官方标签，也不是题目自带分类。底层 attempt route 很多，例如
`true:hinst_var`、`true:z3_proof_guided_explicit_fast_seed4`、
`false:pysat_finitefirst` 等。为了周报可读，将它们合并成 5 个大类。

| route kind | 含义 |
| --- | --- |
| `explicit_hinst_grind` | 显式生成一批 `h` 实例，然后交给 Lean `grind` 收尾 |
| `z3_guided_true_then_finite` | 先用 Z3/等式搜索引导 true proof，不行再转有限模型方向 |
| `shape_playbook` | 按 source/target 的 shape 套已知 proof/countermodel playbook |
| `direct_true` | 直接 true 证明，通常是短 rewrite、KB 或手写模板 |
| `finite_first` | 优先找 finite magma countermodel，生成 false certificate |

1000 题 accepted 按路线粗分：

| route kind | accepted |
| --- | ---: |
| `explicit_hinst_grind` | `316` |
| `z3_guided_true_then_finite` | `228` |
| `shape_playbook` | `103` |
| `direct_true` | `38` |
| `finite_first` | `33` |

1000 题 remaining 按路线粗分：

| route kind | remaining |
| --- | ---: |
| `z3_guided_true_then_finite` | `107` |
| `explicit_hinst_grind` | `88` |
| `finite_first` | `69` |
| `shape_playbook` | `12` |
| `direct_true` | `6` |

## 下周聚焦

1. true 侧继续用蕴含图 frontier/exact-unknown sample 定位高密度 true residual
   形状簇，再交给 proof compiler 或 Z3/prover guided workflow。
2. false 侧不要继续盲扩旧 affine/high-fin 候选；优先做 certificate-aware 的
   finite model search，或把已 accepted tail pack 合理批量化。
3. ProofBench 侧优先攻 `residual-100-v1` 剩余 6 题，同时用 1000 题剩余
   `282` 题做路线分层复盘。

## 依据文件

- `members/wubing/data/processed/order5_strategy_registry/coverage_summary.json`
- `docs/experiments/2026-05-29-high-roi-queue-revival-check.md`
- `members/wubing/docs/experiments/2026-05-29-order5-strategy-merge-review-queue.md`
- `../math-distill-stage2-proofbench/math-distill-stage2-proofbench/artifacts/proofbench_runs/20260526-accepted/summary.json`
- `../math-distill-stage2-proofbench/math-distill-stage2-proofbench/artifacts/proofbench_runs/20260529-residual1000-stage-summary.json`
