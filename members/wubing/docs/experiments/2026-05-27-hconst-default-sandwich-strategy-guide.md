# hconst-default-sandwich 策略说明

日期：2026-05-27

本文说明 `hconst_default_sandwich_match_collapse` 这一族 true proof-template 策略：

- 如何从 seed / residual 中发现这个策略；
- 如何判断一个 directed equation pair 是否符合该策略；
- Python compiler 如何生成证明模板和 Lean 代码；
- 如何做 exact scan、remote judge smoke、registry 合入和后续复核；
- 用一个真实 pair `41990 -> 42460` 贯穿说明。

相关代码入口：

- compiler：`src/math_distill_stage2/order5_opnorm_match_collapse.py`
- shape exact scan：`scripts/data/scan_order5_opnorm_hconst_shape_bucket.py`
- registry：`src/math_distill_stage2/order5_strategy_registry.py`
- remote smoke：`scripts/lean_certificates/verify_order5_paircheck_remote_smoke.py`

下文命令默认在 `members/wubing/` 目录执行。若从 monorepo 根目录执行，请把路径前面加上 `members/wubing/`。

## 1. 策略一句话

`hconst-default-sandwich` 是一个 true 证书生成模式：

```lean
target_lhs
  = intermediate1 := h ...
  = intermediate2 := hconst / congrArg ...
  = target_rhs    := h ... 或 (h ...).symm
```

其中：

- `h` 是题目给出的 source equation 的 Lean 假设。
- `hconst` 是从同一个 `h` 自动派生出的“某个表达式对某个变量不敏感”的常值性引理。
- `default` 表示 source 中未被 target 结构约束的变量，用 target 的第一个变量默认填充。
- `sandwich` 表示两端各用一次 `h`，中间夹一段 `hconst` 折叠。

它是快路径，不是完整搜索器。它牺牲一部分 completeness，换取可大规模 exact scan 的速度和稳定证书形状。

## 2. 发现过程

这个策略不是从纯理论先验直接写出来的，而是从 top residual true seed 中抽象出来的。

最早的 seed cluster 是 top16 true seed 里的两类：

- `plain_calc_match_collapse`
- `nested_congrArg_match_collapse`

先用较慢的 `hconst_sandwich` compiler 验证这些 seed 可被同一类证明模式覆盖。慢路径能覆盖 6 条 seed，但直接扩到 seed source / shape source 时耗时过高。

观察这些 seed 后得到两个快路径：

- `hconst-default-sandwich`：未约束 source 变量用 target 首变量填充，中间只允许 `hconst` 折叠。
- `hstep-default-sandwich`：同样默认填充，但中间允许普通 `h` 子项改写。这个能覆盖少量 `hconst-default` 覆盖不到的 seed，但更慢，目前不是主注册主线。

2026-05-21 的记录中，分层验证结果是：

| 范围 | compiler | union increment | conflict | smoke |
| --- | --- | ---: | ---: | --- |
| 6 seed source | hconst-default + hstep-default combined | 2,788 | 0 | 6/6 |
| 48 RHS role-signature source | hconst-default + hstep-default combined | 22,658 | 0 | 24/24 |
| full top16 source shape | hconst-default | 269,662 | 0 | 71/71 |

第一个正式 register batch 是：

```text
true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.top16_fullshape.v1
```

之后按 residual shape 继续扩张出 `d14vc4_multitarget`、`d13vc4_multitarget`、`lowvc_extension`、`topbucket_extension`、多轮 `postedge*` 等同族策略。

## 3. 数学形状

设 source equation 是：

```text
S_lhs = S_rhs
```

Lean 中进入 proof 后有：

```lean
intro G _ h
```

这里 `h` 的形状相当于：

```lean
h : forall source_vars, S_lhs = S_rhs
```

### 3.1 从 source 推出 hconst

如果某个 source 变量只出现在 RHS，不出现在 LHS，那么固定其他变量，改变这个变量不会改变 RHS。原因是 RHS 两次都等于同一个 LHS：

```lean
have hconst : forall other_vars a b, RHS[v := a] = RHS[v := b] :=
  fun other_vars a b => (h args_a).symm.trans (h args_b)
```

如果某个 source 变量只出现在 LHS，不出现在 RHS，则反过来：

```lean
have hconst : forall other_vars a b, LHS[v := a] = LHS[v := b] :=
  fun other_vars a b => (h args_a).trans (h args_b).symm
```

实现位置是 `build_constancy_info(...)`。它会为所有 lhs-only / rhs-only 变量构造候选 `hconst` 模板，并记录：

- `have_line`：Lean 的 `have hconst ...` 行；
- `lhs_template` / `rhs_template`；
- 对应的 op tree；
- 量化变量顺序 `quant_vars`。

### 3.2 default fill

当 target 左端或右端只匹配了 source 的一部分变量，source 里剩下变量没有被结构约束。普通慢搜索会尝试多个变量或子项填充，default-sandwich 只做一个选择：

```python
default_fill = target_vars[0]
```

例如 target variables 是 `x y z`，则所有缺失 source 变量默认填成 `x`。

这一步由 `_default_filled_subst(...)` 完成。

## 4. 如何判断一个 pair 是否符合策略

直接判断入口：

```python
matches_hconst_default_sandwich_match_collapse(
    source_equation,
    target_equation,
    max_candidates=64,
    max_constancy_steps=4,
)
```

证书生成入口：

```python
render_first_hconst_default_sandwich_match_collapse_certificate(
    source_equation,
    target_equation,
    max_candidates=64,
    max_constancy_steps=4,
)
```

它们都调用同一个 generator：

```python
iter_hconst_default_sandwich_match_collapse_proof_bodies(...)
```

判断流程如下。

### 4.1 解析输入

1. 把 `*` 统一替换成 Lean 证书使用的 `◇`。
2. target 必须能拆成 `target_lhs = target_rhs`。
3. target 必须至少有一个变量，因为 default fill 要取 `target_vars[0]`。
4. source 必须能拆成 `source_lhs = source_rhs`。
5. source 必须有变量。
6. 从 source 中构造至少一个 `hconst`；否则返回不匹配。

### 4.2 生成第一条 h edge

从 target 左端出发，尝试用 source 的一侧匹配它：

- 如果 `source_lhs` 能统一到 `target_lhs`，则把 source 未绑定变量 default-fill，实例化 `source_rhs` 得到 `intermediate1`，证明是 `h args`。
- 如果 `source_rhs` 能统一到 `target_lhs`，则实例化 `source_lhs` 得到 `intermediate1`，证明是 `(h args).symm`。

实现入口：

```python
_h_edges_from_target_expr_default_fill(...)
```

输出：

```python
(intermediate1_tree, first_args)
```

### 4.3 生成最后一条 h preimage edge

目标是找一个 `intermediate2`，它能通过一次 `h` 或反向 `h` 到达 `target_rhs`：

- 如果 `source_rhs` 能统一到 `target_rhs`，则 `intermediate2` 是对应实例化的 `source_lhs`，最后一步证明是 `h args`。
- 如果 `source_lhs` 能统一到 `target_rhs`，则 `intermediate2` 是对应实例化的 `source_rhs`，最后一步证明是 `(h args).symm`。

实现入口：

```python
_h_preimage_edges_to_target_expr_default_fill(...)
```

输出：

```python
(intermediate2_tree, final_args)
```

### 4.4 用 hconst 把 intermediate1 改成 intermediate2

对每一组 `(intermediate1, intermediate2)`，调用：

```python
find_constancy_steps(
    intermediate1_tree,
    intermediate2_tree,
    constancy_info,
    default_fill,
    max_steps=max_constancy_steps,
)
```

默认最多 4 步。每一步：

1. 先尝试把整棵当前树用某个 `hconst` 模板改成目标树。
2. 如果整棵树不行，就递归看左子树，再看右子树。
3. 找到一个子项改写后，更新当前树为目标树在该 path 上的子项。
4. 重复直到当前树等于 `intermediate2`。

每个 step 记录为：

```python
(path, hconst_args, symm, info_index)
```

- `path`：空字符串表示整棵树；`L/R` 序列表示子树路径。
- `hconst_args`：Lean 中调用 `hconst ...` 的参数。
- `symm`：是否反向使用该 hconst。
- `info_index`：使用哪一个派生出来的 hconst 模板。

### 4.5 生成 calc body

找到 steps 后，生成如下 proof body：

```lean
intro target_vars
have hconst : ...
calc target_lhs
  _ = intermediate1 := h ...
  _ = ... := congrArg ... (hconst ...)
  _ = target_rhs := h ... 或 (h ...).symm
```

如果 `hconst` 作用在子项上，会用 `wrap_congr_arg(...)` 自动包 `congrArg`。例如 path 是 `RR`，表示在右子树的右子树里改写，于是外层会包两层 `congrArg`。

最后由 `make_true_code(...)` 包成官方需要的完整 Lean 文件：

```lean
import JudgeProblem

def submission : Goal := by
  intro G _ h
  ...
```

## 5. 具体示例：pair 41990 -> 42460

这是 `top16_fullshape` batch 的代表 pair。

```text
eq1_id = 41990
source = x * y = y * (z * (y * (w * u)))

eq2_id = 42460
target = x * x = y * (x * ((x * x) * z))
```

运行：

```bash
PYTHONPATH=src uv run python - <<'PY'
from math_distill_stage2.order5_opnorm_match_collapse import (
    matches_hconst_default_sandwich_match_collapse,
    render_first_hconst_default_sandwich_match_collapse_certificate,
)

source = "x * y = y * (z * (y * (w * u)))"
target = "x * x = y * (x * ((x * x) * z))"

print(matches_hconst_default_sandwich_match_collapse(source, target, max_candidates=1))
print(render_first_hconst_default_sandwich_match_collapse_certificate(source, target, max_candidates=1))
PY
```

输出的第一行是：

```text
True
```

### 5.1 内部匹配状态

规范化后：

```text
source_lhs = x ◇ y
source_rhs = y ◇ (z ◇ (y ◇ (w ◇ u)))
source_vars = x y z w u
target_vars = x y z
default_fill = x
```

source 里：

- `x` 只出现在 LHS；
- `z w u` 只出现在 RHS。

compiler 会构造多个 `hconst` 候选。这个 pair 实际用到的是 lhs-only 变量 `x` 产生的引理：

```lean
have hconst : ∀ (y z w u a b : G), a ◇ y = b ◇ y :=
  fun y z w u a b => (h a y z w u).trans (h b y z w u).symm
```

第一条 h edge：

```text
target_lhs = x ◇ x
source_lhs = x ◇ y

match source_lhs to target_lhs:
  source x := x
  source y := x
  source z,w,u default-fill := x

intermediate1 = x ◇ (x ◇ (x ◇ (x ◇ x)))
proof        = h x x x x x
```

最后一条 h preimage edge：

```text
target_rhs = y ◇ (x ◇ ((x ◇ x) ◇ z))
source_lhs = x ◇ y

match source_lhs to target_rhs:
  source x := y
  source y := x ◇ ((x ◇ x) ◇ z)
  source z,w,u default-fill := x

intermediate2 =
  (x ◇ ((x ◇ x) ◇ z)) ◇
    (x ◇ ((x ◇ ((x ◇ x) ◇ z)) ◇ (x ◇ x)))
proof to target_rhs =
  (h y (x ◇ ((x ◇ x) ◇ z)) x x x).symm
```

中间的 hconst steps：

```text
step 1 path = RR
  把 intermediate1 的右-右子项从 x ◇ x
  改成 x ◇ ((x ◇ x) ◇ z)
  外层需要两层 congrArg

step 2 path = ""
  整棵树从上一步结果改成 intermediate2
```

### 5.2 生成的 Lean 证书

```lean
import JudgeProblem

def submission : Goal := by
  intro G _ h
  intro x y z
  have hconst : ∀ (y z w u a b : G), a ◇ y = b ◇ y := fun y z w u a b => (h a y z w u).trans (h b y z w u).symm
  calc x ◇ x
    _ = (x ◇ (x ◇ (x ◇ (x ◇ x)))) := h x x x x x
    _ = (x ◇ (x ◇ ((x ◇ ((x ◇ x) ◇ z)) ◇ (x ◇ x)))) := congrArg (x ◇ ·) (congrArg (x ◇ ·) ((hconst (x ◇ x) x x x x (x ◇ ((x ◇ x) ◇ z)))))
    _ = ((x ◇ ((x ◇ x) ◇ z)) ◇ (x ◇ ((x ◇ ((x ◇ x) ◇ z)) ◇ (x ◇ x)))) := (hconst (x ◇ ((x ◇ ((x ◇ x) ◇ z)) ◇ (x ◇ x))) x x x x (x ◇ ((x ◇ x) ◇ z)))
    _ = y ◇ (x ◇ ((x ◇ x) ◇ z)) := (h y (x ◇ ((x ◇ x) ◇ z)) x x x).symm
```

这段证书的结构和模板完全对应：

- 第 1 个 `calc` step：target 左端经 `h` 到 `intermediate1`。
- 第 2、3 个 `calc` step：用 `hconst` 把 `intermediate1` 改到 `intermediate2`。
- 最后一步：`intermediate2` 经反向 `h` 到 target 右端。

## 6. 如何做 shape exact scan

单个 pair 的 `matches_*` 只回答“这个 pair 是否命中”。要把策略扩成 registry batch，需要在 current residual 上做 shape exact scan。

使用脚本：

```bash
uv run python scripts/data/scan_order5_opnorm_hconst_shape_bucket.py \
  --compiler hconst-default-sandwich \
  --shape-bucket "roots=mul>mul|d=1>4|vc=5|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>4|vc=3|lm=0|rm=0|vs=0" \
  --coverage-profile data/processed/order5_strategy_registry/candidates/current_coverage_profile_v8_20260521.json \
  --coverage-summary data/processed/order5_strategy_registry/coverage_summary.json \
  --hits-output data/processed/order5_strategy_registry/candidates/my_hconst_default_sandwich_hits.jsonl \
  --summary-output data/processed/order5_strategy_registry/candidates/my_hconst_default_sandwich_summary.json \
  --workers 8
```

脚本做的事情：

1. 读取 `eq_size5.txt`，按 `equation_shape_bucket(...)` 建 source/target shape index。
2. 从 coverage profile 中取出当前 true/false 已覆盖目标，避免重复扫描已解决 pair。
3. 对选中 shape 的 current residual pair 跑 compiler matcher。
4. 记录每个命中 pair 的 `eq1_id`、`eq2_id`、`pair_index`、shape、stratum、proof_template。
5. 用 `explicit_hits_delta_from_profile(...)` 计算当前 profile 下的：
   - raw coverage；
   - same-verdict overlap；
   - opposite-verdict overlap；
   - conflict increment；
   - union increment；
   - total deterministic increment。
6. 输出 summary，并按阈值给出 `registry_status`：
   - `>= 1,000,000`：main candidate；
   - `>= 100,000`：tail candidate；
   - `< 100,000`：parking lot；
   - conflict 非 0：blocked。

如果只想调试少量 source，可加：

```bash
--source-ids 41990 --include-code-limit 5
```

这样 hits 前几条会带 `code` 和 `code_sha256`，方便人工审查证书形状。

## 7. 如何从 hits 进入 register 候选

exact scan 通过后，需要把 hits 固化成 pair-index cache。cache 是 registry 的实际覆盖规则，compiler 本身只负责按需生成证书。

常用步骤：

```bash
jq -r '.pair_index' data/processed/order5_strategy_registry/candidates/my_hconst_default_sandwich_hits.jsonl \
  | sort -n \
  | uniq \
  > data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_my_batch_pair_indexes_20260527.txt

shasum -a 256 data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_my_batch_pair_indexes_20260527.txt
```

register summary 至少需要记录：

- hits path；
- pair-index cache path；
- pair count；
- pair-index SHA256；
- coverage profile；
- delta against current profile；
- remote smoke input / results / summary；
- representative pairs；
- soundness status。

`top16_fullshape` 的 register summary 例子：

```json
{
  "pair_count": 269662,
  "delta_against_current_profile_v8": {
    "raw_coverage": 269662,
    "same_verdict_overlap": 0,
    "opposite_verdict_overlap": 0,
    "conflict_increment": 0,
    "union_increment": 269662,
    "total_deterministic_increment": 269662
  },
  "remote_smoke_status": "accepted_71_of_71",
  "pair_index_cache_sha256": "c2a582a3af265c76b6271d1af8c0d83ec811b44ad1c5b0d37d2229e2cdd26f20",
  "registry_status": "tail_register_ready_remote_smoke_passed",
  "soundness_status": "exact v8 current-residual pair-index set; conflict 0; representative remote smoke accepted 71/71"
}
```

## 8. 如何生成 remote smoke 输入

remote smoke 输入每行是一个 JSON object，包含：

```json
{
  "problem": {
    "id": "opnorm_hconst_default_sandwich_top16_41990_42460",
    "eq1_id": 41990,
    "eq2_id": 42460,
    "equation1": "x * y = y * (z * (y * (w * u)))",
    "equation2": "x * x = y * (x * ((x * x) * z))"
  },
  "answer": {
    "call": "judge",
    "verdict": "true",
    "code": "import JudgeProblem\n\n..."
  }
}
```

可以用 registry wrapper 生成 `answer`：

```python
from math_distill_stage2.order5_strategy_registry import (
    opnorm_hconst_default_sandwich_true_judge_answer,
)

answer = opnorm_hconst_default_sandwich_true_judge_answer(
    source_equation,
    target_equation,
)
```

一个最小 smoke input 生成片段：

```bash
PYTHONPATH=src uv run python - <<'PY'
import json
from pathlib import Path
from math_distill_stage2.order5_strategy_registry import (
    opnorm_hconst_default_sandwich_true_judge_answer,
)

hits_path = Path("data/processed/order5_strategy_registry/candidates/my_hconst_default_sandwich_hits.jsonl")
out_path = Path("data/processed/order5_strategy_registry/candidates/my_hconst_default_sandwich_smoke_input.jsonl")

rows = []
for line in hits_path.read_text(encoding="utf-8").splitlines():
    hit = json.loads(line)
    # 实际 batch 需要按 source/target/stratum/shape 分层抽样；这里仅示范前若干条。
    if len(rows) >= 20:
        break
    answer = opnorm_hconst_default_sandwich_true_judge_answer(
        hit["equation1"],
        hit["equation2"],
    )
    rows.append({
        "schema_version": 1,
        "eq1_id": hit["eq1_id"],
        "eq2_id": hit["eq2_id"],
        "pair_index": hit["pair_index"],
        "problem": {
            "id": f"hconst_default_sandwich_smoke_{hit['eq1_id']}_{hit['eq2_id']}",
            "eq1_id": hit["eq1_id"],
            "eq2_id": hit["eq2_id"],
            "equation1": hit["equation1"],
            "equation2": hit["equation2"],
        },
        "answer": {
            "call": "judge",
            **answer,
        },
    })

out_path.write_text(
    "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
    encoding="utf-8",
)
print(out_path, len(rows))
PY
```

注意：上面的 `answer` wrapper 返回 `{"verdict": "true", "code": ...}`，所以写入 remote smoke 时要补上 `"call": "judge"`。

## 9. 如何 remote judge

使用：

```bash
uv run python scripts/lean_certificates/verify_order5_paircheck_remote_smoke.py \
  --input data/processed/order5_strategy_registry/candidates/my_hconst_default_sandwich_smoke_input.jsonl \
  --output data/processed/order5_strategy_registry/candidates/my_hconst_default_sandwich_smoke_results.jsonl \
  --summary data/processed/order5_strategy_registry/candidates/my_hconst_default_sandwich_smoke_summary.json \
  --base-urls http://10.220.69.172:8888,http://10.220.69.153:8888 \
  --max-workers 16 \
  --run-id-prefix stage2-opnorm-hconst-default-sandwich-my-batch-smoke
```

脚本会：

1. 读取每行 `problem` 和 `answer`。
2. 调用 remote simple-api batch judge。
3. 把每条结果写入 output JSONL。
4. 输出 summary：`total_count`、`accepted_count`、`status_counts`、`error_code_counts`、remote backend 信息。
5. 如果不是全部 accepted，进程返回非 0。

`top16_fullshape` 的真实 smoke summary：

```json
{
  "total_count": 71,
  "accepted_count": 71,
  "status_counts": {"accepted": 71},
  "error_code_counts": {"": 71},
  "remote": {
    "base_url": "http://10.220.69.172:8888",
    "candidate_base_urls": [
      "http://10.220.69.172:8888",
      "http://10.220.69.153:8888"
    ],
    "max_workers": 16
  }
}
```

示例 pair `41990 -> 42460` 的 remote result 是 `accepted`，并返回：

```text
remote simple-api accepted certificate
```

## 10. 如何接入 registry

registry 接入分四层。

### 10.1 定义 strategy key 和默认路径

在 `order5_strategy_registry.py` 顶部添加：

```python
OPNORM_HCONST_DEFAULT_SANDWICH_MY_BATCH_STRATEGY_KEY = (
    "true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse."
    "my_batch"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_MY_BATCH_PAIR_INDEX_CACHE = Path(
    "data/processed/order5_strategy_registry/"
    "opnorm_hconst_default_sandwich_my_batch_pair_indexes_20260527.txt"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_MY_BATCH_REGISTER_SUMMARY = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_opnorm_hconst_default_sandwich_my_batch_register_pair_index_cache_20260527_summary.json"
)
```

### 10.2 加载 pair-index cache

参照 `_opnorm_hconst_default_sandwich_top16_pair_indexes(...)`：

- 读取 pair index；
- 校验能被 `pair_index_to_ids(...)` 解码；
- 去重；
- 对排序后的 pair index 计算 newline-sorted SHA256；
- 从 register summary 读 evidence；
- 返回 `frozenset(pair_indexes), evidence`。

### 10.3 构建 CoverageStrategy

参照 `_build_opnorm_hconst_default_sandwich_top16_strategy(...)`：

```python
CoverageStrategy(
    strategy_key=OPNORM_HCONST_DEFAULT_SANDWICH_MY_BATCH_STRATEGY_KEY,
    strategy_version=1,
    verdict=True,
    priority=...,
    coverage_rule=CompilerPairIndexesRule(
        pair_indexes=pair_indexes,
        law_count=int(evidence["law_count"]),
        compiler_name="opnorm_hconst_default_sandwich_match_collapse_my_batch",
    ),
    certificate_family="opnorm_hconst_default_sandwich_match_collapse",
    certificate_mode="proof_template",
    verification_mode="templatecheck+remote_smoke",
    coverage_rule_kind="compiler_pair_indexes",
    certificate_generator="opnorm_hconst_default_sandwich_match_collapse",
    evidence=evidence,
)
```

### 10.4 注册到默认 registry 和 pair lookup

`build_default_order5_strategy_registry(...)` 里只有在默认 `eq_size5` 且 pair-index cache 存在时才加载这类策略。

此外，`find_true_strategy_ids_for_pair(...)` 还有快速查询分支。它不会重新跑 compiler，而是：

1. 用 `ids_to_pair_index(eq1_id, eq2_id, law_count=...)` 得到 pair index；
2. 读取对应 batch 的 pair-index cache；
3. 判断 membership；
4. 返回 `strategy_key.v1`。

这意味着：

- registry coverage 以 pair-index cache 为准；
- certificate 仍由 compiler 按 pair 现场生成；
- 如果 compiler 逻辑改变，必须重新 smoke 代表 pair，必要时重扫 cache。

## 11. 验证清单

一个 batch 合入前，建议按下面顺序验证。

### 11.1 compiler 单元测试

已有 focused tests：

```bash
uv run pytest tests/order5_strategy_registry/test_opnorm_match_collapse.py -q
```

覆盖点包括：

- seed 是否能匹配；
- `matches_*` 和 `render_first_*` 是否一致；
- 生成的证书包含 `def submission : Goal := by`、`have hconst`、`calc`；
- 证书里不应出现 `sorry`、`admit`、`axiom`、`unsafe`；
- 证书中不保留 `*`，统一用 `◇`；
- registry wrapper 是否能生成 judge code。

### 11.2 candidate-layer exact scan

检查 summary：

- `compiler_hit_count > 0`；
- `sample_explicit_delta_summary.conflict_increment == 0`；
- `union_increment` 达到 register 阈值；
- `representative_pairs` 覆盖主要 stratum；
- `soundness_status` 是 deterministic compiler exact residual scan。

### 11.3 remote smoke

要求代表性 smoke 全 accepted。对 main batch 通常抽更多样本，按 source、target shape、stratum、top source hit count 分层抽样。历史 batch 记录例如：

- top16：71/71 accepted；
- d14vc4 multitarget：86/86 accepted；
- d13vc4 multitarget：90/90 accepted；
- postedge top40：120/120 accepted；
- postedge7 sample-hit top20 tail：120/120 accepted。

### 11.4 registry 复核

合入后跑：

```bash
uv run pytest tests/order5_strategy_registry/test_opnorm_match_collapse.py \
  tests/order5_strategy_registry/test_explicit_pairs_rule.py \
  tests/order5_strategy_registry/test_coverage_profile.py -q
```

如果更新了 registry summary / coverage summary，还要跑：

```bash
uv run python scripts/data/summarize_order5_strategy_coverage.py
```

并记录：

- strategy count；
- deterministic true covered；
- deterministic false covered；
- unresolved estimate；
- conflict count。

## 12. 常见误区和限制

1. pair 方向有意义。`eq1 -> eq2` 命中不代表 `eq2 -> eq1` 命中。
2. self pair 默认排除，pair space 使用 `ids_to_pair_index(..., include_self=False)`。
3. source 必须有 constancy variable，也就是有变量只在一侧出现；否则没有 `hconst` 可用。
4. default fill 固定用 target 首变量，因此需要其他变量或复合项填充的 pair 会漏掉。
5. `max_constancy_steps` 默认 4；超过 4 步的合法证明会漏掉。
6. `find_constancy_step` 是确定性贪心搜索，先整树，再左子树，再右子树；不是完整 rewrite search。
7. op tree 是语法树匹配，没有结合律、交换律、重排等归一化。
8. registry 的覆盖是 pair-index cache，不是每次在线跑 matcher。cache 一旦生成，就应通过 digest、summary 和 smoke 固化。
9. remote smoke 是代表性验证，不是对每个 pair 全量 Lean 验证。因此 candidate exact scan、conflict delta、cache digest、unit tests 共同构成证据链。

## 13. 最小复现脚本

下面脚本同时判断 pair、生成 Lean code，并可作为讨论时的最小复现：

```bash
PYTHONPATH=src uv run python - <<'PY'
from math_distill_stage2.order5_opnorm_match_collapse import (
    matches_hconst_default_sandwich_match_collapse,
    render_first_hconst_default_sandwich_match_collapse_certificate,
)

source = "x * y = y * (z * (y * (w * u)))"
target = "x * x = y * (x * ((x * x) * z))"

assert matches_hconst_default_sandwich_match_collapse(source, target, max_candidates=1)
code = render_first_hconst_default_sandwich_match_collapse_certificate(
    source,
    target,
    max_candidates=1,
)
assert code is not None
print(code)
PY
```

## 14. 读代码顺序建议

如果要改这个策略，建议按这个顺序读：

1. `build_constancy_info(...)`：理解 `hconst` 从哪里来。
2. `_h_edges_from_target_expr_default_fill(...)`：理解第一条 `h` edge。
3. `_h_preimage_edges_to_target_expr_default_fill(...)`：理解最后一条 `h` edge。
4. `find_constancy_steps(...)`：理解中间怎么用 hconst 折叠。
5. `iter_hconst_default_sandwich_match_collapse_proof_bodies(...)`：理解完整模板拼装。
6. `render_first_hconst_default_sandwich_match_collapse_certificate(...)`：理解 Lean 文件包装。
7. `scan_order5_opnorm_hconst_shape_bucket.py`：理解如何从单 pair 扩到 shape exact scan。
8. `order5_strategy_registry.py` 中的 `*_default_sandwich_*`：理解如何把 pair-index cache 变成 registry strategy。

