# Public Eval Harness MVP Implementation Plan（公开集实验编排器 MVP 实施计划）

> **For agentic workers（给后续 agentic worker）:** REQUIRED: Use superpowers:executing-plans to implement this plan if continuing in a separate session. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal（目标）:** Build the first reproducible public evaluation harness that writes run artifacts for the current Stage 2 public problem set. 构建第一版可复现的公开集实验编排器，为当前 Stage 2 公开问题集写出 run artifacts（运行产物）。

**Architecture（架构）:** Add a small library module that reuses existing coverage analysis and writes a timestamped run directory. Add a CLI wrapper under `scripts/` so future experiments have a stable command entrypoint. 新增一个小型库模块复用现有覆盖率分析，并写出带时间戳的 run 目录；同时在 `scripts/` 下新增 CLI 入口。

**Tech Stack（技术栈）:** Python 3.10+, existing JSONL helpers, pytest.

---

### Task 1: Public Eval Run Writer（公开集评测运行写入器）

**Files:**
- Create: `src/math_distill_stage2/public_eval.py`
- Create: `tests/test_public_eval.py`
- Create: `scripts/run_public_eval.py`
- Modify: `docs/architecture.md`
- Create: `docs/experiments/2026-04-29-public-eval-harness-mvp.md`

- [x] **Step 1: Write failing tests（编写失败测试）**
  - Test that a public eval run creates `manifest.json`, `metrics.json`, `errors.jsonl`, and `uncovered_negatives.jsonl`.
  - Test that the CLI help runs by path.

- [x] **Step 2: Verify tests fail（确认测试失败）**
  - Run `pytest tests/test_public_eval.py -q`.
  - Expected: fail because `math_distill_stage2.public_eval` does not exist.

- [x] **Step 3: Implement minimal library and CLI（实现最小库和 CLI）**
  - Reuse `analyze_public_coverage`, `ImplicationGraph`, and `FactIndex`.
  - Write machine artifacts under `artifacts/runs/<run_id>/`.
  - Keep the schema small and explicit.

- [x] **Step 4: Verify tests pass（确认测试通过）**
  - Run `pytest tests/test_public_eval.py -q`.

- [x] **Step 5: Run full test suite（运行完整测试）**
  - Run `pytest -q`.

- [x] **Step 6: Produce one real local run（生成一次真实本地运行）**
  - Run `python scripts/run_public_eval.py`.
  - Confirm the run directory contains metrics and uncovered negative rows.
