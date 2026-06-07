# v11 h-instantiated grind proof generator

## 背景

- 冻结日期：2026-05-12
- 来源 draft：`solvers/solo_official/drafts/2026-05-11/d3`
- base version：`2026-05-09/v10`
- solver hash：`ca6585bcb8a9e649377abf97f2bed795875982edaad6e8b0cb84fa8ff848e7a5`
- solver size：`259195` bytes

v11 将 d3 的 `h-instantiated grind` 策略冻结为当前 best snapshot。该策略针对
`eq1` 左边是单变量的 true 问题，从目标变量、目标 compound subterms（复合子项）
和当前方程语法生成 `h` 的若干实例化，然后交给 `grind` 收尾。

这不是 pair-level known-proof table（题目对题目的已知证明表）：solver 运行时不读取
proofbank 文件，也不按 `eq1_id/eq2_id` 直接分支。

## 关键变更

- 新增 `try_hinstantiated_grind_proof`。
- 该策略接在 bare `grind` 后，重型 deterministic compilers 之前。
- `MAX_LLM_ROUNDS` 保持 `0`，没有 runtime LLM 依赖。

## 验证

Focused tests：

```bash
pytest tests/official/test_official_solo_submission.py::test_d17_solver_emits_hinstantiated_grind_for_proofbank_true_samples -q
pytest tests/official/test_official_solo_submission.py -q
```

结果：

- `1 passed in 65.01s`
- `27 passed in 283.02s`

Targeted official evidence：

- run id：`official-draft-d3-hinst-grind-targeted-w2`
- metrics：`6A / 0R / 0E`
- LLM calls：`0`

Remote `dev_fast`：

- run id：`remote-d3-hinst-grind-dev-fast-w24-c50-20260511-223747`
- metrics：`1861A / 139R / 0E`
- delta vs v10 dev_fast (`1648A / 352R / 0E`)：`+213A`

Remote `dev_main`：

- run id：`remote-d3-hinst-grind-dev-main-w24-c20-20260511-175532`
- metrics：`9293A / 707R / 0E`
- delta vs v10 dev_main (`8227A / 1773R / 0E`)：`+1066A`

Full `test_locked` promotion gate：

- run id：`remote-d3-hinst-grind-test-locked-w24-c50-20260511-230311`
- metrics：`46331A / 3669R / 0E`
- accepted verdicts：`false=24968`, `true=21363`
- judge calls：`93038`
- LLM calls：`0`
- returncode：`0`
- delta vs v10 full `test_locked` (`40971A / 9029R / 0E`)：`+5360A`

## 状态

`2026-05-12/v11` 已同步到 `solvers/solo_official/current/`。没有导出到
`submissions/solo_official/solver.py`。
