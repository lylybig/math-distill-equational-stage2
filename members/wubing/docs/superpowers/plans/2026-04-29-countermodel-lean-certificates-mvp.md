# Countermodel Lean Certificates MVP Implementation Plan（反模型 Lean 证书 MVP 实施计划）

> **For agentic workers（给后续 agentic worker）:** REQUIRED: Use superpowers:executing-plans to implement this plan if continuing in a separate session. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal（目标）:** Generate Lean `Fin n` counterexample certificates from `countermodels.jsonl` and verify a batch file locally.

**Architecture（架构）:** Extend the Lean certificate helper with table-driven finite magma certificates. Add a CLI that writes per-problem Lean files plus one combined `batch.lean` for local verification.

**Tech Stack（技术栈）:** Python 3.10+, Lean 4, ETP `equational_theories.Equations.All`, pytest.

---

### Task 1: Table-Driven Negative Certificates（表驱动负例证书）

**Files:**
- Modify: `src/math_distill_stage2/lean_certificates.py`
- Modify: `tests/test_lean_certificates.py`
- Create: `scripts/generate_countermodel_certificates.py`
- Create: `docs/experiments/2026-04-29-countermodel-lean-certificates-mvp.md`

- [x] **Step 1: Write failing tests（编写失败测试）**
  - Test table-driven certificate code for a size-2 left projection table.
  - Test invalid tables are rejected.
  - Test CLI help runs by path.

- [x] **Step 2: Verify tests fail（确认测试失败）**
  - Run `pytest tests/test_lean_certificates.py -q`.
  - Expected: fail because the new generator does not exist.

- [x] **Step 3: Implement generator and CLI（实现生成器和 CLI）**
  - Generate `let op : Fin n -> Fin n -> Fin n` from table entries.
  - Use `equational_theories.Equations.All` for arbitrary equation ids.
  - Write individual certificates and a combined `batch.lean`.

- [x] **Step 4: Verify tests pass（确认测试通过）**
  - Run `pytest tests/test_lean_certificates.py -q`.

- [x] **Step 5: Generate real certificates（生成真实证书）**
  - Run the generator on `artifacts/runs/2026-04-29/000001-countermodel-search-order2-full/countermodels.jsonl`.

- [x] **Step 6: Verify batch with Lean（用 Lean 验证 batch）**
  - Run `cd external/equational_theories && lake env lean ../../Math-Distill-Stage2/artifacts/runs/<run>/batch.lean` or an absolute path.

- [x] **Step 7: Run full regression（运行完整回归）**
  - Run `pytest -q`.
