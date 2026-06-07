# Glossary

> 项目术语统一。新成员入职先读这页。

## ETP / Equational Theories Project

研究 magma (binary op) 等式公理之间蕴含关系的 Lean 4 项目。Stage 2 蒸馏赛道在
其基础上要求用 ≤ 32B 模型 + ≤ 500KB solver.py 复现尽量多的蕴含证明 / 反例。

上游：[teorth/equational_theories](https://github.com/teorth/equational_theories)，
本仓挂在 `third_party/equational_theories/`。

## 比赛官方仓

[SAIRcompetition/equational-theories-lean-stage2](https://github.com/SAIRcompetition/equational-theories-lean-stage2)，
挂在 `third_party/equational-theories-lean-stage2/`。judge 规则、sandbox policy、
提交格式都以这里为准。

## 全图 (Full graph)

ETP 4694 个方程之间的全部蕴含对 (~4694² ≈ 22M 有向对)。我们的真正目标。
1669 contest benchmark 是从全图采样的子集，**不是目标本身**。

## CSV oracle

ETP 官方发布的 ~8.7M 已知答案 (10K explicit_true + 8M implicit_true + 587K explicit_false)。
用于评估 solver 输出是否正确。

## closure graph

src→dst 蕴含的有向图。BFS 求可达即可证 TRUE。v3 版本 8884 条边。

## superpose / subsumption / mod_symm

ETP `equational_theories.Superposition` 里的 Lean meta elaborator。
~200 行 elab 代码。sandbox 不允许 elab/macro，所以我们必须**模拟**或**翻译为纯 term**。

## tactic_sweep

我们的 Stage 4：对常见 tactic (`grind` / `simp` / `aesop` 各种变体) +
h-instantiations 做 ~22 种组合扫描。

## superposition simulator

Stage 4.5：在纯 Lean 里手工模拟 superposition calculus 的几步实例化 + grind。
浅层版本已实装，深层 (~9 步) 待 Layer 4.6。

## paper §-name vs local nickname

反例族**只用 paper §-name**：
- `finite-sec` (§3.1 + §3.8)
- `linear-sec` (§3.2)
- `cyclic-sec` (§3.3)
- `twisting-sec` (§2.3.10 / §3.4)
- `cohomology-sec` (§2.3.12 / §3.6)

不要用 `Brockian` / `Ray` / `EULER` 这种历史昵称，没有论文 traceability。

## Class A / B / C

已知难题三大类。详见 [known_intractable.md](known_intractable.md)。

## TIER 1 / 2 / 3

评估分层：
- TIER 1: closure + brute Fin + cex (廉价, ~10 min on 1669)
- TIER 2: tactic_sweep + superposition (中等)
- TIER 3: invertibility + LLM + 高级反例族 (慢)
