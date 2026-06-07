# Known Intractable Problems

> 已尝试且当前工具能力下解不动的题。**先归类，再考虑是否值得专攻**。

## 分类规则

每条记录至少包含：
- 题号或 (src, dst)
- 已尝试的 stage
- 失败原因
- 归属 Class (A / B / C / D=其他)
- 是否值得专攻 (yes / no / wait-for-stronger-llm)

## Class A — VampireProven 类

ETP 用 `superpose` / `subsumption` / `mod_symm` 自定义 elaborator (200 行 Lean meta)。
sandbox 没这些 + policy 禁 `elab/macro`，搬不动。

| 题号 | 已试 | 备注 |
|---|---|---|
| (待录入) | | |

**通用解决方案**: Layer 4.6 Vampire trace decoder (待实现, ~500 LOC)

## Class B — Meta-closure auxiliary lemma 类

ETP 走"沿闭包图链推出辅助引理 `eq_aux`，nth_rewrite goal，apply h"。
我们的 BFS 只查 src→dst 直链，不会主动找 useful auxiliary。

| 题号 | 已试 | 备注 |
|---|---|---|
| (待录入) | | |

**通用解决方案**: Layer 3.6 meta-closure tactic-aware 重做

## Class C — Cohomology / twisting FALSE 类

paper §3.4 / §3.6 (ii) 的代数构造。当前 cex 引擎只到 §3.1-§3.3 + §3.8 基础族。

| 题号 | 已试 | 备注 |
|---|---|---|
| (待录入) | | |

**通用解决方案**: Layer 3.x §2.3.10 twisting + §2.3.12 cohomology

## Class D — 真正孤例（无类可归）

只有在确认**该题无任何同类规律可总结**时才进入这一类。能进 Class A/B/C 优先归到那里。

| 题号 | 原因 | 是否值得 hardcoded |
|---|---|---|
| (待录入) | | no by default |
