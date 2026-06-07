---
name: stage2-train-improve-solver
description: Use when changing the official Stage 2 Solo solver.py to improve deterministic or LLM-assisted certificate generation while preserving the single-file submission contract.
---

# Stage2 Improve Solver

Use this skill when the task is to edit a draft official Solo `solver.py`
or its focused tests. The goal is to improve official judge accepted count
without relying on removed prompt-evaluator workflows.

Solver versions live outside the official submission directory under
`solvers/solo_official/{current,drafts,versions}`. The official submission
directory is only the runner mirror and must remain single-file.

## When To Use

- The user asks to improve the official `solver.py`.
- A previous official solver run identified failed problem ids to target.
- The task is to port a deterministic strategy from official `baseline`,
  `twophase`, or `opnorm`.
- The task is to add an LLM fallback after deterministic strategies.
- `stage2-train-offline-explore-solver` produced a candidate solver strategy from
  bounded offline exploration.

## Workflow

1. Read `references/solver-rules.md`.
2. Inspect `solvers/solo_official/current/solver.py`; if there is no narrow
   implementation candidate yet, use `stage2-train-offline-explore-solver` first.
3. Create or update a `solvers/solo_official/drafts/YYYY-MM-DD/dN/` snapshot
   with manifest notes before preserving an experimental change.
4. Write or update focused tests in `tests/official/test_official_solo_submission.py` first.
5. Keep `submissions/solo_official/` single-file: only `solver.py`.
6. Run focused tests.
7. Run targeted official single-problem checks first.
8. Run a failed subset or order4 split evidence through a run-local submission
   directory when the change is ready for a standard metric run:
   `dev_fast` for fast training signal, `dev_main` for main training signal,
   stress splits for class-specific pressure, and `test_locked` only as a
   promotion gate.
9. Hand draft promotion and rollback to `stage2-train-version-solver`; do not freeze
   versions from inside the improvement workflow.
10. Report accepted count deltas and remaining failed ids.

## Hard Constraints

- Do not add helper files inside `submissions/solo_official/`.
- Do not store version manifests or notes inside `submissions/solo_official/`.
- Keep `solver.py` under the official size cap.
- Do not require network for deterministic stages.
- Do not use a known-proof table as the default tactic for current small
  datasets or sample-only misses. Known proofs are a last-resort exception
  bank for a few high-value, official-judge-verified, hard-to-generalize
  cases after attempting a general proof generator or template repair; ask
  for explicit approval before adding new memorized proof entries.
- While mass zhangkang completion is unavailable, do not make LLM fallback part of the default expected score.
- Every emitted certificate must be validated by official judge, not by label matching.
