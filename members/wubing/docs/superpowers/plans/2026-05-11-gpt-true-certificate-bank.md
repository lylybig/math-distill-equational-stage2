# GPT True Certificate Bank Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Stage 2 GPT/Codex true certificate proof bank MVP: skills, prompt packs, response import, official judge verification, bank merge, and integrity checks.

**Architecture:** Project skills orchestrate the creative Codex proof-generation step; deterministic Python modules and CLI scripts handle keying, content-addressed storage, prompt packs, extraction, official judge verification, merge, and rebuild. The global bank is append-only for source ledgers and rebuildable for derived indexes.

**Tech Stack:** Python 3, pytest, JSONL files, existing `math_distill_stage2.equations`, existing official Stage 2 judge adapter, Codex skills under `skills/`.

---

## File Structure

Create or modify these files:

- Modify `AGENTS.md` to route proof bank work to `stage2-proofbank-*`.
- Modify `docs/architecture.md` to add the offline true proof bank layer.
- Modify `tests/skills/test_stage2_skills.py` to cover proof bank skill directories and boundaries.
- Create `skills/stage2-proofbank-start/SKILL.md`.
- Create `skills/stage2-proofbank-start/agents/openai.yaml`.
- Create `skills/stage2-proofbank-generate-true-certificate/SKILL.md`.
- Create `skills/stage2-proofbank-generate-true-certificate/agents/openai.yaml`.
- Create `skills/stage2-proofbank-generate-true-certificate/references/prompt-item-contract.md`.
- Create `skills/stage2-proofbank-verify-import/SKILL.md`.
- Create `skills/stage2-proofbank-verify-import/agents/openai.yaml`.
- Create `skills/stage2-proofbank-verify-import/references/judge-result-contract.md`.
- Create `skills/stage2-proofbank-maintain/SKILL.md`.
- Create `skills/stage2-proofbank-maintain/agents/openai.yaml`.
- Create `skills/stage2-proofbank-maintain/references/bank-contract.md`.
- Create `src/math_distill_stage2/proof_bank/__init__.py`.
- Create `src/math_distill_stage2/proof_bank/keying.py` for equation signatures, problem keys, and hashes.
- Create `src/math_distill_stage2/proof_bank/storage.py` for JSON and content-addressed file helpers.
- Create `src/math_distill_stage2/proof_bank/bank.py` for init, rebuild, check, and merge logic.
- Create `src/math_distill_stage2/proof_bank/prompt_pack.py` for prompt pack creation.
- Create `src/math_distill_stage2/proof_bank/import_responses.py` for extraction, normalization, wrapping, and judge import.
- Create `src/math_distill_stage2/proof_bank/judge_classification.py` for official judge status/error classification.
- Create `scripts/lean_certificates/proof_bank_init.py`.
- Create `scripts/lean_certificates/proof_bank_build_prompt_pack.py`.
- Create `scripts/lean_certificates/proof_bank_import_responses.py`.
- Create `scripts/lean_certificates/proof_bank_merge_run.py`.
- Create `scripts/lean_certificates/proof_bank_check.py`.
- Create `scripts/lean_certificates/proof_bank_rebuild_indexes.py`.
- Create `tests/proof_bank/test_keying.py`.
- Create `tests/proof_bank/test_storage.py`.
- Create `tests/proof_bank/test_bank_indexes.py`.
- Create `tests/proof_bank/test_prompt_pack.py`.
- Create `tests/proof_bank/test_import_responses.py`.
- Create `tests/proof_bank/test_merge_run.py`.
- Create `tests/proof_bank/test_cli.py`.

---

### Task 1: Add Proof Bank Skills And Long-Term Project Rules

**Files:**
- Modify: `tests/skills/test_stage2_skills.py`
- Modify: `AGENTS.md`
- Modify: `docs/architecture.md`
- Create: `skills/stage2-proofbank-start/SKILL.md`
- Create: `skills/stage2-proofbank-start/agents/openai.yaml`
- Create: `skills/stage2-proofbank-generate-true-certificate/SKILL.md`
- Create: `skills/stage2-proofbank-generate-true-certificate/agents/openai.yaml`
- Create: `skills/stage2-proofbank-generate-true-certificate/references/prompt-item-contract.md`
- Create: `skills/stage2-proofbank-verify-import/SKILL.md`
- Create: `skills/stage2-proofbank-verify-import/agents/openai.yaml`
- Create: `skills/stage2-proofbank-verify-import/references/judge-result-contract.md`
- Create: `skills/stage2-proofbank-maintain/SKILL.md`
- Create: `skills/stage2-proofbank-maintain/agents/openai.yaml`
- Create: `skills/stage2-proofbank-maintain/references/bank-contract.md`
- Test: `tests/skills/test_stage2_skills.py`

- [ ] **Step 1: Write failing skill tests**

Append this test to `tests/skills/test_stage2_skills.py`:

```python
def test_stage2_proofbank_skills_define_offline_certificate_bank_workflow():
    root = Path(__file__).resolve().parents[2]
    expected = [
        root / "skills" / "stage2-proofbank-start",
        root / "skills" / "stage2-proofbank-generate-true-certificate",
        root / "skills" / "stage2-proofbank-verify-import",
        root / "skills" / "stage2-proofbank-maintain",
    ]
    for path in expected:
        assert path.is_dir(), f"missing proofbank skill directory: {path}"
        assert (path / "SKILL.md").exists(), f"missing SKILL.md: {path}"
        assert (path / "agents" / "openai.yaml").exists(), f"missing openai.yaml: {path}"

    start = (root / "skills" / "stage2-proofbank-start" / "SKILL.md").read_text(encoding="utf-8")
    generate = (
        root
        / "skills"
        / "stage2-proofbank-generate-true-certificate"
        / "SKILL.md"
    ).read_text(encoding="utf-8")
    verify = (
        root / "skills" / "stage2-proofbank-verify-import" / "SKILL.md"
    ).read_text(encoding="utf-8")
    maintain = (
        root / "skills" / "stage2-proofbank-maintain" / "SKILL.md"
    ).read_text(encoding="utf-8")

    assert "name: stage2-proofbank-start" in frontmatter_text(root / "skills" / "stage2-proofbank-start")
    assert "offline Stage 2 GPT/Codex true certificate bank generation" in start
    assert "stage2-proofbank-generate-true-certificate" in start
    assert "stage2-proofbank-verify-import" in start
    assert "stage2-proofbank-maintain" in start
    assert "Do not edit `solver.py`" in start
    assert "test_locked" in start

    assert "name: stage2-proofbank-generate-true-certificate" in frontmatter_text(
        root / "skills" / "stage2-proofbank-generate-true-certificate"
    )
    assert "Use the current Codex model" in generate
    assert "raw_response_path" in generate
    assert "Do not call the judge" in generate
    assert "Use `◇` and `congrArg`" in generate
    assert (root / "skills" / "stage2-proofbank-generate-true-certificate" / "references" / "prompt-item-contract.md").exists()

    assert "name: stage2-proofbank-verify-import" in frontmatter_text(
        root / "skills" / "stage2-proofbank-verify-import"
    )
    assert "official Stage 2 judge" in verify
    assert "Do not synthesize or repair proofs" in verify
    assert "generated_attempts.jsonl" in verify
    assert (root / "skills" / "stage2-proofbank-verify-import" / "references" / "judge-result-contract.md").exists()

    assert "name: stage2-proofbank-maintain" in frontmatter_text(
        root / "skills" / "stage2-proofbank-maintain"
    )
    assert "data/processed/proof_banks/gpt_true_certificates/" in maintain
    assert "dry-run before write" in maintain
    assert "Do not generate proofs" in maintain
    assert (root / "skills" / "stage2-proofbank-maintain" / "references" / "bank-contract.md").exists()
```

- [ ] **Step 2: Run the failing skill test**

Run:

```bash
pytest -q tests/skills/test_stage2_skills.py::test_stage2_proofbank_skills_define_offline_certificate_bank_workflow
```

Expected: FAIL because the proof bank skill directories do not exist.

- [ ] **Step 3: Create `stage2-proofbank-start` skill**

Create `skills/stage2-proofbank-start/SKILL.md`:

```markdown
---
name: stage2-proofbank-start
description: Use when starting or continuing offline Stage 2 GPT/Codex true certificate bank generation, proof bank batches, or Codex-assisted Lean certificate mining.
---

# Stage2 Proofbank Start

Coordinate offline true certificate bank generation. This workflow creates and verifies certificate attempts; it does not improve or edit `solver.py`.

## Goal

Build `data/processed/proof_banks/gpt_true_certificates/` from Codex-generated true proof attempts that are verified by the official Stage 2 judge.

## Load Order

1. Use `stage2-proofbank-maintain` to inspect or initialize the bank.
2. Build or continue a bounded prompt pack.
3. Use `stage2-proofbank-generate-true-certificate` for 1-3 prompt items.
4. Use `stage2-proofbank-verify-import` to extract and judge raw responses.
5. Use `stage2-proofbank-maintain` to merge, rebuild indexes, and check the bank.

## Autonomy

You may create proof bank run directories, prompt packs, raw responses, judge artifacts, and global bank index updates. Keep batches to 1-3 Codex proof-generation items unless the user explicitly asks for more.

## Stop And Ask

Stop before modifying `solver.py`, using `test_locked` individual failures, adding known-proof tables, deleting bank ledgers, running large/paid/cloud batches, or converting certificates into solver templates.

## Report

Report generated raw responses, accepted/rejected/skipped counts, bank path, source run id, and confirm that no solver files changed.
```

Create `skills/stage2-proofbank-start/agents/openai.yaml`:

```yaml
interface:
  display_name: "Stage2 Proofbank Start"
  short_description: "Coordinate offline certificate bank batches"
  default_prompt: "Use $stage2-proofbank-start to continue offline Stage 2 true certificate bank generation."

policy:
  allow_implicit_invocation: true
```

- [ ] **Step 4: Create `stage2-proofbank-generate-true-certificate` skill**

Create `skills/stage2-proofbank-generate-true-certificate/SKILL.md`:

```markdown
---
name: stage2-proofbank-generate-true-certificate
description: Use when Codex should synthesize Lean 4 true proof responses for Stage 2 proof bank prompt pack items or unsolved true implications.
---

# Stage2 Proofbank Generate True Certificate

Use the current Codex model to produce raw true proof responses for proof bank prompt pack items. The output is not accepted until `stage2-proofbank-verify-import` runs the official judge.

## Workflow

1. Read one prompt item from `artifacts/proof_bank_runs/YYYY-MM-DD/<source_run_id>/prompt_pack/`.
2. Synthesize a self-contained Lean proof body for the given implication.
3. Write exactly one JSON object to the item’s `raw_response_path`.
4. Re-read the file and confirm it is a JSON object.
5. Process at most 1-3 items per invocation.

## Output Shape

```json
{"verdict":"true","proof":"intro x y z\ncalc\n  x = x := rfl"}
```

The `proof` field is inserted after:

```lean
import JudgeProblem

def submission : Goal := by
  intro G _ h
  <proof>
```

## Hard Constraints

Do not edit `solver.py`, call the judge, modify the global bank, claim accepted, generate false counterexamples, import external theorems, use `sorry`, `admit`, `axiom`, `unsafe`, `congr_arg`, `*`, theorem headers, or `def submission`.

Use `◇` and `congrArg`.

## If Stuck

Still write a raw response with an empty proof and a short `notes` field. Do not leave the item unrecorded.
```

Create `skills/stage2-proofbank-generate-true-certificate/agents/openai.yaml`:

```yaml
interface:
  display_name: "Stage2 Proofbank Generate"
  short_description: "Generate Codex true proof responses"
  default_prompt: "Use $stage2-proofbank-generate-true-certificate to synthesize Lean true proof responses for proof bank prompt items."

policy:
  allow_implicit_invocation: true
```

Create `skills/stage2-proofbank-generate-true-certificate/references/prompt-item-contract.md`:

```markdown
# Prompt Item Contract

## Required Sections

A prompt pack item must include Artifact Routing, Problem Identity, Equations, Judge Wrapper, Required Output, Allowed Lean Constructs, Forbidden, and Optional Trace Hint.

## Raw Response

Write exactly one JSON object to `raw_response_path`.

## Proof Body

The proof starts after `intro G _ h`; do not include imports, theorem headers, or `def submission`.

## Failure Response

Use `{"verdict":"true","proof":"","notes":"No self-contained proof found within this bounded generation attempt."}` when no proof is found.

## Existing Output

Do not overwrite an existing raw response unless the user explicitly asks for a retry.
```

- [ ] **Step 5: Create `stage2-proofbank-verify-import` skill**

Create `skills/stage2-proofbank-verify-import/SKILL.md`:

```markdown
---
name: stage2-proofbank-verify-import
description: Use when importing Codex-generated proof bank responses, extracting Lean proof bodies, wrapping Stage 2 certificates, or verifying with the official judge.
---

# Stage2 Proofbank Verify Import

Turn proof bank raw responses into deterministic attempt records using the official Stage 2 judge.

## Workflow

1. Read the proof bank run manifest, input problems, prompt pack, and raw responses.
2. Extract proof bodies from strict JSON, fenced JSON, fenced Lean, or bare Lean fallback.
3. Run preflight for forbidden constructs.
4. Wrap proof bodies with the Stage 2 true certificate wrapper.
5. Verify with the official Stage 2 judge.
6. Write `generated_attempts.jsonl`, `judge_results/`, `proof_bodies/`, `certificates/`, `extraction_errors.jsonl`, and `summary.json`.

## Constraints

Do not synthesize or repair proofs, modify `solver.py`, modify the global bank, or treat non-accepted judge results as accepted certificates.

## Report

Report attempt count, accepted/rejected/skipped/error/timeout counts, top error kinds, and the run artifact path.
```

Create `skills/stage2-proofbank-verify-import/agents/openai.yaml`:

```yaml
interface:
  display_name: "Stage2 Proofbank Verify"
  short_description: "Verify and import proof responses"
  default_prompt: "Use $stage2-proofbank-verify-import to extract Codex proof responses and verify them with the official Stage 2 judge."

policy:
  allow_implicit_invocation: true
```

Create `skills/stage2-proofbank-verify-import/references/judge-result-contract.md`:

```markdown
# Judge Result Contract

## Extraction Order

Use strict JSON, fenced JSON, fenced Lean, then bare Lean fallback.

## Normalization

Strip fences, strip wrappers, replace `*` with `◇`, replace `congr_arg` with `congrArg`, and record all actions.

## Status Mapping

Map official `accepted` to bank `accepted`; map official `unparsed`, `malformed`, `incomplete_proof`, and `incorrect` to bank `rejected`; map runner timeout to `timeout`; map adapter exceptions to `error`; map preflight skips to `skipped`.

## Error Kinds

Use `none`, `no_certificate_extracted`, `invalid_json_or_payload`, `forbidden_construct`, `lean_parse_error`, `lean_unknown_identifier`, `lean_type_error`, `lean_unsolved_goals`, `lean_tactic_failure`, `lean_timeout`, `judge_protocol_error`, `generator_error`, or `unknown`.

## Attempt Summary

Store only hashes and short classification fields in `generated_attempts.jsonl`; store full raw stdout, stderr, message, and artifact metadata in content-addressed judge result JSON.
```

- [ ] **Step 6: Create `stage2-proofbank-maintain` skill**

Create `skills/stage2-proofbank-maintain/SKILL.md`:

```markdown
---
name: stage2-proofbank-maintain
description: Use when merging, checking, rebuilding, initializing, or auditing the global Stage 2 GPT true certificate proof bank.
---

# Stage2 Proofbank Maintain

Maintain the global proof bank at `data/processed/proof_banks/gpt_true_certificates/`.

## Modes

- `init`: create an empty bank manifest, ledgers, indexes, and content directories.
- `merge`: merge a proof bank run into the global bank.
- `check`: validate hashes, schemas, problem keys, content files, accepted evidence, and derived indexes.
- `rebuild`: regenerate `accepted.jsonl`, `latest_by_problem.jsonl`, and `bank_summary.json`.

## Rules

Run dry-run before write for merge. Treat `attempts.jsonl` and `problems.jsonl` as source ledgers. Treat accepted/latest/summary as derived indexes. Stop on same attempt id with different hashes, problem key signature mismatch, missing content files, or accepted attempts without official accepted judge evidence.

## Constraints

Do not generate proofs, run Codex proof synthesis, modify `solver.py`, export submissions, or select solver templates.

## Report

Report new problems, attempts, accepted records, skipped duplicates, hard errors, and final bank check status.
```

Create `skills/stage2-proofbank-maintain/agents/openai.yaml`:

```yaml
interface:
  display_name: "Stage2 Proofbank Maintain"
  short_description: "Merge and audit the certificate bank"
  default_prompt: "Use $stage2-proofbank-maintain to merge, check, or rebuild the global Stage 2 true certificate bank."

policy:
  allow_implicit_invocation: true
```

Create `skills/stage2-proofbank-maintain/references/bank-contract.md`:

```markdown
# Proof Bank Contract

## Layout

The global bank lives at `data/processed/proof_banks/gpt_true_certificates/`.

## Source Ledgers

`problems.jsonl` and `attempts.jsonl` are source ledgers.

## Derived Indexes

`accepted.jsonl`, `latest_by_problem.jsonl`, and `bank_summary.json` are rebuildable derived indexes.

## Problem Key

Use `implication:sig:<eq1_hash16>:<eq2_hash16>`.

## Merge Rules

Merge is idempotent. The same attempt id with different hashes is a hard error.

## Check Rules

Recompute signatures, hashes, indexes, and official accepted evidence.
```

- [ ] **Step 7: Update `AGENTS.md`**

Add this block under the existing “技能优先原则” list:

```markdown
- 涉及离线使用 Codex/GPT 生成、验证、保存 Stage 2 true Lean certificate 到全局 proof bank，且不立即修改 `solver.py` 时，优先使用：
  - `stage2-proofbank-start`
  - `stage2-proofbank-generate-true-certificate`
  - `stage2-proofbank-verify-import`
  - `stage2-proofbank-maintain`
- `stage2-proofbank-*` 技能只负责离线 certificate attempt bank（证书尝试库）的生成、验证和维护；不等同于 solver 训练闭环。只有用户明确要求把 accepted certificate 转化为 solver template、focused test 或版本提升时，才切换到 `stage2-train-*`。
- proof bank 相关项目私有技能统一使用 `stage2-proofbank-` 前缀；不要和 `stage2-train-proof-seed` 混用。
```

- [ ] **Step 8: Update `docs/architecture.md`**

Add a short subsection under the certificate asset or LLM strategy area:

```markdown
### 离线 true proof bank

`data/processed/proof_banks/gpt_true_certificates/` 保存全局 Codex/GPT 生成的 true proof certificate attempts（真命题证明证书尝试）。`artifacts/proof_bank_runs/YYYY-MM-DD/<source_run_id>/` 保存单次 proof bank generation run（生成批次）的 prompt pack、raw responses、judge results 和 summary。

`stage2-proofbank-*` 技能负责用当前 Codex 会话生成 Lean proof body、用官方 judge 验证、再把结果合并进全局 bank。全局 bank 是离线证书事实库，不是 solver 策略层，也不直接修改 `solver.py`。accepted certificate 的唯一得分边界仍是官方 Stage 2 judge `accepted`。
```

- [ ] **Step 9: Run skill tests**

Run:

```bash
pytest -q tests/skills/test_stage2_skills.py
```

Expected: PASS.

- [ ] **Step 10: Commit**

Run:

```bash
git add AGENTS.md docs/architecture.md tests/skills/test_stage2_skills.py skills/stage2-proofbank-start skills/stage2-proofbank-generate-true-certificate skills/stage2-proofbank-verify-import skills/stage2-proofbank-maintain
git commit -m "docs: add stage2 proofbank skills"
```

---

### Task 2: Add Core Problem Keying And Content Storage

**Files:**
- Create: `tests/proof_bank/test_keying.py`
- Create: `tests/proof_bank/test_storage.py`
- Create: `src/math_distill_stage2/proof_bank/__init__.py`
- Create: `src/math_distill_stage2/proof_bank/keying.py`
- Create: `src/math_distill_stage2/proof_bank/storage.py`

- [ ] **Step 1: Write failing keying tests**

Create `tests/proof_bank/test_keying.py`:

```python
from math_distill_stage2.proof_bank.keying import (
    canonical_signature_for_bank,
    problem_key_from_equations,
    sha256_hex,
    short_hash,
)


def test_canonical_signature_accepts_diamond_operator():
    assert canonical_signature_for_bank("x = y ◇ x") == "v0=(v1*v0)"


def test_problem_key_is_signature_first_and_oriented():
    forward = problem_key_from_equations("x = y ◇ x", "x = x ◇ y")
    backward = problem_key_from_equations("x = x ◇ y", "x = y ◇ x")

    assert forward.startswith("implication:sig:")
    assert forward != backward
    assert len(forward.split(":")[-1]) == 16


def test_short_hash_uses_sha256_prefix():
    digest = sha256_hex("abc")
    assert digest == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert short_hash("abc") == "ba7816bf8f01cfea"
```

- [ ] **Step 2: Write failing storage tests**

Create `tests/proof_bank/test_storage.py`:

```python
import json
from pathlib import Path

from math_distill_stage2.proof_bank.storage import (
    content_addressed_path,
    read_json,
    write_content_addressed_text,
    write_json,
)


def test_write_content_addressed_text_uses_first_two_sha_chars(tmp_path: Path):
    result = write_content_addressed_text(tmp_path, "proof_bodies", "hello\n", ".lean")

    assert result.sha256 == "5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03"
    assert result.path == tmp_path / "proof_bodies" / "58" / f"{result.sha256}.lean"
    assert result.path.read_text(encoding="utf-8") == "hello\n"


def test_content_addressed_path_is_deterministic(tmp_path: Path):
    sha = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    assert content_addressed_path(tmp_path, "certificates", sha, ".lean") == (
        tmp_path / "certificates" / "01" / f"{sha}.lean"
    )


def test_write_and_read_json(tmp_path: Path):
    path = tmp_path / "nested" / "payload.json"
    write_json(path, {"b": 2, "a": 1})

    assert json.loads(path.read_text(encoding="utf-8")) == {"a": 1, "b": 2}
    assert read_json(path) == {"a": 1, "b": 2}
```

- [ ] **Step 3: Run failing tests**

Run:

```bash
pytest -q tests/proof_bank/test_keying.py tests/proof_bank/test_storage.py
```

Expected: FAIL with import errors for `math_distill_stage2.proof_bank`.

- [ ] **Step 4: Implement keying and storage**

Create `src/math_distill_stage2/proof_bank/__init__.py`:

```python
"""Offline Stage 2 true proof certificate bank utilities."""
```

Create `src/math_distill_stage2/proof_bank/keying.py`:

```python
from __future__ import annotations

import hashlib

from math_distill_stage2.equations import canonical_equation_signature


def normalize_equation_operator(source: str) -> str:
    return source.replace("◇", "*")


def canonical_signature_for_bank(source: str) -> str:
    return canonical_equation_signature(normalize_equation_operator(source))


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def short_hash(text: str, length: int = 16) -> str:
    if length <= 0 or length > 64:
        raise ValueError("length must be between 1 and 64")
    return sha256_hex(text)[:length]


def problem_key_from_signatures(eq1_signature: str, eq2_signature: str) -> str:
    return f"implication:sig:{short_hash(eq1_signature)}:{short_hash(eq2_signature)}"


def problem_key_from_equations(equation1: str, equation2: str) -> str:
    return problem_key_from_signatures(
        canonical_signature_for_bank(equation1),
        canonical_signature_for_bank(equation2),
    )
```

Create `src/math_distill_stage2/proof_bank/storage.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class StoredText:
    sha256: str
    path: Path
    byte_length: int


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def content_addressed_path(root: Path, kind: str, sha256: str, suffix: str) -> Path:
    if len(sha256) != 64:
        raise ValueError("sha256 must be a 64-character hex digest")
    if not suffix.startswith("."):
        raise ValueError("suffix must start with '.'")
    return root / kind / sha256[:2] / f"{sha256}{suffix}"


def write_content_addressed_text(root: Path, kind: str, text: str, suffix: str) -> StoredText:
    digest = text_sha256(text)
    path = content_addressed_path(root, kind, digest, suffix)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(text, encoding="utf-8")
    return StoredText(sha256=digest, path=path, byte_length=len(text.encode("utf-8")))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload
```

- [ ] **Step 5: Run tests**

Run:

```bash
pytest -q tests/proof_bank/test_keying.py tests/proof_bank/test_storage.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add src/math_distill_stage2/proof_bank tests/proof_bank/test_keying.py tests/proof_bank/test_storage.py
git commit -m "feat: add proof bank keying and storage"
```

---

### Task 3: Add Bank Init, Index Rebuild, And Integrity Check

**Files:**
- Create: `tests/proof_bank/test_bank_indexes.py`
- Create: `src/math_distill_stage2/proof_bank/bank.py`
- Create: `scripts/lean_certificates/proof_bank_init.py`
- Create: `scripts/lean_certificates/proof_bank_rebuild_indexes.py`
- Create: `scripts/lean_certificates/proof_bank_check.py`
- Test: `tests/proof_bank/test_bank_indexes.py`

- [ ] **Step 1: Write failing bank index tests**

Create `tests/proof_bank/test_bank_indexes.py`:

```python
from pathlib import Path

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.proof_bank.bank import (
    check_bank,
    init_bank,
    rebuild_indexes,
)


def accepted_attempt(problem_key: str, attempt_id: str) -> dict:
    return {
        "schema_version": 1,
        "attempt_id": attempt_id,
        "problem_key": problem_key,
        "certificate_kind": "true_proof",
        "certificate_sha256": "a" * 64,
        "judge_commit": "6805e2323018fbd8a85f41ca09fc33d74d5a02a5",
        "official_judge_status": "accepted",
        "judge_status": "accepted",
        "judge_error_kind": "none",
        "source_run_id": "run-1",
        "created_at": "2026-05-11T00:00:00Z",
    }


def test_init_bank_writes_empty_ledgers_and_manifest(tmp_path: Path):
    summary = init_bank(tmp_path)

    assert summary["bank"] == str(tmp_path)
    assert (tmp_path / "bank_manifest.json").exists()
    assert (tmp_path / "problems.jsonl").read_text(encoding="utf-8") == ""
    assert (tmp_path / "attempts.jsonl").read_text(encoding="utf-8") == ""
    assert (tmp_path / "accepted.jsonl").read_text(encoding="utf-8") == ""
    assert (tmp_path / "latest_by_problem.jsonl").read_text(encoding="utf-8") == ""


def test_rebuild_indexes_derives_accepted_and_latest(tmp_path: Path):
    init_bank(tmp_path)
    problem_key = "implication:sig:1111111111111111:2222222222222222"
    write_jsonl(
        tmp_path / "problems.jsonl",
        [
            {
                "schema_version": 1,
                "problem_key": problem_key,
                "problem_aliases": [],
                "equation1": "x = x",
                "equation2": "x = x",
                "eq1_signature": "v0=v0",
                "eq2_signature": "v0=v0",
                "source_datasets": ["fixture"],
            }
        ],
    )
    write_jsonl(
        tmp_path / "attempts.jsonl",
        [
            {
                **accepted_attempt(problem_key, "attempt:run-1:000001"),
                "judge_result_sha256": "b" * 64,
            },
            {
                "schema_version": 1,
                "attempt_id": "attempt:run-1:000002",
                "problem_key": problem_key,
                "certificate_kind": "true_proof",
                "judge_status": "rejected",
                "official_judge_status": "incorrect",
                "judge_error_kind": "lean_type_error",
                "source_run_id": "run-1",
                "created_at": "2026-05-11T00:01:00Z",
            },
        ],
    )

    summary = rebuild_indexes(tmp_path)

    accepted_rows = read_jsonl(tmp_path / "accepted.jsonl")
    latest_rows = read_jsonl(tmp_path / "latest_by_problem.jsonl")
    assert summary["accepted_count"] == 1
    assert accepted_rows[0]["attempt_id"] == "attempt:run-1:000001"
    assert latest_rows[0]["latest_attempt_id"] == "attempt:run-1:000002"
    assert latest_rows[0]["accepted_attempt_count"] == 1
    assert latest_rows[0]["rejected_attempt_count"] == 1


def test_check_bank_reports_duplicate_attempt_ids(tmp_path: Path):
    init_bank(tmp_path)
    problem_key = "implication:sig:1111111111111111:2222222222222222"
    row = accepted_attempt(problem_key, "attempt:run-1:000001")
    write_jsonl(tmp_path / "attempts.jsonl", [row, row])

    result = check_bank(tmp_path)

    assert result["ok"] is False
    assert "duplicate attempt_id: attempt:run-1:000001" in result["errors"]
```

- [ ] **Step 2: Run failing tests**

Run:

```bash
pytest -q tests/proof_bank/test_bank_indexes.py
```

Expected: FAIL because `proof_bank.bank` does not exist.

- [ ] **Step 3: Implement bank init, rebuild, and check**

Create `src/math_distill_stage2/proof_bank/bank.py`:

```python
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.proof_bank.storage import write_json


CONTENT_DIRS = (
    "certificates",
    "proof_bodies",
    "prompts",
    "raw_responses",
    "judge_results",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def init_bank(bank: Path) -> dict[str, Any]:
    bank.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1,
        "bank_id": "gpt_true_certificates",
        "certificate_kind": "true_proof",
        "created_at_utc": utc_now(),
        "problem_key_scheme": {
            "version": 1,
            "format": "implication:sig:<eq1_hash16>:<eq2_hash16>",
            "hash": "sha256",
            "hash_prefix_length": 16,
            "oriented": True,
        },
    }
    if not (bank / "bank_manifest.json").exists():
        write_json(bank / "bank_manifest.json", manifest)
    for filename in (
        "problems.jsonl",
        "attempts.jsonl",
        "accepted.jsonl",
        "latest_by_problem.jsonl",
    ):
        path = bank / filename
        if not path.exists():
            path.write_text("", encoding="utf-8")
    for dirname in CONTENT_DIRS:
        (bank / dirname).mkdir(parents=True, exist_ok=True)
    summary = rebuild_indexes(bank)
    summary["bank"] = str(bank)
    return summary


def rebuild_indexes(bank: Path) -> dict[str, Any]:
    attempts = read_jsonl(bank / "attempts.jsonl") if (bank / "attempts.jsonl").exists() else []
    accepted = [
        {
            "schema_version": 1,
            "problem_key": row["problem_key"],
            "attempt_id": row["attempt_id"],
            "certificate_sha256": row.get("certificate_sha256"),
            "certificate_kind": row.get("certificate_kind"),
            "judge_commit": row.get("judge_commit"),
            "accepted_at": row.get("created_at"),
        }
        for row in attempts
        if row.get("judge_status") == "accepted"
        and row.get("official_judge_status") == "accepted"
        and row.get("certificate_kind") == "true_proof"
    ]

    by_problem: dict[str, list[dict]] = defaultdict(list)
    for row in attempts:
        by_problem[str(row.get("problem_key"))].append(row)

    latest_rows = []
    for problem_key, rows in sorted(by_problem.items()):
        latest = rows[-1]
        accepted_rows = [row for row in rows if row.get("judge_status") == "accepted"]
        rejected_rows = [row for row in rows if row.get("judge_status") == "rejected"]
        latest_rows.append(
            {
                "schema_version": 1,
                "problem_key": problem_key,
                "latest_attempt_id": latest.get("attempt_id"),
                "latest_status": latest.get("judge_status"),
                "accepted_attempt_count": len(accepted_rows),
                "rejected_attempt_count": len(rejected_rows),
                "best_known_certificate_sha256": (
                    accepted_rows[0].get("certificate_sha256") if accepted_rows else None
                ),
                "updated_at": latest.get("created_at"),
            }
        )

    write_jsonl(bank / "accepted.jsonl", accepted)
    write_jsonl(bank / "latest_by_problem.jsonl", latest_rows)
    summary = {
        "schema_version": 1,
        "problem_count": len(read_jsonl(bank / "problems.jsonl")) if (bank / "problems.jsonl").exists() else 0,
        "attempt_count": len(attempts),
        "accepted_count": len(accepted),
        "latest_problem_count": len(latest_rows),
    }
    write_json(bank / "bank_summary.json", summary)
    return summary


def check_bank(bank: Path) -> dict[str, Any]:
    errors: list[str] = []
    if not (bank / "bank_manifest.json").exists():
        errors.append("missing bank_manifest.json")
    attempts = read_jsonl(bank / "attempts.jsonl") if (bank / "attempts.jsonl").exists() else []
    seen_attempts: set[str] = set()
    for row in attempts:
        attempt_id = str(row.get("attempt_id"))
        if attempt_id in seen_attempts:
            errors.append(f"duplicate attempt_id: {attempt_id}")
        seen_attempts.add(attempt_id)
        if row.get("judge_status") == "accepted" and row.get("official_judge_status") != "accepted":
            errors.append(f"accepted attempt without official accepted judge result: {attempt_id}")
    return {
        "bank": str(bank),
        "ok": not errors,
        "errors": errors,
        "attempt_count": len(attempts),
    }
```

- [ ] **Step 4: Add CLI wrappers**

Create `scripts/lean_certificates/proof_bank_init.py`:

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))

from math_distill_stage2.proof_bank.bank import init_bank


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Initialize the Stage 2 GPT true certificate proof bank.")
    parser.add_argument("--bank", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(init_bank(args.bank), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Create `scripts/lean_certificates/proof_bank_rebuild_indexes.py`:

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))

from math_distill_stage2.proof_bank.bank import rebuild_indexes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rebuild derived indexes for the proof bank.")
    parser.add_argument("--bank", type=Path, required=True)
    parser.add_argument("--write", action="store_true", help="Accepted for interface consistency; rebuild writes indexes.")
    args = parser.parse_args(argv)
    print(json.dumps(rebuild_indexes(args.bank), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Create `scripts/lean_certificates/proof_bank_check.py`:

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))

from math_distill_stage2.proof_bank.bank import check_bank


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check proof bank integrity.")
    parser.add_argument("--bank", type=Path, required=True)
    args = parser.parse_args(argv)
    result = check_bank(args.bank)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run tests**

Run:

```bash
pytest -q tests/proof_bank/test_bank_indexes.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add src/math_distill_stage2/proof_bank/bank.py scripts/lean_certificates/proof_bank_init.py scripts/lean_certificates/proof_bank_rebuild_indexes.py scripts/lean_certificates/proof_bank_check.py tests/proof_bank/test_bank_indexes.py
git commit -m "feat: add proof bank ledgers and indexes"
```

---

### Task 4: Add Prompt Pack Builder

**Files:**
- Create: `tests/proof_bank/test_prompt_pack.py`
- Create: `src/math_distill_stage2/proof_bank/prompt_pack.py`
- Create: `scripts/lean_certificates/proof_bank_build_prompt_pack.py`

- [ ] **Step 1: Write failing prompt pack tests**

Create `tests/proof_bank/test_prompt_pack.py`:

```python
from pathlib import Path

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.proof_bank.bank import init_bank
from math_distill_stage2.proof_bank.prompt_pack import build_prompt_pack


def test_build_prompt_pack_writes_prompt_and_manifest(tmp_path: Path):
    bank = tmp_path / "bank"
    init_bank(bank)
    pool = tmp_path / "candidate_pool.jsonl"
    write_jsonl(
        pool,
        [
            {
                "source_problem_id": "true_5_2638",
                "source_dataset": "order4_splits/dev_fast",
                "eq1_id": 5,
                "eq2_id": 2638,
                "equation1": "x = y ◇ x",
                "equation2": "x = (y ◇ z) ◇ x",
                "expected_verdict": True,
                "priority_score": 10,
                "external_trace_available": False,
            }
        ],
    )
    run_root = tmp_path / "runs"

    summary = build_prompt_pack(
        bank=bank,
        candidate_pool=pool,
        run_root=run_root,
        source_run_id="gpt-true-cert-fixture-20260511-001",
        limit=1,
        prompt_policy="trace-if-available",
    )

    run_dir = Path(summary["run_dir"])
    prompt = (run_dir / "prompt_pack" / "000001.md").read_text(encoding="utf-8")
    assert summary["problem_count"] == 1
    assert (run_dir / "manifest.json").exists()
    assert read_jsonl(run_dir / "input_problems.jsonl")[0]["source_problem_id"] == "true_5_2638"
    assert "raw_response_path:" in prompt
    assert "x = y ◇ x" in prompt
    assert "def submission : Goal := by" in prompt
    assert '"verdict": "true"' in prompt
```

- [ ] **Step 2: Run failing test**

Run:

```bash
pytest -q tests/proof_bank/test_prompt_pack.py
```

Expected: FAIL because `prompt_pack.py` does not exist.

- [ ] **Step 3: Implement prompt pack builder**

Create `src/math_distill_stage2/proof_bank/prompt_pack.py`:

```python
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.proof_bank.keying import (
    canonical_signature_for_bank,
    problem_key_from_equations,
)
from math_distill_stage2.proof_bank.storage import write_json


def run_dir_for(run_root: Path, source_run_id: str, day: date | None = None) -> Path:
    day = day or date.today()
    return run_root / day.isoformat() / source_run_id


def build_prompt_pack(
    *,
    bank: Path,
    candidate_pool: Path,
    run_root: Path,
    source_run_id: str,
    limit: int,
    prompt_policy: str,
) -> dict[str, Any]:
    rows = read_jsonl(candidate_pool)
    selected = rows[:limit]
    run_dir = run_dir_for(run_root, source_run_id)
    prompt_dir = run_dir / "prompt_pack"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    input_rows: list[dict[str, Any]] = []
    for index, row in enumerate(selected, start=1):
        item_id = f"{index:06d}"
        eq1 = str(row["equation1"])
        eq2 = str(row["equation2"])
        problem_key = problem_key_from_equations(eq1, eq2)
        problem = {
            **row,
            "schema_version": 1,
            "item_id": item_id,
            "problem_key": problem_key,
            "eq1_signature": canonical_signature_for_bank(eq1),
            "eq2_signature": canonical_signature_for_bank(eq2),
        }
        input_rows.append(problem)
        raw_response_path = run_dir / "raw_responses" / f"{item_id}.txt"
        prompt_text = render_prompt_item(problem, source_run_id, raw_response_path)
        (prompt_dir / f"{item_id}.md").write_text(prompt_text, encoding="utf-8")

    write_jsonl(run_dir / "input_problems.jsonl", input_rows)
    manifest = {
        "schema_version": 1,
        "source_run_id": source_run_id,
        "bank_id": "gpt_true_certificates",
        "bank": str(bank),
        "candidate_pool": str(candidate_pool),
        "prompt_policy": prompt_policy,
        "problem_count": len(input_rows),
    }
    write_json(run_dir / "manifest.json", manifest)
    return {"run_dir": str(run_dir), "problem_count": len(input_rows)}


def render_prompt_item(problem: dict[str, Any], source_run_id: str, raw_response_path: Path) -> str:
    trace = "none"
    if problem.get("external_trace_available"):
        trace = str(problem.get("external_trace_family") or "available")
    return f"""# Stage 2 True Certificate Prompt Item

## Artifact Routing

- source_run_id: {source_run_id}
- item_id: {problem["item_id"]}
- raw_response_path: {raw_response_path}

## Problem Identity

- problem_key: {problem["problem_key"]}
- source_problem_id: {problem.get("source_problem_id")}
- source_dataset: {problem.get("source_dataset")}
- eq1_id: {problem.get("eq1_id")}
- eq2_id: {problem.get("eq2_id")}

## Equations

Premise equation `h`:

```text
{problem["equation1"]}
```

Goal equation:

```text
{problem["equation2"]}
```

## Judge Wrapper

Your proof will be inserted here:

```lean
import JudgeProblem

def submission : Goal := by
  intro G _ h
  <YOUR PROOF BODY>
```

## Required Output

Write exactly one JSON object to `raw_response_path`:

```json
{{
  "verdict": "true",
  "proof": "intro x y z\\ncalc\\n  x = x := rfl"
}}
```

The `proof` field must be only the tactic body after `intro G _ h`.

## Allowed Lean Constructs

Prefer: `intro`, `let`, `have`, `calc`, `exact`, `fun`, `rfl`, `Eq.trans`, `Eq.symm`, `.trans`, `.symm`, `congrArg`.

## Forbidden

`sorry`, `admit`, `axiom`, `unsafe`, `import`, theorem headers, `def submission`, external theorem names, `congr_arg`, `*`.

Use `◇`, not `*`. Use `congrArg`, not `congr_arg`.

## Optional Trace Hint

trace: {trace}

These hints are not available as theorem names. They may only guide a self-contained proof from `h`.
"""
```

- [ ] **Step 4: Add CLI wrapper**

Create `scripts/lean_certificates/proof_bank_build_prompt_pack.py`:

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))

from math_distill_stage2.proof_bank.prompt_pack import build_prompt_pack


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a Stage 2 proof bank prompt pack.")
    parser.add_argument("--bank", type=Path, required=True)
    parser.add_argument("--candidate-pool", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, default=Path("artifacts/proof_bank_runs"))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--prompt-policy", default="trace-if-available")
    args = parser.parse_args(argv)
    summary = build_prompt_pack(
        bank=args.bank,
        candidate_pool=args.candidate_pool,
        run_root=args.run_root,
        source_run_id=args.run_id,
        limit=args.limit,
        prompt_policy=args.prompt_policy,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run tests**

Run:

```bash
pytest -q tests/proof_bank/test_prompt_pack.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add src/math_distill_stage2/proof_bank/prompt_pack.py scripts/lean_certificates/proof_bank_build_prompt_pack.py tests/proof_bank/test_prompt_pack.py
git commit -m "feat: build proof bank prompt packs"
```

---

### Task 5: Add Raw Response Extraction, Normalization, And Judge Classification

**Files:**
- Create: `tests/proof_bank/test_import_responses.py`
- Create: `src/math_distill_stage2/proof_bank/judge_classification.py`
- Create: `src/math_distill_stage2/proof_bank/import_responses.py`

- [ ] **Step 1: Write failing extraction and classification tests**

Create `tests/proof_bank/test_import_responses.py`:

```python
from math_distill_stage2.proof_bank.import_responses import (
    extract_response,
    normalize_proof_body,
    wrap_true_certificate,
)
from math_distill_stage2.proof_bank.judge_classification import classify_official_result


def test_extract_response_from_strict_json():
    extracted = extract_response('{"verdict":"true","proof":"intro x\\nexact h x"}')

    assert extracted.proof == "intro x\nexact h x"
    assert extracted.error_kind is None


def test_extract_response_from_lean_fence():
    extracted = extract_response("```lean\nintro x\nexact h x\n```")

    assert extracted.proof == "intro x\nexact h x"
    assert extracted.error_kind is None


def test_normalize_proof_body_records_safe_actions():
    normalized = normalize_proof_body("intro x\nhave hx := congr_arg (fun t => t * x) rfl")

    assert normalized.proof == "intro x\nhave hx := congrArg (fun t => t ◇ x) rfl"
    assert normalized.actions == ["replace_star_with_diamond", "replace_congr_arg_with_congrArg"]


def test_wrap_true_certificate_uses_judge_problem_wrapper():
    code = wrap_true_certificate("intro x\nexact h x")

    assert code.startswith("import JudgeProblem\n\n")
    assert "def submission : Goal := by\n  intro G _ h\n" in code
    assert "  intro x\n  exact h x\n" in code


def test_classify_official_result_maps_accepted_and_type_errors():
    accepted = classify_official_result(
        {"status": "accepted", "stderr": "", "message": "", "error_code": ""}
    )
    rejected = classify_official_result(
        {"status": "incorrect", "stderr": "application type mismatch", "message": "", "error_code": ""}
    )

    assert accepted["judge_status"] == "accepted"
    assert accepted["judge_error_kind"] == "none"
    assert rejected["judge_status"] == "rejected"
    assert rejected["judge_error_kind"] == "lean_type_error"
```

- [ ] **Step 2: Run failing tests**

Run:

```bash
pytest -q tests/proof_bank/test_import_responses.py
```

Expected: FAIL because import and classification modules do not exist.

- [ ] **Step 3: Implement classification**

Create `src/math_distill_stage2/proof_bank/judge_classification.py`:

```python
from __future__ import annotations

from typing import Any


def classify_official_result(raw: dict[str, Any]) -> dict[str, str | None]:
    status = str(raw.get("status") or "")
    text = " ".join(
        str(raw.get(key) or "") for key in ("stderr", "stdout", "message", "error_code")
    ).lower()
    if status == "accepted":
        return {
            "official_judge_status": "accepted",
            "judge_status": "accepted",
            "judge_error_kind": "none",
            "judge_error_subkind": None,
            "judge_error_summary": None,
        }
    if "unknown identifier" in text:
        kind = "lean_unknown_identifier"
    elif "unexpected token" in text or "expected command" in text:
        kind = "lean_parse_error"
    elif "application type mismatch" in text or "type mismatch" in text:
        kind = "lean_type_error"
    elif "unsolved goals" in text or "goals unsolved" in text:
        kind = "lean_unsolved_goals"
    elif "tactic" in text and "failed" in text:
        kind = "lean_tactic_failure"
    elif "timeout" in text or "timed out" in text:
        kind = "lean_timeout"
    elif status in {"unparsed", "malformed"}:
        kind = "invalid_json_or_payload" if status == "malformed" else "lean_parse_error"
    else:
        kind = "unknown"
    return {
        "official_judge_status": status,
        "judge_status": "rejected",
        "judge_error_kind": kind,
        "judge_error_subkind": None,
        "judge_error_summary": f"Official judge returned {status}.",
    }
```

- [ ] **Step 4: Implement extraction, normalization, and wrapping**

Create `src/math_distill_stage2/proof_bank/import_responses.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
import json
import re


@dataclass(frozen=True)
class ExtractedResponse:
    verdict: str | None
    proof: str
    error_kind: str | None
    error_summary: str | None = None


@dataclass(frozen=True)
class NormalizedProof:
    proof: str
    actions: list[str]


def extract_response(text: str) -> ExtractedResponse:
    stripped = text.strip()
    for candidate in _json_candidates(stripped):
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        proof = payload.get("proof")
        verdict = payload.get("verdict")
        if verdict != "true":
            return ExtractedResponse(None, "", "invalid_json_or_payload", "verdict must be true")
        if not isinstance(proof, str) or not proof.strip():
            return ExtractedResponse("true", "", "no_certificate_extracted", "proof is empty")
        return ExtractedResponse("true", proof.strip(), None)

    lean_match = re.search(r"```lean\s*(.*?)```", stripped, flags=re.DOTALL)
    if lean_match:
        proof = lean_match.group(1).strip()
        return ExtractedResponse("true", proof, None) if proof else ExtractedResponse("true", "", "no_certificate_extracted")

    if _looks_like_bare_lean(stripped):
        return ExtractedResponse("true", stripped, None)

    return ExtractedResponse(None, "", "no_certificate_extracted", "no JSON proof field or Lean code block found")


def _json_candidates(text: str) -> list[str]:
    candidates = [text]
    fenced = re.findall(r"```json\s*(.*?)```", text, flags=re.DOTALL)
    candidates.extend(match.strip() for match in fenced)
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        candidates.append(match.group(0))
    return candidates


def _looks_like_bare_lean(text: str) -> bool:
    if "\n" not in text:
        return False
    lean_starts = ("intro ", "let ", "have ", "calc", "exact ")
    return any(text.lstrip().startswith(prefix) for prefix in lean_starts)


def normalize_proof_body(proof: str) -> NormalizedProof:
    actions: list[str] = []
    normalized = proof.strip()
    if normalized.startswith("```"):
        normalized = re.sub(r"^```(?:lean)?\s*", "", normalized)
        normalized = re.sub(r"\s*```$", "", normalized)
        actions.append("strip_markdown_fence")
    if "def submission" in normalized or "intro G _ h" in normalized:
        lines = normalized.splitlines()
        for index, line in enumerate(lines):
            if line.strip() == "intro G _ h":
                normalized = "\n".join(lines[index + 1 :]).strip()
                actions.append("strip_submission_wrapper")
                break
    if "*" in normalized:
        normalized = normalized.replace("*", "◇")
        actions.append("replace_star_with_diamond")
    if "congr_arg" in normalized:
        normalized = normalized.replace("congr_arg", "congrArg")
        actions.append("replace_congr_arg_with_congrArg")
    return NormalizedProof(proof=normalized, actions=actions)


def has_forbidden_construct(proof: str) -> str | None:
    forbidden = ("sorry", "admit", "axiom", "unsafe", "import ", "def submission", "theorem ")
    for token in forbidden:
        if token in proof:
            return token.strip()
    return None


def wrap_true_certificate(proof_body: str) -> str:
    lines = proof_body.strip().splitlines()
    non_empty = [line for line in lines if line.strip()]
    if non_empty:
        min_indent = min(len(line) - len(line.lstrip()) for line in non_empty)
        lines = [line[min_indent:] if len(line) >= min_indent else line for line in lines]
    indented = "\n".join("  " + line if line.strip() else "" for line in lines)
    return "import JudgeProblem\n\n" "def submission : Goal := by\n" "  intro G _ h\n" f"{indented}\n"
```

- [ ] **Step 5: Run tests**

Run:

```bash
pytest -q tests/proof_bank/test_import_responses.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add src/math_distill_stage2/proof_bank/import_responses.py src/math_distill_stage2/proof_bank/judge_classification.py tests/proof_bank/test_import_responses.py
git commit -m "feat: extract proof bank responses"
```

---

### Task 6: Add Response Import Runner With Injectable Judge

**Files:**
- Modify: `tests/proof_bank/test_import_responses.py`
- Modify: `src/math_distill_stage2/proof_bank/import_responses.py`
- Create: `scripts/lean_certificates/proof_bank_import_responses.py`

- [ ] **Step 1: Add failing import-run test**

Append to `tests/proof_bank/test_import_responses.py`:

```python
import json
from pathlib import Path

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.proof_bank.import_responses import import_responses


def test_import_responses_writes_attempts_and_summary(tmp_path: Path):
    run_dir = tmp_path / "run"
    (run_dir / "raw_responses").mkdir(parents=True)
    write_jsonl(
        run_dir / "input_problems.jsonl",
        [
            {
                "schema_version": 1,
                "item_id": "000001",
                "problem_key": "implication:sig:1111111111111111:2222222222222222",
                "source_problem_id": "true_1_2",
                "source_dataset": "fixture",
                "eq1_id": 1,
                "eq2_id": 2,
                "equation1": "x = x",
                "equation2": "x = x",
                "expected_verdict": True,
            }
        ],
    )
    (run_dir / "manifest.json").write_text(
        json.dumps({"source_run_id": "run-1", "generator": {"model": "codex-gpt-5.5"}}),
        encoding="utf-8",
    )
    (run_dir / "raw_responses" / "000001.txt").write_text(
        '{"verdict":"true","proof":"intro x\\nexact rfl"}',
        encoding="utf-8",
    )

    def fake_judge(problem: dict, answer: dict) -> dict:
        assert answer["verdict"] == "true"
        assert "def submission : Goal := by" in answer["code"]
        return {"status": "accepted", "stderr": "", "stdout": "", "message": "", "error_code": ""}

    summary = import_responses(run_dir, judge=fake_judge)

    attempts = read_jsonl(run_dir / "generated_attempts.jsonl")
    assert summary["accepted_count"] == 1
    assert attempts[0]["attempt_id"] == "attempt:run-1:000001"
    assert attempts[0]["judge_status"] == "accepted"
    assert attempts[0]["certificate_sha256"]
    assert (run_dir / "summary.json").exists()
```

- [ ] **Step 2: Run failing test**

Run:

```bash
pytest -q tests/proof_bank/test_import_responses.py::test_import_responses_writes_attempts_and_summary
```

Expected: FAIL because `import_responses` is not implemented.

- [ ] **Step 3: Implement import runner**

Extend `src/math_distill_stage2/proof_bank/import_responses.py` with:

```python
from collections import Counter
from pathlib import Path
from typing import Any, Callable

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.proof_bank.judge_classification import classify_official_result
from math_distill_stage2.proof_bank.storage import (
    write_content_addressed_text,
    write_json,
)

JudgeFunction = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]


def import_responses(run_dir: Path, judge: JudgeFunction) -> dict[str, Any]:
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    source_run_id = str(manifest["source_run_id"])
    problems = read_jsonl(run_dir / "input_problems.jsonl")
    attempts: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    for problem in problems:
        item_id = str(problem["item_id"])
        raw_path = run_dir / "raw_responses" / f"{item_id}.txt"
        if not raw_path.exists():
            errors.append({"item_id": item_id, "error": "missing_raw_response"})
            counts["missing_response"] += 1
            continue
        raw_text = raw_path.read_text(encoding="utf-8")
        raw_store = write_content_addressed_text(run_dir, "raw_responses_by_hash", raw_text, ".txt")
        extracted = extract_response(raw_text)
        attempt_id = f"attempt:{source_run_id}:{item_id}"
        base = {
            "schema_version": 1,
            "attempt_id": attempt_id,
            "problem_key": problem["problem_key"],
            "certificate_kind": "true_proof",
            "generator_mode": "codex_task",
            "generator_tool": "VSCode Codex",
            "generator_model": manifest.get("generator", {}).get("model"),
            "raw_response_sha256": raw_store.sha256,
            "source_run_id": source_run_id,
            "created_at": manifest.get("created_at_utc"),
        }
        if extracted.error_kind:
            attempts.append(
                {
                    **base,
                    "judge_status": "skipped",
                    "official_judge_status": None,
                    "judge_error_kind": extracted.error_kind,
                    "judge_error_subkind": None,
                    "judge_error_summary": extracted.error_summary,
                }
            )
            counts["skipped"] += 1
            continue
        normalized = normalize_proof_body(extracted.proof)
        forbidden = has_forbidden_construct(normalized.proof)
        proof_store = write_content_addressed_text(run_dir, "proof_bodies", normalized.proof + "\n", ".lean")
        if forbidden:
            attempts.append(
                {
                    **base,
                    "proof_body_sha256": proof_store.sha256,
                    "normalization_actions": normalized.actions,
                    "judge_status": "skipped",
                    "official_judge_status": None,
                    "judge_error_kind": "forbidden_construct",
                    "judge_error_subkind": forbidden,
                    "judge_error_summary": f"Forbidden construct: {forbidden}",
                }
            )
            counts["skipped"] += 1
            continue
        code = wrap_true_certificate(normalized.proof)
        cert_store = write_content_addressed_text(run_dir, "certificates", code, ".lean")
        raw_result = judge(problem, {"call": "judge", "verdict": "true", "code": code})
        result_store = write_content_addressed_text(
            run_dir,
            "judge_results",
            json.dumps(raw_result, ensure_ascii=False, sort_keys=True) + "\n",
            ".json",
        )
        classification = classify_official_result(raw_result)
        attempts.append(
            {
                **base,
                "proof_body_sha256": proof_store.sha256,
                "certificate_sha256": cert_store.sha256,
                "normalization_actions": normalized.actions,
                "judge_result_sha256": result_store.sha256,
                **classification,
            }
        )
        counts[str(classification["judge_status"])] += 1

    write_jsonl(run_dir / "generated_attempts.jsonl", attempts)
    write_jsonl(run_dir / "extraction_errors.jsonl", errors)
    summary = {
        "source_run_id": source_run_id,
        "problem_count": len(problems),
        "attempt_count": len(attempts),
        "accepted_count": counts["accepted"],
        "rejected_count": counts["rejected"],
        "skipped_count": counts["skipped"],
        "error_count": counts["error"],
        "timeout_count": counts["timeout"],
        "missing_response_count": counts["missing_response"],
    }
    write_json(run_dir / "summary.json", summary)
    return summary
```

- [ ] **Step 4: Add CLI wrapper using official judge adapter**

Create `scripts/lean_certificates/proof_bank_import_responses.py`:

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))

from math_distill_stage2.official_stage2_judge import verify_official_stage2_answer
from math_distill_stage2.proof_bank.import_responses import import_responses


def official_judge(problem: dict, answer: dict) -> dict:
    result = verify_official_stage2_answer(problem, answer)
    return result.raw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import proof bank raw responses and verify with the official judge.")
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args(argv)
    summary = import_responses(args.run, judge=official_judge)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run tests**

Run:

```bash
pytest -q tests/proof_bank/test_import_responses.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add src/math_distill_stage2/proof_bank/import_responses.py scripts/lean_certificates/proof_bank_import_responses.py tests/proof_bank/test_import_responses.py
git commit -m "feat: import proof bank responses"
```

---

### Task 7: Add Run Merge Into Global Bank

**Files:**
- Create: `tests/proof_bank/test_merge_run.py`
- Modify: `src/math_distill_stage2/proof_bank/bank.py`
- Create: `scripts/lean_certificates/proof_bank_merge_run.py`

- [ ] **Step 1: Write failing merge tests**

Create `tests/proof_bank/test_merge_run.py`:

```python
import json
from pathlib import Path

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.proof_bank.bank import init_bank, merge_run


def test_merge_run_is_idempotent(tmp_path: Path):
    bank = tmp_path / "bank"
    run = tmp_path / "run"
    init_bank(bank)
    run.mkdir()
    (run / "manifest.json").write_text(json.dumps({"source_run_id": "run-1"}), encoding="utf-8")
    write_jsonl(
        run / "input_problems.jsonl",
        [
            {
                "schema_version": 1,
                "problem_key": "implication:sig:1111111111111111:2222222222222222",
                "problem_aliases": ["fixture:true_1_2"],
                "equation1": "x = x",
                "equation2": "x = x",
                "eq1_signature": "v0=v0",
                "eq2_signature": "v0=v0",
                "source_datasets": ["fixture"],
            }
        ],
    )
    write_jsonl(
        run / "generated_attempts.jsonl",
        [
            {
                "schema_version": 1,
                "attempt_id": "attempt:run-1:000001",
                "problem_key": "implication:sig:1111111111111111:2222222222222222",
                "certificate_kind": "true_proof",
                "certificate_sha256": "a" * 64,
                "judge_commit": "6805e2323018fbd8a85f41ca09fc33d74d5a02a5",
                "official_judge_status": "accepted",
                "judge_status": "accepted",
                "judge_error_kind": "none",
                "source_run_id": "run-1",
                "created_at": "2026-05-11T00:00:00Z",
            }
        ],
    )

    first = merge_run(bank, run)
    second = merge_run(bank, run)

    assert first["new_problems"] == 1
    assert first["new_attempts"] == 1
    assert second["new_problems"] == 0
    assert second["new_attempts"] == 0
    assert len(read_jsonl(bank / "attempts.jsonl")) == 1
    assert len(read_jsonl(bank / "accepted.jsonl")) == 1
```

- [ ] **Step 2: Run failing test**

Run:

```bash
pytest -q tests/proof_bank/test_merge_run.py
```

Expected: FAIL because `merge_run` is not implemented.

- [ ] **Step 3: Implement `merge_run`**

Append this to `src/math_distill_stage2/proof_bank/bank.py`:

```python
def merge_run(bank: Path, run_dir: Path) -> dict[str, Any]:
    init_bank(bank)
    existing_problems = read_jsonl(bank / "problems.jsonl")
    existing_attempts = read_jsonl(bank / "attempts.jsonl")
    problem_by_key = {row["problem_key"]: row for row in existing_problems}
    attempt_by_id = {row["attempt_id"]: row for row in existing_attempts}

    new_problems = 0
    for row in read_jsonl(run_dir / "input_problems.jsonl"):
        key = row["problem_key"]
        if key not in problem_by_key:
            problem_by_key[key] = {
                "schema_version": 1,
                "problem_key": key,
                "problem_aliases": row.get("problem_aliases", []),
                "eq1_id": row.get("eq1_id"),
                "eq2_id": row.get("eq2_id"),
                "equation1": row.get("equation1"),
                "equation2": row.get("equation2"),
                "eq1_signature": row.get("eq1_signature"),
                "eq2_signature": row.get("eq2_signature"),
                "expected_verdict": row.get("expected_verdict"),
                "first_seen_dataset": row.get("source_dataset"),
                "source_datasets": row.get("source_datasets") or [row.get("source_dataset")],
                "created_at": utc_now(),
            }
            new_problems += 1

    new_attempts = 0
    for row in read_jsonl(run_dir / "generated_attempts.jsonl"):
        attempt_id = row["attempt_id"]
        if attempt_id in attempt_by_id:
            if attempt_by_id[attempt_id] != row:
                raise ValueError(f"same attempt_id with different payload: {attempt_id}")
            continue
        attempt_by_id[attempt_id] = row
        new_attempts += 1

    write_jsonl(bank / "problems.jsonl", [problem_by_key[key] for key in sorted(problem_by_key)])
    write_jsonl(bank / "attempts.jsonl", [attempt_by_id[key] for key in sorted(attempt_by_id)])
    summary = rebuild_indexes(bank)
    return {
        "bank": str(bank),
        "run_dir": str(run_dir),
        "new_problems": new_problems,
        "new_attempts": new_attempts,
        "accepted_count": summary["accepted_count"],
    }
```

- [ ] **Step 4: Add CLI wrapper**

Create `scripts/lean_certificates/proof_bank_merge_run.py`:

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))

from math_distill_stage2.proof_bank.bank import merge_run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Merge a proof bank run into the global bank.")
    parser.add_argument("--bank", type=Path, required=True)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--write", action="store_true", help="Required to perform the merge.")
    args = parser.parse_args(argv)
    if not args.write:
        print(json.dumps({"dry_run": True, "bank": str(args.bank), "run": str(args.run)}, indent=2))
        return 0
    print(json.dumps(merge_run(args.bank, args.run), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run tests**

Run:

```bash
pytest -q tests/proof_bank/test_merge_run.py tests/proof_bank/test_bank_indexes.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add src/math_distill_stage2/proof_bank/bank.py scripts/lean_certificates/proof_bank_merge_run.py tests/proof_bank/test_merge_run.py
git commit -m "feat: merge proof bank runs"
```

---

### Task 8: Add CLI Smoke Tests

**Files:**
- Create: `tests/proof_bank/test_cli.py`

- [ ] **Step 1: Write CLI help tests**

Create `tests/proof_bank/test_cli.py`:

```python
import subprocess
import sys
from pathlib import Path


SCRIPTS = [
    "scripts/lean_certificates/proof_bank_init.py",
    "scripts/lean_certificates/proof_bank_build_prompt_pack.py",
    "scripts/lean_certificates/proof_bank_import_responses.py",
    "scripts/lean_certificates/proof_bank_merge_run.py",
    "scripts/lean_certificates/proof_bank_check.py",
    "scripts/lean_certificates/proof_bank_rebuild_indexes.py",
]


def test_proof_bank_cli_help_runs():
    root = Path(__file__).resolve().parents[2]
    for script in SCRIPTS:
        result = subprocess.run(
            [sys.executable, script, "--help"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, f"{script}: {result.stderr}"
        assert "proof" in result.stdout.lower()
```

- [ ] **Step 2: Run CLI tests**

Run:

```bash
pytest -q tests/proof_bank/test_cli.py
```

Expected: PASS.

- [ ] **Step 3: Run full proof bank test set**

Run:

```bash
pytest -q tests/proof_bank tests/skills/test_stage2_skills.py
```

Expected: PASS.

- [ ] **Step 4: Commit**

Run:

```bash
git add tests/proof_bank/test_cli.py
git commit -m "test: add proof bank cli smoke tests"
```

---

### Task 9: Document MVP Smoke Usage

**Files:**
- Modify: `docs/architecture.md`
- Create: `docs/experiments/2026-05-11-gpt-true-certificate-bank-mvp.md`

- [ ] **Step 1: Add experiment note**

Create `docs/experiments/2026-05-11-gpt-true-certificate-bank-mvp.md`:

```markdown
# GPT true certificate bank MVP

## 目标

记录第一版 `gpt_true_certificates` proof bank 的本地 smoke 使用方式。该流程只生成、验证、归档 true proof certificate attempts，不修改 `solver.py`。

## 标准流程

1. 初始化全局 bank：

```bash
python scripts/lean_certificates/proof_bank_init.py \
  --bank data/processed/proof_banks/gpt_true_certificates
```

2. 从候选池生成 prompt pack：

```bash
python scripts/lean_certificates/proof_bank_build_prompt_pack.py \
  --bank data/processed/proof_banks/gpt_true_certificates \
  --candidate-pool data/processed/proof_banks/gpt_true_certificates/candidate_pools/order4_true_unsolved_v1.jsonl \
  --run-id gpt-true-cert-order4-wide-20260511-001 \
  --limit 3
```

3. 使用 `stage2-proofbank-generate-true-certificate` 在当前 Codex 会话中读取 `prompt_pack/*.md`，并写入 `raw_responses/*.txt`。

4. 导入并验证 raw responses：

```bash
python scripts/lean_certificates/proof_bank_import_responses.py \
  --run artifacts/proof_bank_runs/2026-05-11/gpt-true-cert-order4-wide-20260511-001
```

5. 合并到全局 bank：

```bash
python scripts/lean_certificates/proof_bank_merge_run.py \
  --bank data/processed/proof_banks/gpt_true_certificates \
  --run artifacts/proof_bank_runs/2026-05-11/gpt-true-cert-order4-wide-20260511-001 \
  --write
```

6. 检查 bank：

```bash
python scripts/lean_certificates/proof_bank_check.py \
  --bank data/processed/proof_banks/gpt_true_certificates
```

## 边界

- 不使用 `test_locked` individual failures 建池。
- 不修改 `solver.py`。
- 不将 accepted certificate 自动写入 solver template。
```

- [ ] **Step 2: Run path/link grep**

Run:

```bash
rg -n "proof_bank_|gpt_true_certificates|stage2-proofbank" docs/experiments/2026-05-11-gpt-true-certificate-bank-mvp.md docs/architecture.md AGENTS.md
```

Expected: commands and paths appear exactly as intended; no misspelling of `gpt_true_certificates`.

- [ ] **Step 3: Commit**

Run:

```bash
git add docs/experiments/2026-05-11-gpt-true-certificate-bank-mvp.md docs/architecture.md AGENTS.md
git commit -m "docs: document proof bank mvp workflow"
```

---

## Final Verification

- [ ] **Step 1: Run focused tests**

Run:

```bash
pytest -q tests/proof_bank tests/skills/test_stage2_skills.py
```

Expected: PASS.

- [ ] **Step 2: Run CLI help smoke**

Run:

```bash
for script in \
  scripts/lean_certificates/proof_bank_init.py \
  scripts/lean_certificates/proof_bank_build_prompt_pack.py \
  scripts/lean_certificates/proof_bank_import_responses.py \
  scripts/lean_certificates/proof_bank_merge_run.py \
  scripts/lean_certificates/proof_bank_check.py \
  scripts/lean_certificates/proof_bank_rebuild_indexes.py
do
  python "$script" --help >/dev/null
done
```

Expected: every command exits 0.

- [ ] **Step 3: Confirm solver files untouched**

Run:

```bash
git diff -- solvers/solo_official submissions/solo_official
```

Expected: no output from this task.

- [ ] **Step 4: Check working tree scope**

Run:

```bash
git status --short
```

Expected: only files intentionally changed by this plan are present; unrelated pre-existing changes may remain and must not be reverted.
