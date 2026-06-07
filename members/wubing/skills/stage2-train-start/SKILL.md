---
name: stage2-train-start
description: Use when the user asks to start train, continue training, keep going autonomously, or run the Stage 2 Solo solver improvement loop without asking for next-step confirmation.
---

# Stage2 Start Train

Use this skill as the autonomy contract for a Stage 2 Solo solver iteration loop.
It coordinates existing project skills; it does not replace their detailed
rules.

## Default Objective

Improve the current official Solo solver on the fixed `order4_splits` training
evaluation ladder while keeping every candidate reproducible, judge-verified,
and rollback-friendly.

## Load Order

When this skill triggers, load the minimum relevant downstream skills:

1. `stage2-train-analyze-run` when choosing targets from prior runs.
2. `stage2-train-version-solver` when creating drafts, run-local submissions,
   manifests, promotions, or exports.
3. `stage2-train-offline-explore-solver` when remaining failures need bounded offline
   exploration before choosing the next solver change.
4. `stage2-train-proof-seed` when remaining true failures need proof trace
   clustering, single-problem Lean proof exploration, or reusable template
   seed records before editing `solver.py`.
5. `stage2-train-improve-solver` before editing any draft `solver.py` or focused
   solver tests.
6. `stage2-train-evaluate` before running targeted or order4 split evaluation.

Do not load `stage2-report-solver-baseline` from this loop. Reports and PDFs
are human-triggered communication work, not part of autonomous training.

## Skill Visibility

Intermediary updates should name the stage2 skills being used when it helps a
human confirm the workflow, especially before evaluation, solver edits,
promotion, or export. Keep this lightweight; do not force a skill-name prefix
into every update if it makes the message awkward or reduces clarity. Example:

`使用技能：stage2-train-start -> stage2-train-version-solver -> stage2-train-evaluate`

Keep the final report focused on results; it does not need to repeat the skill
chain unless that helps explain a decision.

## Autonomy Contract

Proceed without asking for "next step" confirmation when the action stays
inside this loop:

- create a new `solvers/solo_official/drafts/YYYY-MM-DD/dN/` draft
- write focused tests before changing `solver.py`
- edit draft-only `solver.py`
- run focused tests and targeted official evaluations
- run `data/processed/order4_splits/dev_fast.jsonl` with the project default
  parallel setting after focused evidence
- run `data/processed/order4_splits/dev_main.jsonl` when `dev_fast` evidence is
  positive and the change is broad enough
- run `data/processed/order4_splits/stress_true.jsonl` or
  `stress_false.jsonl` when the next target is clearly true-proof or
  false-countermodel coverage
- run the full `data/processed/order4_splits/test_locked.jsonl` only as a
  version promotion gate after both `dev_fast` and `dev_main` improve; inspect
  aggregate metrics only, and do not tune directly against individual locked
  failures
- update draft `manifest.json`, `notes.md`, and experiment summaries
- choose the next target from accepted-count deltas, failed ids, judge logs, or
  obvious regression evidence
- prepare bounded proof-seed records for selected true failures before choosing
  a deterministic proof-template edit
- promote an improved order4 split validated draft into the next
  `versions/YYYY-MM-DD/vN/` snapshot and update `current/`
- abandon or revert only the agent's own draft changes when tests or evaluation
  show no value

Stop and ask the user before:

- modifying `submissions/solo_official/solver.py`
- adding or expanding a known-proof table
- running marathon, large cloud jobs, paid/bulk API work, all-22M official judge
  sweeps, or unusually long evaluations outside the order4 split ladder; full
  `test_locked` is inside the ladder and may run automatically only under the
  promotion-gate condition above
- deleting files, resetting git state, or performing destructive operations
- choosing between two strategy paths with similar evidence but different
  strategic tradeoffs
- relying on uncertain competition rules or unofficial assumptions

## Loop

1. Orient from the newest validated run and latest draft notes.
2. Pick one narrow target: a failed true family, a false-counterexample gap, an
   LLM fallback setting, or a regression.
3. Create or continue a draft; never use `submissions/solo_official/` for
   routine iteration.
4. For solver changes, first add a focused test that fails for the current
   candidate.
5. Implement the smallest draft-only change that should move the target.
6. Run focused tests, then targeted official evaluation.
7. If targeted evidence is positive, run `dev_fast`; if that improves or
   clarifies a high-value class, run `dev_main` or the relevant stress split.
8. Record hash, bytes, commands, accepted/rejected/error counts, LLM calls,
   judge calls, wall time, fixed ids, and new failures.
9. If `dev_main` improves the current best accepted count/rate without
   regressing `dev_fast`, run the full `test_locked` promotion gate. Use only
   aggregate `test_locked` metrics for the promote/no-promote decision; do not
   inspect or tune individual locked failures. If `test_locked` confirms the
   gain and the solver stays within hard constraints, promote the draft automatically
   through `stage2-train-version-solver`; do not export to
   `submissions/solo_official/solver.py` unless the user asks for an official
   submission package.
10. Decide the next experiment from the evidence and continue until a stop
   condition is reached.

## Strategy Defaults

- Prefer deterministic certificate generation before LLM fallback changes.
- Prefer reusable proof templates over memorized known proofs.
- Use proof-seed clustering before adding another narrow deterministic compiler
  when the next target is unclear.
- Treat LLM round increases as experimental until targeted evidence shows net
  accepted-count value.
- Use the `stage2-train-evaluate` judge-v2 default for standard certificate
  batch
  evaluation. Do not plan local batch judge/evaluator runs unless the user
  explicitly asks to debug the local environment.
- Standard order4 split ladder:
  - `dev_fast`: fast smoke metric for every meaningful draft.
  - `dev_main`: main training metric for promising drafts.
  - `stress_true` / `stress_false`: focused class pressure tests.
  - `test_locked`: full promotion gate after `dev_fast` and `dev_main` improve;
    avoid per-id tuning.
- A draft is not score-bearing until it has standard evidence; focused tests
  and single-problem checks are only local validation.

## Completion Report

When pausing or reaching a stop condition, report:

- latest draft/version and solver hash
- best validated accepted/rejected/error counts
- what changed and which tests/evaluations ran
- fixed ids, new failures, and remaining high-value targets
- whether the next step can continue autonomously or needs user approval
