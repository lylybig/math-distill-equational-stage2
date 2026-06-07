---
name: stage2-train-version-solver
description: Use when managing the official Stage 2 Solo solver version lifecycle, including current, draft, version, promotion, rollback, or syncing a solver snapshot for evaluation.
---

# Stage2 Version Solver

Use this skill when the task is to manage solver snapshots under
`solvers/solo_official/`, generate a run-local submission copy, promote a
draft, or export a solver for final official submission.

## When To Use

- The user wants to create a solver draft from `current`.
- The user wants to evaluate a draft or frozen version.
- The user wants to promote a draft after order4 split evidence.
- The user wants to record or inspect current best solver state.
- The user wants to export a known version to `submissions/solo_official/`.

## Workflow

1. Read `references/solver-versioning-rules.md`.
2. Confirm `submissions/solo_official/` contains only `solver.py` if a final
   export is being touched; normal evaluation should not modify it.
3. Identify the intended source snapshot:
   - `solvers/solo_official/current/`
   - `solvers/solo_official/drafts/YYYY-MM-DD/dN/`
   - `solvers/solo_official/versions/YYYY-MM-DD/vN/`
4. Compute and record the solver hash and byte size.
5. For a new draft, copy `current/solver.py` into `drafts/YYYY-MM-DD/dN/solver.py`
   and write `manifest.json` plus `notes.md`.
6. For evaluation, create `artifacts/runs/YYYY-MM-DD/<run-id>/submission/solver.py`
   from the intended source snapshot and write `solver_snapshot.json`; then use
   `stage2-train-evaluate` with that run-local submission directory.
7. For promotion, require standard evidence first: failed subset for targeted
   checks, `dev_fast` and `dev_main` for training metrics, and the full
   `test_locked` split when freezing a score-bearing version. Use `test_locked`
   only as an aggregate promotion gate; do not tune against individual locked
   failures.
8. When `stage2-train-start` has an order4 split validated draft that improves
   the current best accepted count/rate and stays within hard constraints,
   promote without asking for another next-step confirmation.
9. Choose the next visible `vN` by inspecting existing frozen versions; do not
   restart numbering just because the date directory changed.
10. Promote by copying the accepted draft into `versions/YYYY-MM-DD/vN/`, writing
   `manifest.json` and `notes.md`, then updating `current/`.
11. Export to `submissions/solo_official/solver.py` only when preparing the final
   official submission package.

## Manifest Fields

At minimum, record:

- `schema`
- `created_date` or `updated_date`
- `status`
- `solver_path`
- `solver_sha256`
- `solver_bytes`
- source snapshot, such as `base_version` or `source_version`
- `label`
- evaluation evidence, including run dir, accepted count, accepted rate,
  rejected/errors, judge calls, LLM calls, aggregate problem elapsed time, and
  wall time when available. For parallel runs, do not treat runner
  `elapsedSeconds` as wall time; record explicit `wall_time_seconds` /
  `wall_time_text`.

## Hard Constraints

- Do not put `manifest.json`, `notes.md`, or any draft file in
  `submissions/solo_official/`.
- Do not use `submissions/solo_official/solver.py` for routine draft or version
  evaluation; use a run-local `submission/solver.py`.
- Do not overwrite existing versions.
- Do not promote a draft based only on a single-problem check.
- Do not modify official run result JSON or logs while recording version
  metadata.
- Keep `current/solver.py` aligned with the promoted version after promotion.
