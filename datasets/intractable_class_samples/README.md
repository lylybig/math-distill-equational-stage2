# Intractable Class Samples

6 个按失败类拆分的 JSONL，作为团队**共享 test set** — 写新引擎时拿对应
`intractable_<CLASS>.jsonl` 跑回归。

来源：[`members/zhangkang/experiments/intractable_mining/`](../../members/zhangkang/experiments/intractable_mining/) 实验产物（no-closure-graph mining，1000 题 order ≤ 4 sampled，383 intractable）。
分类规则：见 [`docs/known_intractable.md`](../../docs/known_intractable.md) "## 失败类"。

## 文件

| 类 | 文件 | 题数 | 目标引擎 |
|---|---|---:|---|
| **V-vampire** | `intractable_V_vampire.jsonl` | 27 | Layer 4.6 Vampire trace decoder |
| **E-search**  | `intractable_E_search.jsonl`  | 13 | 同 V (短情形) |
| **B-brute**   | `intractable_B_brute.jsonl`   | 12 | RewriteHypothesisAndGoal extender |
| **R-rewrite** ★ | `intractable_R_rewrite.jsonl` | 80 | n-step rewrite chain engine (ROI #1) |
| **D-implicit** | `intractable_D_implicit.jsonl` | 197 | Layer 1.5 扩 closure_graph_v3 |
| **C-cex**     | `intractable_C_cex.jsonl`     | 54 | Layer 3.x twisting + cohomology |

总 383 题；总 468 KB；可直接进 git。

## Schema (每行)

```json
{
  "id": "mine_le4_<eq1>_<eq2>",
  "eq1_id": int, "eq2_id": int,
  "equation1": str, "equation2": str,
  "oracle_answer": true | false,
  "stages_tried": [{"stage", "ms", "hit", "judge_status?"}, ...],
  "class_v2": "V-vampire" | "E-search" | "B-brute" | "R-rewrite" | "D-implicit" | "C-cex",
  "class_v2_evidence": str,
  "etp_proof_path": "third_party/.../EquationN.lean" | null,
  "source": "force" | "sample",   // force=已知 sample_200/contest_1669 未解，sample=oracle 随机抽样
  "total_ms": int
}
```

## 用法约定

1. 写新引擎时拿对应类的 JSONL 做 test set
2. 目标 ≥ 80% solve rate 才能宣告"类 X 已 clear"
3. 引擎合入 main pipeline 后，重跑 [`exp_mine_order_le_4.sh full`](../../members/zhangkang/experiments/intractable_mining/experiments/exp_mine_order_le_4.sh) 自动 regenerate 这 6 个文件——已解题自动消失，**不要手工修 JSONL**
4. 若想只看"全图无偏估"的子集，filter `source == "sample"`（759 题来自 oracle 随机抽样，145 intractable）；force-include 是 sample_200 + contest_1669 已知未解，会偏 V-vampire / C-cex

## 不在本数据集的两类

| 类 | 处理 |
|---|---|
| **M-manual** (`ManuallyProved/` 33 个 Tao 等手工硬证) | 通用引擎不可解，承认 unsolved，不进 test set |
| **O-open** (190 条 ETP 自身 conjecture / unknown) | mining oracle 已 skip；如要专攻需另建数据集 |
