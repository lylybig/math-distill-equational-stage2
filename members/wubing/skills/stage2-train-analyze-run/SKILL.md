---
name: stage2-train-analyze-run
description: Use when an official Stage 2 Solo solver run already exists and the task is to summarize solved/failed patterns without changing original run records.
---

# Stage2 Analyze Run

Use this skill when the task starts from an existing official solver `run_dir`
and the next step is to understand failures before changing `solver.py`.

## When To Use

- The user has a completed official Solo run and wants accepted/failed breakdowns.
- The task is to identify false failures, true failures, LLM failures, or judge rejections.
- The next workflow step depends on selecting deterministic solver improvements.
- The run is over an order4 split such as `dev_fast`, `dev_main`,
  `stress_true`, `stress_false`, or `test_locked`.

## Workflow

1. Read `references/stage2-shared-rules.md`.
2. Confirm the target `run_dir` contains `results/*.json` and `summary.json`.
3. Compare results with the original problem set if labels are available.
4. Report:
   - total accepted / failed
   - accepted verdict distribution
   - failures by known `answer` label when available
   - order4 split name and whether it is training, stress, or locked-test evidence
   - judge calls and LLM calls
   - representative failed problem ids
5. Classify actionable failure categories when the raw result has enough evidence:
   - Lean compile error
   - Lean timeout
   - certificate rejected
   - LLM timeout
   - LLM malformed
   - true proof miss
   - false countermodel miss
6. Write or report a failed ids subset when the next step is targeted
   evaluation or draft selection.
7. For `test_locked`, summarize aggregate failure classes but do not recommend
   tuning against individual ids; use `dev_fast`, `dev_main`, and stress split
   failures for iteration targets.
8. Do not edit `solver.py` during analysis; use `stage2-train-improve-solver` for implementation and `stage2-train-version-solver` for snapshot lifecycle.

## Hard Constraints

- Do not edit official runner result JSON or logs.
- Do not rewrite Lean certificates in generated artifacts.
- Keep analysis outputs inside the target `run_dir` if new files are written.
- Prefer existing run artifacts over recomputing upstream evaluation steps.
- Do not treat the taxonomy as ground truth when the result only contains a generic judge rejection; mark those cases as needing certificate inspection.
