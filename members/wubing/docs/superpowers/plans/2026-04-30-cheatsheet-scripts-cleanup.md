# Cheatsheet And Scripts Cleanup Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize cheatsheets by dataset stage, clean script layout, and document the standard concurrency policy.

**Architecture:** Runtime cheatsheets live under dataset-stage directories such as `cheatsheets/mini/current/`, with English files used by evaluator and Chinese files used only for human review. Error analysis logic remains in `src/math_distill_stage2/error_analysis/`; scripts are thin command wrappers. Documentation records concurrency defaults: first-pass batch concurrency 32 and failed rerun concurrency 4.

**Tech Stack:** Python CLI wrappers, Markdown docs, JSON manifests, pytest.

---

### Task 1: Cheatsheet Directory Structure

**Files:**
- Move: `cheatsheets/current/*`
- Move: `cheatsheets/versions/*`
- Create: `cheatsheets/mini/current/manifest.json`
- Create: `cheatsheets/smoke/current/manifest.json`

- [x] Move current English and Chinese cheatsheets to `cheatsheets/mini/current/`.
- [x] Copy the same files to `cheatsheets/smoke/current/` as the smoke starting point.
- [x] Move accepted versions to `cheatsheets/mini/versions/`.
- [x] Add manifests that record current version, base version, dataset stage, and notes.

### Task 2: Script Cleanup

**Files:**
- Modify docs references to prefer `scripts/evaluation/`, `scripts/analysis/`, and `scripts/cheatsheets/`.
- Delete generated `scripts/__pycache__/`.

- [x] Remove generated Python cache files under `scripts/`.
- [x] Keep root command wrappers for compatibility.
- [x] Keep business logic in `src/`.

### Task 3: Docs And AGENTS

**Files:**
- Modify: `AGENTS.md`
- Modify: `docs/architecture.md`
- Modify: `docs/cheatsheet-optimization.md`
- Modify: `README.md`
- Modify: `docs/data-inventory.md`

- [x] Record concurrency policy: batch first pass 32, failed rerun 4.
- [x] Record new cheatsheet directory structure.
- [x] Remove stale root `cheatsheets/current/` references.

### Task 4: Tests

**Files:**
- Modify tests that assert default cheatsheet paths.

- [x] Update expected default path to `cheatsheets/mini/current/stage2_judge_json_certificate.en.md`.
- [x] Run targeted tests.
- [x] Run full `pytest -q`.
