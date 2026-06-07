# Stage 2 Workbench Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first reproducible Stage 2 workbench slice: docs, downloads, equation parser, and public-problem index.

**Architecture:** Keep raw public source snapshots immutable under `data/raw/`, implement focused Python utilities under `src/math_distill_stage2/`, and generate derived indexes under `data/processed/`. The first slice avoids Lean proof generation until the parser and dataset index are stable.

**Tech Stack:** Python 3.10, stdlib JSON/urllib/dataclasses, pytest.

---

## Chunk 1: Foundation And Documentation

### Task 1: Create Project Docs

**Files:**
- Create: `README.md`
- Create: `docs/competition-analysis.md`
- Create: `docs/sources.md`
- Create: `docs/week1-plan.md`
- Create: `memory/2026-04-27.md`

- [x] **Step 1: Write docs describing the Stage 2 solver strategy**
- [x] **Step 2: Record the corrected public data counts**
- [x] **Step 3: Record source URLs and download policy**

## Chunk 2: Parser And Dataset Utilities

### Task 2: Equation Parser

**Files:**
- Create: `tests/test_equations.py`
- Create: `src/math_distill_stage2/equations.py`

- [x] **Step 1: Write failing parser tests**
- [x] **Step 2: Run parser tests and verify they fail because code is missing**
- [x] **Step 3: Implement minimal parser/canonicalizer**
- [x] **Step 4: Run parser tests and verify they pass**

### Task 3: Dataset IO

**Files:**
- Create: `tests/test_dataset_io.py`
- Create: `src/math_distill_stage2/dataset_io.py`

- [x] **Step 1: Write failing JSONL/count validation tests**
- [x] **Step 2: Run tests and verify they fail because code is missing**
- [x] **Step 3: Implement minimal JSONL/count helpers**
- [x] **Step 4: Run tests and verify they pass**

## Chunk 3: Repeatable Scripts

### Task 4: Download Public Data

**Files:**
- Create: `scripts/download_public_data.py`
- Create: `tests/test_download_public_data.py`

- [x] **Step 1: Test expected config metadata and URL generation**
- [x] **Step 2: Implement downloader using bounded raw URLs**
- [x] **Step 3: Run downloader**
- [x] **Step 4: Verify row counts**

### Task 5: Build Public Problem Index

**Files:**
- Create: `scripts/build_problem_index.py`
- Create: `tests/test_build_problem_index.py`

- [x] **Step 1: Test indexing on temp JSONL fixtures**
- [x] **Step 2: Implement index builder**
- [x] **Step 3: Run index builder on downloaded data**
- [x] **Step 4: Verify processed index and summary**

### Task 6: ETP Result Index

**Files:**
- Create: `src/math_distill_stage2/etp_entries.py`
- Create: `scripts/build_etp_result_index.py`
- Create: `tests/test_etp_entries.py`

- [x] **Step 1: Write failing tests for extracting implication/fact rows**
- [x] **Step 2: Implement ETP entry extraction**
- [x] **Step 3: Run full test suite**
- [x] **Step 4: Build processed ETP result index**
