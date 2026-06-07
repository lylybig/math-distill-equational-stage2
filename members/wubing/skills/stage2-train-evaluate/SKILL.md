---
name: stage2-train-evaluate
description: Use when running a reproducible official Stage 2 Solo solver evaluation for this repository with official runner outputs and history-style artifacts.
---

# Stage2 Evaluate

Use this skill when the task is to run a single-file official Solo submission
directory against a Stage 2 problem set.
The expected output is a reproducible run directory under
`artifacts/runs/YYYY-MM-DD/<run-id>/` containing official runner results,
logs, `summary.json`, and `history.md`.

For standard runs, the source snapshot should come from
`solvers/solo_official/current/solver.py`, a draft, or a frozen version. Draft
or version evaluations should use a run-local submission directory such as
`artifacts/runs/YYYY-MM-DD/<run-id>/submission/solver.py`, with
`solver_snapshot.json` recording the source. Do not point the official runner at
a directory containing manifest files.

## When To Use

- The user wants to evaluate the current official Solo `solver.py`.
- The user wants to compare two solver submissions on the same problem set.
- The user wants the current standard order4 split metric run.
- The task is to reproduce a history-style result similar to the SAIR playground.

## Workflow

1. Read `references/stage2-shared-rules.md`.
2. Read `references/evaluator-defaults.md` when choosing suite, submission path, and output directory.
3. If LLM calls may be used, check the mass `gemma-4-31b` context note in `references/evaluator-defaults.md`; distinguish the model-card `256K` context from the current endpoint deployment limit.
4. For Lean certificate verification, use judge-v2 at `http://10.220.69.172:8890`; do not route certificate smoke through a legacy backend.
5. Confirm the submission directory contains only `solver.py`.
6. Confirm the submission solver hash matches the intended `current`, `draft`, or `version` snapshot.
7. Confirm the target `run_id` is fresh or intentionally reusable under the selected date directory.
8. Choose the scope:
   - fast order4 training metric:
     `--problem-set data/processed/order4_splits/dev_fast.jsonl`
   - main order4 training metric:
     `--problem-set data/processed/order4_splits/dev_main.jsonl`
   - full promotion gate after `dev_fast` and `dev_main` improve:
     `--problem-set data/processed/order4_splits/test_locked.jsonl`
   - focused stress splits:
     `--problem-set data/processed/order4_splits/stress_true.jsonl` or
     `--problem-set data/processed/order4_splits/stress_false.jsonl`
   - targeted regression: a failed subset problem file generated from a prior run
   Choose the runner shape:
   - certificate smoke: use `remote-http`/`remote-judge-v2` against
     `http://10.220.69.172:8890`; this validates emitted certificates through
     judge-v2 and creates judge-v2 `/jobs`.
   - serial/default compatibility: `scripts/evaluator/run_official_solo_history.py`
   - local diagnostic run: `scripts/evaluator/run_official_solo_history_parallel.py --max-workers N`
     when per-problem Solo isolation should be preserved but independent
     problems can be evaluated concurrently, only if the user explicitly asks
     to debug the local runner or remote service is unavailable.
9. Record the solver snapshot id, hash, selected remote base URL, and whether
   this is `current`, a `draft`, or a frozen `version`; for run-local
   submissions, verify `solver_snapshot.json`.
10. Run the selected official Solo history entrypoint with the selected
   `--submission`, problem set or suite, and `--run-id`.
11. Verify that the run directory contains:
   - `results/<problem_set>.json`
   - `logs/<problem_set>.log`
   - `summary.json`
   - `history.json`
   - `history.md`
   Parallel runs may additionally contain `parallel_shards/` and
   `parallel_logs/`; those are runner-local diagnostics and do not change the
   official Solo result JSON contract.
12. Report accepted count, failed/no-candidate count, judge calls, LLM calls,
   selected remote base URL, solver snapshot, and paths to artifacts. For
   parallel runs, distinguish
   runner `elapsedSeconds` from wall time: `elapsedSeconds` is aggregate
   per-problem solver elapsed time, not end-to-end wall time. When recording a
   promoted solver manifest, include explicit `wall_time_seconds` /
   `wall_time_text` when available.

## Hard Constraints

- Do not edit solver snapshots while using this skill.
- Do not modify generated result JSON or logs after the run.
- Keep write scope inside the requested `artifacts/runs/YYYY-MM-DD/<run-id>/` directory.
- Use the official Stage 2 runner/proxy path, not the removed prompt-evaluator flow.
- Treat the parallel history runner as an outer evaluation wrapper only: do
  not edit `solver.py`, the official external `pipeline/runner.py`, or the
  Solo protocol to get concurrency.
- Use order4 split JSONL files as the standard training/evaluation suite.
- Do not run an all-22M official judge sweep as part of routine training.
- Do not use local Docker/Lean for routine batch certificate verification; this
  workstation has limited resources. Use judge-v2 `:8890` for remote certificate
  checks unless the user explicitly asks to debug local runtime behavior.
- Prefer a failed subset run before rerunning `dev_main` or `test_locked` for a targeted draft.
- Full `test_locked` is allowed for score-bearing version freeze after
  `dev_fast` and `dev_main` improve; analyze aggregate metrics only and do not
  tune from individual locked failures.
