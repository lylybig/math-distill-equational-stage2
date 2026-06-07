# d3 proofbank pattern cluster

## 背景

日期：2026-05-11

目标：在 d3 `h-instantiated grind` 大幅提升后，检查 proofbank 中已经由
Codex/GPT 生成并通过 official judge 的 true certificates，哪些已经被 d3
吸收，哪些仍可作为 d4 的 proof-seed（证明种子）。

## 输入

- solver：`solvers/solo_official/drafts/2026-05-11/d3/solver.py`
- solver hash：`ca6585bcb8a9e649377abf97f2bed795875982edaad6e8b0cb84fa8ff848e7a5`
- proofbank：`data/processed/proof_banks/gpt_true_certificates/`
- accepted certificates：`80`
- targeted problem set：
  `artifacts/tmp/2026-05-11-proofbank-accepted80-problems.jsonl`

## d3 targeted partial check

命令：

```bash
python scripts/evaluator/run_official_solo_history_parallel.py \
  --submission artifacts/submissions/solo_official_d3_hinst_grind \
  --problem-set /home/bing/.openclaw/workspace-fenshen-executor-agent/Math-Distill-Stage2/artifacts/tmp/2026-05-11-proofbank-accepted80-problems.jsonl \
  --run-id official-draft-d3-proofbank-accepted80-w8 \
  --max-workers 8 \
  --problems-per-shard 4
```

该辅助 run 在完成前 16 个 shards 后停止，避免本地长时间占用 Lean 资源。
已完成结果：

- result files：`16`
- rows：`60`
- d3 solved：`44`
- d3 failed：`16`

说明：这不是标准 split metric，只用于 proof-seed 选型。

## d3 仍未覆盖的 proofbank accepted ids

- `true_1065_3074`
- `true_1071_1875`
- `true_1074_939`
- `true_1087_2170`
- `true_1087_996`
- `true_1094_2992`
- `true_1182_1869`
- `true_1272_833`
- `true_1283_2449`
- `true_1363_838`
- `true_1553_2230`
- `true_1554_3380`
- `true_1556_4131`
- `true_2133_210`
- `true_2495_1204`
- `true_392_4366`

## Pattern clusters

### right-expansion / singleton proof-body cluster

Representative ids:

- `true_1065_3074`
- `true_1071_1875`
- `true_1272_833`

Common shape:

- derive an eq1-level lemma such as `∀ (x y : G), x = x ◇ y`
- close the target by repeated `.trans` applications
- proof uses `rw`, `Eq.trans`, `Eq.symm`, local `M := @Magma.op G _`, and
  a generated equality chain

Probe:

- Tried a generic lemma:
  `have grow : ∀ (a b : G), a = a ◇ b := by intro a b; grind`
- Official judge rejected on `true_1065_3074`; plain `grind` does not derive
  `grow` without a more specific proof chain.

Implication:

- This cluster likely needs either a reusable right-expansion proof generator
  or an eq1-level proof-body seed.
- Adding eq1-level proof bodies to a table would be a known-proof/seed table
  expansion and needs explicit approval before implementation.

### singleton from generated equality chain

Representative ids:

- `true_1074_939`
- `true_1094_2992`
- `true_1182_1869`
- `true_1283_2449`
- `true_1363_838`
- `true_1553_2230`
- `true_2133_210`

Common shape:

- derive `singleton : ∀ (x y : G), x = y`
- close target with `exact singleton ... ...`
- certificates are long proof terms with `T/S/R/M/C` helper aliases

Implication:

- These are high-value but not obviously reducible to the current d3
  `h-instantiated grind`.
- Candidate d4 path: proof-seed compiler for reusable singleton traces, but
  avoid broad pair-level known-proof tables.

### calc/congrArg theorem-chain cluster

Representative ids:

- `true_1087_2170`
- `true_1087_996`
- `true_1554_3380`
- `true_1556_4131`
- `true_392_4366`

Common shape:

- derive intermediate lemmas like `eq9`, `eq12`, `eq19`
- close with `calc` and `congrArg`
- sometimes `grind` proves intermediate theorem statements after earlier
  lemmas are introduced

Implication:

- This resembles existing MagmaEgg/Vampire singleton compiler work.
- Good d4 target if a repeated trace family appears in dev_fast/dev_main
  failures.

## Next action

Do not edit solver yet. Wait for d3 full `test_locked` aggregate result. If d3
passes the promotion gate, promote d3 first. Then choose d4 from the residual
proofbank clusters above, preferring a generic proof generator over any
known-proof table expansion.
