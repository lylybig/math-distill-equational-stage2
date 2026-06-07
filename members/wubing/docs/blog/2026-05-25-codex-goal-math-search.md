---
layout: post
title: "和 Codex Goal 一起挖数学搜索空间：从 39 亿 pair 到 1.8 亿 residual"
date: 2026-05-25
description: "一次关于 goal-driven AI collaboration、Lean certificate 和大规模 solver engineering 的比赛复盘。"
tags:
  - AI for Math
  - Codex
  - Lean
  - Formal Verification
  - Competition Engineering
---

> 说明：这是一篇比赛进行期间可公开的技术文章草稿。文中保留方法论、协作体验和聚合数量级；刻意省略当前 solver 的 predicate、proof template、shape 白名单、策略顺序、内部 endpoint、prompt、脚本参数和未发布数据。

# 和 Codex Goal 一起挖数学搜索空间：从 39 亿 pair 到 1.8 亿 residual

最近我在参加 SAIR Foundation 的 [Mathematics Distillation Challenge: Equational Theories Stage 2](https://competition.sair.foundation/competitions/mathematics-distillation-challenge-equational-theories-stage2/overview)。

这个比赛研究的是 equational theories（等式理论），也就是代数结构中的等式蕴含问题。粗略地说，给定两个等式律 `E1` 和 `E2`，我们需要判断 `E1 => E2` 是否成立。Stage 2 的关键门槛在于：答案不能只是 true / false，而必须附带 Lean 4 可以验证的 certificate（证书）。真命题需要 proof（证明），假命题需要 counterexample（反例），最后由 deterministic Lean judge（确定性 Lean 评测器）接受或拒绝。

这改变了整个问题的性质。

如果没有形式化验证约束，我们可以把题目直接扔给大模型，让它给出判断和解释。但在 Stage 2 中，一个自然语言解释、一个看起来合理的推理草图、一个自信的 true / false 判断，都不是最终结果。只有 Lean judge 返回 accepted，才算真正解决。

所以我真正做的事情，并不是简单地问 GPT：

> 这个等式蕴含是否成立？

而是换成另一个问题：

> 在 Lean certificate 作为最终边界的前提下，能不能把 Codex 变成一个持续协作的数学搜索工程伙伴？

这篇文章想记录的就是这个过程：我如何通过 Codex 的 `goal` 功能，把零散对话变成长期探索，把一个约 39 亿 pair 的搜索空间，一步步推进到约 1.8 亿 hard residual（困难剩余集）。

## 这篇文章真正想讲什么

这不是一篇“我发现了某个神奇比赛解法”的文章。比赛仍在进行中，我不会公开当前 solver 的具体规则、模板、策略顺序或内部验证资源。

我更想讲的是一种工作方式：

> LLM 不一定要直接成为数学裁判。它可以成为形式化数学系统旁边那个高效、耐心、持续工作的协作者。

在这个项目里，Codex 的价值主要不在于一次性写出最终 Lean proof，而在于持续参与这些环节：

- 阅读失败样本和统计结果；
- 归纳 residual 的结构模式；
- 生成和重构分析脚本；
- 辅助设计 deterministic strategy（确定性策略）；
- 帮助维护 solver 版本和实验记录；
- 根据 Lean / judge 失败信息提出修复方向；
- 把零散观察整理成可验证的 pipeline（流水线）。

但所有结果最终都必须回到 Lean certificate。这条边界非常重要：LLM 可以提出候选，不能替代验证器。

## 从聊天助手到长期协作者

如果只是普通 chat，我通常会这样使用 AI：

> 帮我看一下这个日志。
> 帮我写个统计脚本。
> 这个失败样本有什么规律？
> 下一步该试什么？

这些都很有用，但每次都像一个孤立的小任务。

这个比赛里的工作不是单点问题，而是一个很长的链条：读数据、归并结构、挖掘模式、写脚本、跑验证、看失败、改策略、记录版本，然后继续下一轮。只靠一次次临时提问，很容易把上下文打散，也很容易忘记某个实验到底验证了什么。

后来我开始使用 Codex 的 `goal` 功能，把任务描述成一个持续目标：分析当前 residual，寻找新的 reduction（缩减）机会，验证候选策略，记录结果，再继续推进。

这个变化很明显。

Codex 不再只是回答我刚刚问的问题，而是围绕同一个目标持续工作。它会主动读取已有统计、比较 solver 版本、检查 registry（策略注册表）、写临时分析脚本、归纳失败原因、提出下一步实验，并在验证结果回来后继续调整方向。

我仍然控制边界和判断：什么可以进入正式 solver，什么只能作为候选，什么因为比赛保密不能公开。但大量中间推进不再需要我每一步手动拆解。

这带来了一种很强的协作快感。

不是“AI 替我完成了数学研究”的快感，而是另一种更工程化的快感：你把一个巨大、混乱、几乎不可下手的问题交给一个持续运转的协作者，然后看它一点点变成表格、脚本、证书、日志和下降的 residual count。

## 一个典型的 goal 循环

我们经常进行这样的循环：

```text
设定目标
  -> 读取当前 residual 和覆盖统计
  -> 找到一个大 bucket 或策略空白
  -> 写脚本做聚合分析
  -> 生成候选 rule / finite-model check / proof-template idea
  -> 跑 focused validation
  -> 汇总命中、冲突和失败原因
  -> 判断是否值得进入正式系统
  -> 继续寻找下一个机会
```

这个循环本身并不神秘。真正重要的是，它可以高频发生。

在这种协作模式下，`39 亿 pair -> 1.8 亿 residual` 不是一次灵光一闪，而是一串很小但可验证的进展：今天压掉一批重复结构，明天确认一个 false family，后天修正一个 proof template，再过一天发现某个统计口径有问题。

每一步都不一定惊艳，但每一步都能落盘、能复现、能被 judge 检验。

这和传统“问 AI 一个答案”的体验完全不同。更像是你和一个持续在线的研究助理一起在数学搜索空间里推进：它不替你决定最终数学真相，但它让观察、猜想、实现、验证、记录这个循环变得非常快。

## 39 亿为什么难

原始 pair 数量约为 39 亿。这个数字本身容易变成噱头，但真正困难的不是“大”，而是“大到如果没有结构化 accounting（核算体系），就根本不知道自己做对了什么”。

在这种规模下，最基本的问题都会变难：

- 某个策略到底新增覆盖了多少？
- 它是不是只覆盖了其他策略已经解决的部分？
- 它解决的是大 bucket，还是稀疏 long tail（长尾）？
- 它会不会引入 true / false 冲突？
- 它的 certificate 能不能被 Lean 稳定验证？

所以 pipeline 的第一目标不是证明，而是把空间变得可统计、可比较、可审计。

高层上，我把流程理解成：

```text
raw algebraic pairs
  -> canonicalization
  -> bucket / hash / metadata
  -> deterministic filters
  -> finite-model counterexample search
  -> proof-template attempts
  -> Lean / judge verification
  -> residual analysis
```

这里最重要的原则是：进入 accepted set 的结果必须有 certificate；留在 residual set 的对象，也要尽量知道它为什么还没被解决。

## 从 39 亿到 1.8 亿

经过多轮 canonicalization（规范化）、deterministic filtering（确定性过滤）、finite-model search（有限模型搜索）和 proof-template coverage（证明模板覆盖）后，原始约 39 亿 pair 被推进到约 1.8 亿 hard residual。

我觉得这个结果的意义不只是“数量变少了”。

更重要的是，剩下的 1.8 亿不是随机未解集合，而是经过强 baseline（基线系统）过滤后的 residual set。它们已经避开了一批便宜规则，没有被当前有限模型策略快速反驳，也没有落入已有 proof template。

换句话说，它们暴露的是当前 solver 的真实盲区。

这也是我觉得 residual 很有价值的原因。很多时候，我们喜欢展示 solved count；但在大规模形式化搜索中，residual 本身也是资产。它告诉你下一步该挖哪里，哪些结构还没有被解释，哪些方向可能值得发展成新的 benchmark（基准）。

## Codex 的价值在哪里

在这个项目里，Codex 最有价值的地方不是一次性写出某个 Lean proof。

它真正帮到我的，是把一个巨大、混乱、容易失控的探索过程维持成一个有节奏的闭环：

- 快速读懂脚本、日志和失败样本；
- 把临时观察变成可重复运行的统计；
- 生成候选实现，再交给 judge 验证；
- 帮助比较不同版本的覆盖增量；
- 把失败归因整理成下一轮策略；
- 在长时间探索中保持上下文和方向感。

这种协作的高效感很特别。

它不是“AI 替我完成了数学研究”，而是“AI 让研究工程循环跑得更快”。最终判断仍然来自 Lean certificate，但 Codex 显著缩短了从观察到实验、从实验到总结、从总结到下一步的距离。

我最喜欢的时刻，是一个模糊的想法被连续推进成可验证结果的过程：先看到某个 residual bucket 异常大，然后 Codex 帮我把样本拉出来、写统计、归纳结构、生成候选检查器，再把结果汇总成是否值得继续的判断。哪怕最后策略失败，它也会变成下一轮搜索的负样本，而不是一次浪费。

这就是 `goal` 模式最适合这类任务的地方：它把“帮我做一件事”变成“和我一起推进一个方向”。

## 为什么 verifier 边界很重要

LLM 的一个问题是，它很容易给出看起来合理但并不可靠的回答。形式化数学把这个问题放大了：一个 proof 只要有一个 hidden assumption（隐藏假设），一个 Lean 文件只要有一点依赖越界，就会被拒绝。

所以我不希望 Codex 直接成为裁判。

我更愿意把它放在 verifier（验证器）外围：

- Codex 负责提出候选；
- scripts 负责批量化和复现；
- solver 负责生成 certificate；
- Lean judge 负责最终接受或拒绝；
- residual analysis 负责解释失败并开启下一轮。

这种结构给了我一种很安心的速度感。Codex 可以大胆提出方向，但 accepted result 不能靠自信进入系统。它必须穿过 Lean certificate 这道门。

这也是这次协作最让我上头的地方：探索速度很快，但每个真正留下来的进展都很硬。

## 我希望读者带走什么

如果你也在做 AI for Math、formal methods（形式化方法）、LLM agent 或大规模搜索系统，我觉得这里有几个经验是通用的。

第一，把 LLM 放在 verifier 外围，而不是 verifier 位置上。LLM 可以提出候选、写代码、解释失败，但最终接受标准必须来自 Lean / judge。

第二，先让问题空间可统计，再谈求解。没有 canonicalization、bucket、hash 和 residual accounting，覆盖率很容易是错觉。

第三，把失败样本当成资产。大规模 residual 不是垃圾堆，而是下一轮 strategy mining（策略挖掘）的入口。

第四，长期目标比单次 prompt 更重要。Codex 的 `goal` 功能让我感觉最明显的一点是：当 AI 能围绕一个目标持续推进时，它从“问答工具”变成了“探索伙伴”。

第五，快感来自 verified progress（可验证进展）。在比赛工程里，最让人兴奋的不是模型说“我觉得对”，而是 judge 接受、统计下降、版本记录闭合，下一轮可以站在这个结果上继续往前走。

## 暂不公开的内容

由于比赛仍在进行中，本文刻意省略了所有可直接复刻当前 solver 的细节，包括：

- 具体 predicate；
- proof template；
- 策略顺序；
- shape 列表；
- 内部验证资源；
- prompt；
- 脚本参数；
- 未发布数据文件。

我希望这篇文章公开的是方法和体验，而不是比赛答案。

比赛结束后，如果条件合适，我会考虑把内部版本整理成更完整的 technical report（技术报告）：补充策略分类、覆盖统计、残差 taxonomy（分类法）、benchmark 设计，以及不同 LLM / symbolic baseline 的系统对比。

## 结语

从约 39 亿 pair 到约 1.8 亿 residual，这不是一个单纯的压缩数字。

对我来说，它更像是一次新的协作体验：人类负责设定目标和边界，Codex 负责持续推进探索和工程闭环，Lean judge 负责最终验证数学真相。

最有意思的地方也正在这里。

LLM 不一定要直接成为数学裁判。它可以成为形式化数学系统旁边那个高效、耐心、持续工作的协作者。

而当每一次进展都能被 certificate 验证时，这种协作不仅快，而且踏实。
