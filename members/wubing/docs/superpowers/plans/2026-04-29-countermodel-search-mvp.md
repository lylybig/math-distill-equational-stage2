# Countermodel Search MVP Implementation Plan（反模型搜索 MVP 实施计划）

> **For agentic workers（给后续 agentic worker）:** REQUIRED: Use superpowers:executing-plans to implement this plan if continuing in a separate session. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal（目标）:** Build the first finite magma countermodel searcher that can read uncovered negative rows and write reproducible search artifacts.

**Architecture（架构）:** Add a small evaluator/search module for finite magma tables. Add a CLI that joins `uncovered_negatives.jsonl` with the public problem index, searches small orders, and writes a run directory under `artifacts/runs/`.

**Tech Stack（技术栈）:** Python 3.10+, existing equation parser, JSONL helpers, pytest.

---

### Task 1: Finite Magma Evaluator（有限岩浆求值器）

**Files:**
- Create: `src/math_distill_stage2/countermodels.py`
- Create: `tests/test_countermodels.py`
- Create: `scripts/search_countermodels.py`
- Create: `docs/experiments/2026-04-29-countermodel-search-mvp.md`

- [x] **Step 1: Write failing tests（编写失败测试）**
  - Test equation evaluation over a left-projection magma.
  - Test that a search finds a size-2 countermodel for `x = x * y` not implying `x = y * x`.
  - Test that the CLI help runs by path.

- [x] **Step 2: Verify tests fail（确认测试失败）**
  - Run `pytest tests/test_countermodels.py -q`.
  - Expected: fail because `math_distill_stage2.countermodels` does not exist.

- [x] **Step 3: Implement minimal library and CLI（实现最小库和 CLI）**
  - Enumerate all operation tables up to `--max-order`.
  - For each negative problem, find the first table satisfying Eq1 and refuting Eq2.
  - Write `manifest.json`, `metrics.json`, `countermodels.jsonl`, and `unsolved.jsonl`.

- [x] **Step 4: Verify tests pass（确认测试通过）**
  - Run `pytest tests/test_countermodels.py -q`.

- [x] **Step 5: Run full test suite（运行完整测试）**
  - Run `pytest -q`.

- [x] **Step 6: Produce one real local run（生成一次真实本地运行）**
  - Run `python scripts/search_countermodels.py --max-order 2 --max-problems 20 --run-id 2026-04-29-000000-countermodel-search-mvp --created-at-utc 2026-04-29T00:00:00Z`.
  - Record results in `docs/experiments/`.
