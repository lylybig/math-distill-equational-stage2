# Stage 2 Solver-First Refactor Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Move the project mainline from cheatsheet iteration to official Solo `solver.py` iteration.

**Architecture:** Keep official judge and official runner wrappers as the evaluation spine. Delete cheatsheet workflow files and update documentation/skills so future work targets `submissions/solo_official/solver.py`. Improve deterministic coverage first by importing the official baseline singleton proof strategy.

**Tech Stack:** Python 3, official SAIR Stage 2 `pipeline.runner`, Lean 4 `v4.30.0-rc2`, Docker official judge image, pytest.

---

## Task 1: Remove Cheatsheet Workflow Surface

**Files:**
- Delete: `cheatsheets/`
- Delete: `scripts/cheatsheets/`
- Delete: `src/math_distill_stage2/cheatsheets/`
- Delete: `skills/stage2-optimize-cheatsheet/`
- Delete: `skills/stage2-version-cheatsheet/`
- Delete: `docs/cheatsheet-optimization.md`
- Modify: `AGENTS.md`
- Modify: `docs/README.md`
- Modify: `scripts/README.md`
- Test: `tests/test_stage2_skills.py`
- Test: `tests/test_cheatsheet_drafts.py`
- Test: `tests/test_cheatsheet_versions.py`

- [x] **Step 1: Inspect references**

Run:
```bash
rg -n "cheatsheet|stage2-optimize-cheatsheet|stage2-version-cheatsheet" AGENTS.md README.md docs scripts src tests skills
```

- [x] **Step 2: Delete workflow directories**

Use `rm -r` only for the directories listed above. Do not remove `artifacts/runs/` history.

- [x] **Step 3: Update tests**

Remove tests whose only purpose is cheatsheet draft/version behavior. Update `tests/test_stage2_skills.py` so it expects solver-oriented skills only.

- [x] **Step 4: Run focused deletion tests**

Run:
```bash
pytest tests/test_stage2_skills.py -q
```

Expected: pass.

## Task 2: Make Official Solver Evaluation the Default Entry

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Modify: `docs/data-inventory.md`
- Modify: `scripts/README.md`
- Keep: `scripts/evaluator/run_official_solo_history.py`
- Keep: `src/math_distill_stage2/official_stage2_history.py`
- Test: `tests/test_official_stage2_history.py`

- [x] **Step 1: Rewrite README first commands**

Default commands should be:
```bash
python scripts/evaluator/run_official_solo_history.py --suite sample20 --run-id <run-id>
python scripts/evaluator/run_official_solo_history.py --suite sample200 --run-id <run-id>
pytest tests/test_official_solo_submission.py tests/test_official_stage2_history.py -q
```

- [x] **Step 2: Rewrite architecture**

Make `submissions/solo_official/solver.py` the first-class artifact. Move old LLM-output-as-certificate text to removed/legacy status.

- [x] **Step 3: Update inventories**

Remove cheatsheet inventory rows. Add solver submission, official history runner, official judge batch verifier, and Docker image rows.

- [x] **Step 4: Run doc-linked focused tests**

Run:
```bash
pytest tests/test_official_stage2_history.py -q
```

Expected: pass.

## Task 3: Replace Project Skills with Solver-Oriented Skills

**Files:**
- Keep/modify: `skills/stage2-evaluate/`
- Keep/modify: `skills/stage2-analyze-run/`
- Keep: `skills/stage2-info-competition/`
- Delete: `skills/stage2-optimize-cheatsheet/`
- Delete: `skills/stage2-version-cheatsheet/`
- Test: `tests/test_stage2_skills.py`

- [x] **Step 1: Rename skill descriptions conceptually**

`stage2-evaluate` should mean “run official solver evaluation”, not “run cheatsheet evaluator”.

- [x] **Step 2: Update references**

References should mention official runner outputs:
`results/<problem_set>.json`, `logs/<problem_set>.log`, `summary.json`, `history.md`.

- [x] **Step 3: Add solver improvement guidance**

If adding a new skill is useful, create `skills/stage2-improve-solver/` with rules:
only edit `submissions/solo_official/solver.py`, maintain single-file size, run official sample tests.

- [x] **Step 4: Validate skills**

Run:
```bash
pytest tests/test_stage2_skills.py -q
```

Expected: pass.

## Task 4: Import Baseline Singleton Proof Strategy

**Files:**
- Modify: `submissions/solo_official/solver.py`
- Modify: `tests/test_official_solo_submission.py`

- [x] **Step 1: Write failing test for singleton true proof**

Use one known baseline-only solved true sample such as `true_193_191`. The test should assert the solver's first judge call is `verdict=true` and contains singleton proof structure.

- [x] **Step 2: Verify red**

Run:
```bash
pytest tests/test_official_solo_submission.py::test_solver_emits_singleton_true_judge_call -q
```

Expected: fail because current solver does not emit this proof.

- [x] **Step 3: Implement minimal singleton strategy**

Port the official baseline logic, but normalize equation text for official `◇`.

- [x] **Step 4: Verify green**

Run:
```bash
pytest tests/test_official_solo_submission.py -q
```

Expected: pass.

- [x] **Step 5: Official smoke**

Run:
```bash
python scripts/evaluator/run_official_solo_history.py --suite sample20 --run-id <run-id>
```

Expected: accepted count stays at least current level and may improve.

## Task 5: Run Sample 200 Regression

**Files:**
- Write artifacts under: `artifacts/runs/YYYY-MM-DD/<run-id>/`

- [x] **Step 1: Run official sample200**

Run:
```bash
python scripts/evaluator/run_official_solo_history.py --suite sample200 --run-id <run-id>
```

Expected: accepted count approximately `111/200` after singleton import.

- [x] **Step 2: Compare with previous runs**

Compare against:
- `artifacts/runs/2026-05-06/official-solo-sample200/summary.json`
- `artifacts/runs/2026-05-06/official-baseline-sample200-no-api/summary.json`

- [x] **Step 3: Report remaining gaps**

List false failures and true failures separately. LLM failures should not be treated as regression while mass endpoint is unavailable.

## Task 6: Final Verification

**Files:**
- Verify all changed docs, solver, official wrappers, and tests.

- [x] **Step 1: Run focused tests**

Run:
```bash
pytest tests/test_official_solo_submission.py tests/test_official_stage2_history.py tests/test_official_stage2_judge.py tests/test_official_stage2_docker_batch.py tests/test_stage2_skills.py -q
```

- [x] **Step 2: Check remaining cheatsheet references**

Run:
```bash
rg -n "cheatsheet|stage2-optimize-cheatsheet|stage2-version-cheatsheet" README.md AGENTS.md docs scripts src tests skills
```

Expected: no mainline references; historical experiment records may remain only if explicitly marked historical.

- [x] **Step 3: Check submission layout**

Run:
```bash
find submissions/solo_official -maxdepth 1 -mindepth 1 -print
```

Expected: only `submissions/solo_official/solver.py`.
