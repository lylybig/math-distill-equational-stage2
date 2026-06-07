# Equation2921 Vampire singleton proof seed

## 目标

本记录是 `Equation2921` 的 bounded proof seed（有界证明种子），用于把
外部 Vampire `superpose` trace 转成 Stage 2 official judge 可验证的
Lean certificate（Lean 证书）。

## 选择原因

- 来源：`dev_fast` 剩余 true failures。
- `Equation2921` 在 `dev_fast` 中有 2 个失败样例：
  - `true_2921_512`
  - `true_2921_747`
- 旧 d1 targeted runner 中这两题各消耗约 9-10 次 judge call 后失败。
- `dev_main` 中也存在 `eq1_id=2921` true rows，因此这是可复用
  eq1-level singleton compiler 候选。

## 方程形状

`Equation2921`：

```text
x = ((y ◇ (x ◇ z)) ◇ x) ◇ z
```

外部 trace 给出的关键路线是：

```text
Equation2921 -> Equation890
```

其中 `Equation2921_implies_Equation890` 的 Vampire proof 内部已经导出
singleton：

```text
eq9  : (((X1 ◇ (X0 ◇ X2)) ◇ X0) ◇ X2) = X0
eq12 : ((X1 ◇ X2) ◇ X3) = X2
eq15 : ((X0 ◇ X2) ◇ X2) = X0
eq19 : X0 = X1
```

## 外部来源

- `external/equational_theories/equational_theories/Generated/VampireProven/Proofs7.lean`
  - line `941`
  - theorem：`Equation2921_implies_Equation890`
- `external/equational_theories/equational_theories/Superposition.lean`
  - `superpose` 是 elaborator（ elaboration 阶段生成证明项），不能直接作为
    Stage 2 certificate 依赖导入。

## Lean probe

先直接尝试：

```lean
have eq9 (X0 X1 X2 : G) :
    (((X1 ◇ (X0 ◇ X2)) ◇ X0) ◇ X2) = X0 := by
  exact Eq.symm (h X0 X1 X2)
grind
```

结果：official judge rejected，`grind` 不能直接从 `eq9` 推出 singleton。

随后在外部 Lean 仓库用 `#print` 展开：

```lean
exact superpose eq9 eq9
exact superpose eq12 eq9
```

并手工降级为只使用 `Eq.trans`、`Eq.symm`、`congrArg` 的证明项。

## Accepted certificate shape

核心证明：

```lean
have eq9 (X0 X1 X2 : G) :
    M (M (M X1 (M X0 X2)) X0) X2 = X0 := by
  exact S (h X0 X1 X2)
have eq12 (X1 X2 X3 : G) : M (M X1 X2) X3 = X2 := by
  have q :
      M (M (M X3 (M X1 (M X2 X3))) X1) (M X2 X3) = X1 :=
    eq9 X1 X3 (M X2 X3)
  have p :
      M (M (M (M (M X3 (M X1 (M X2 X3))) X1) (M X2 X3)) X2) X3 = X2 :=
    eq9 X2 (M (M X3 (M X1 (M X2 X3))) X1) X3
  exact T (S (congrArg (fun t => M (M t X2) X3) q)) p
have eq15 (X0 X2 : G) : M (M X0 X2) X2 = X0 := by
  have q : M (M X2 (M X0 X2)) X0 = M X0 X2 :=
    eq12 X2 (M X0 X2) X0
  have p : M (M (M X2 (M X0 X2)) X0) X2 = X0 :=
    eq9 X0 X2 X2
  exact T (S (congrArg (fun t => M t X2) q)) p
exact T (S (eq15 x y)) (eq12 x y y)
```

这里刻意使用 `T := @Eq.trans` 和 `M := @Magma.op`，因为
`try_magmaegg_singleton_compiler` wrapper 固定生成这两个 polymorphic let。
如果 proof body 不使用它们，Lean 会报：

```text
failed to infer universe levels in `let` declaration type
```

## Verification

直接 official judge probe：

- `true_2921_512`：accepted，axioms `()`
- `true_2921_747`：accepted，axioms `()`

focused test：

```text
tests/official/test_official_solo_submission.py::test_d16_solver_emits_eq2921_singleton_compiler_for_dev_fast_family
```

targeted official runner：

- run dir：`artifacts/runs/2026-05-11/official-draft-d1-eq2921-devfast2-fixed-chunk2`
- metrics：`2A / 0R / 0E`
- judge calls：`2`
- LLM calls：`0`

`dev_main` 同族 targeted runner：

- run dir：`artifacts/runs/2026-05-11/official-draft-d2-eq2921-devmain5-chunk5`
- metrics：`5A / 0R / 0E`
- judge calls：`5`
- LLM calls：`0`

`stress_true` 同族 targeted runner：

- run dir：`artifacts/runs/2026-05-11/official-draft-d2-eq2921-stresstrue1-c1`
- metrics：`1A / 0R / 0E`
- judge calls：`1`
- LLM calls：`0`

## 结论

`Equation2921` 是可进入 solver 的 eq1-level singleton strategy（单点坍缩策略），
已经落入 `solvers/solo_official/drafts/2026-05-11/d2/solver.py`。
下一步应在远端资源空闲后跑 d2 full `dev_fast`，预期相对 d1 再增加
`+2A`。
