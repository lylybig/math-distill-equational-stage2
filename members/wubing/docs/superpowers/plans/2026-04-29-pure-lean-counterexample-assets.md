# Pure Lean Counterexample Assets Implementation Plan（纯 Lean 反例资产实施计划）

> **For agentic workers（给后续 agentic worker）:** REQUIRED: Use superpowers:executing-plans to implement this plan if continuing in a separate session. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal（目标）:** Export verified counterexamples into a global dataset-style asset tree with one problem folder per `eq1-<id>-eq2-<id>` and pure Lean 4 certificates.

**Architecture（架构）:** Keep `artifacts/runs/` as experiment history. Add `data/assets/counterexamples/` as durable assets. Generate pure Lean certificates with no imports by inlining `Magma`, both equation definitions, and the finite magma table.

**Tech Stack（技术栈）:** Python 3.10+, Lean 4 core only, pytest.

---

### Task 1: Pure Lean Certificate Generator（纯 Lean 证书生成器）

**Files:**
- Modify: `src/math_distill_stage2/lean_certificates.py`
- Modify: `tests/test_lean_certificates.py`

- [ ] **Step 1: Write failing tests（编写失败测试）**
  - Test generated certificate has no `import`.
  - Test it includes inline `Magma`, `Equation<ID>` abbreviations, table operation, and theorem.

- [ ] **Step 2: Implement generator（实现生成器）**
  - Convert parsed equation AST to Lean expressions using `◇`.
  - Generate variables from each equation in first-occurrence order.

### Task 2: Asset Exporter（资产导出器）

**Files:**
- Create: `src/math_distill_stage2/counterexample_assets.py`
- Create: `scripts/export_counterexample_assets.py`
- Create: `tests/test_counterexample_assets.py`

- [ ] **Step 3: Write failing tests（编写失败测试）**
  - Test `eq1-<id>-eq2-<id>/problem.json`.
  - Test `runs/<run-id>/countermodel.json`, `certificate.lean`, `metadata.json`, `verification.json`.
  - Test global `index.jsonl` and `latest.json`.

- [ ] **Step 4: Implement exporter（实现导出器）**
  - Read `verified_counterexamples.jsonl`.
  - Write global dataset assets.
  - Optionally verify each `certificate.lean` with bare `lean`.

### Task 3: Real Export（真实导出）

- [ ] **Step 5: Export 438 assets（导出 438 个资产）**
  - Use run id `2026-04-29-000004-pure-lean-order2`.

- [ ] **Step 6: Verify with bare Lean（用纯 Lean 验证）**
  - Verify generated `certificate.lean` files without `lake`, `mathlib`, or `equational_theories`.

- [ ] **Step 7: Update docs and run tests（更新文档并测试）**
  - Update architecture/data inventory/experiment docs.
  - Run `pytest -q`.
