---
name: stage2-proofbank-generate-true-certificate
description: Use when Codex should synthesize Lean 4 true proof responses for Stage 2 proof bank prompt pack items or unsolved true implications.
---

# Stage2 Proofbank Generate True Certificate

Use the current Codex model to produce raw true proof responses for proof bank prompt pack items. The output is not accepted until `stage2-proofbank-verify-import` runs the official judge.

## Workflow

1. Read one prompt item from `artifacts/proof_bank_runs/YYYY-MM-DD/<source_run_id>/prompt_pack/`.
2. Inspect `## Skill-Guided Proof Instructions` and the item metadata. The prompt pack embeds the active skill guidance with source paths and sha256 hashes; treat those skill files as the proof-strategy source, not as decorative context.
3. If the item is a rejected-attempt repair candidate or references `lean-proof`, use the `lean-proof` skill before synthesizing the proof. Repair strategy should come from the skill guidance, not from a fixed prompt template.
4. If the item is a targeted singleton-seed gate (`source -> x = y`), focus on a reusable source-level singleton proof. It is fine for the body to start with target variables and derive `x = y`; do not broaden the response into a solver template or pair table.
5. Use any `## ETP Blueprint Context` only as a path/theorem-name hint for planning a self-contained proof; those theorem names are not available to import or call in the judge wrapper.
6. Synthesize a self-contained Lean proof body for the given implication.
7. Write exactly one JSON object to the item’s `raw_response_path`; do not use Markdown fences, surrounding commentary, or multiple JSON objects.
8. Re-read the file and confirm it is exactly one JSON object that will pass nightly raw response preflight.
9. Process at most 1-3 items per invocation.

Long-running workflows may invoke this skill repeatedly through `stage2-proofbank-nightly-loop`, but the per-invocation cap remains 1-3 prompt items so every generated proof has a nearby checkpoint and judge result.

## Output Shape

```json
{"verdict":"true","proof":"intro x y z\ncalc\n  x = x := rfl"}
```

The `proof` field is inserted after:

```lean
import JudgeProblem

def submission : Goal := by
  intro G _ h
  <proof>
```

## Hard Constraints

Do not edit `solver.py`. Do not call the judge. Do not modify the global bank, claim accepted, generate false counterexamples, import external theorems, use `sorry`, `admit`, `axiom`, `unsafe`, `congr_arg`, `*`, theorem headers, or `def submission`.

Use `◇` and `congrArg`.

Nightly preflight scans the full raw response text before judge/import/merge. Keep both `proof` and `notes` free of forbidden tokens, including `import` and `*`; use a short neutral stuck note such as `No short low-timeout proof found in this pass.` when needed.

## If Stuck

Still write a strict JSON raw response with `"verdict":"true"`, an empty `"proof":""`, and a short `notes` field. Do not leave the item unrecorded.
