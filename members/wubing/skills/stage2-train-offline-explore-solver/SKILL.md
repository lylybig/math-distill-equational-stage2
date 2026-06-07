---
name: stage2-train-offline-explore-solver
description: Use when offline exploring remaining Stage 2 Solo solver failures to choose a solver improvement direction before editing solver.py or launching another run.
---

# Stage2 Train Offline Explore Solver

Use this skill for bounded offline exploration that decides the next candidate
solver strategy. It sits between run analysis and implementation: it studies
remaining failures, tries cheap probes, and turns findings into an actionable
solver improvement direction.

## When To Use

- A completed run leaves remaining failures and the next implementation target
  is unclear.
- Existing deterministic templates, LLM fallback behavior, or external proof
  traces need quick feasibility checks before editing `solver.py`.
- Remaining true failures need proof-seed clustering before selecting a narrow
  deterministic template candidate.
- The training loop needs to classify whether the next move is a deterministic
  tweak, a proof-template repair, an LLM prompt/round experiment, or a larger
  strategy fork.

## Workflow

1. Start from `stage2-train-analyze-run` output, run summary, remaining failures,
   and latest draft notes.
2. Pick a small representative subset; avoid rerunning the whole suite for
   exploration.
3. Run bounded probes only: official judge smoke tests, small tactic variants,
   short proof-search experiments, external proof-source inspection, or
   targeted log comparison.
   Use `stage2-train-proof-seed` when the probe needs trace clustering,
   single-problem Lean proof exploration, or offline LLM proof translation.
4. Keep every probe reproducible: record command, input ids, timeout, accepted
   ids, rejected ids, and why the result changes the candidate solver strategy.
5. Write findings into draft `notes.md`, manifest analysis fields, or a
   human-readable experiment note; do not edit official run result JSON.
6. Hand implementation to `stage2-train-improve-solver` only after there is a
   narrow strategy with a focused test target.

## Hard Constraints

- Do not edit `solver.py`; this skill explores direction only.
- Do not promote, export, or modify `submissions/solo_official/`.
- Do not add or expand a known-proof table during exploration. If a proof looks
  memorized but valuable, report it as a possible exception requiring explicit
  approval.
- Do not run marathon, cloud, paid, bulk, or unusually long jobs.
- Kill probes that exceed their intended bound, and report the timeout as a
  finding rather than letting exploration become an unbounded run.

## Output

Report:

- stage2 skills used in intermediary updates when useful for human traceability
- remaining failures or subset inspected
- bounded probes run and their limits
- accepted/rejected/error deltas, if any
- candidate solver strategy, expected blast radius, and next focused test
