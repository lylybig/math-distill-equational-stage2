---
name: stage2-proofbank-maintain
description: Use when merging, checking, rebuilding, initializing, or auditing the global Stage 2 GPT true certificate proof bank.
---

# Stage2 Proofbank Maintain

Maintain the global proof bank at `data/processed/proof_banks/gpt_true_certificates/`.

## Modes

- `init`: create an empty bank manifest, ledgers, indexes, and content directories.
- `merge`: merge a proof bank run into the global bank. `scripts/lean_certificates/proof_bank_merge_run.py` without `--write` performs a validating dry-run and must be run before the write merge.
- `check`: validate hashes, schemas, problem keys, content files, accepted evidence, and derived indexes.
- `rebuild`: regenerate `accepted.jsonl`, `latest_by_problem.jsonl`, and `bank_summary.json`.

## Rules

Run dry-run before write for merge. Treat `attempts.jsonl` and `problems.jsonl` as source ledgers. Treat accepted/latest/summary as derived indexes. Stop on same attempt id with different hashes, problem key signature mismatch, missing content files, or accepted attempts without official accepted judge evidence.

## Constraints

Do not generate proofs, run Codex proof synthesis, modify `solver.py`, export submissions, or select solver templates.

## Report

Report new problems, attempts, accepted records, skipped duplicates, hard errors, and final bank check status.

For long-running quality decisions after structural checks pass, use `stage2-proofbank-quality-audit`; this skill checks ledger integrity, not source balance or accepted yield strategy.
