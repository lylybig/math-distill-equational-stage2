---
name: stage2-proofbank-verify-import
description: Use when importing Codex-generated proof bank responses, extracting Lean proof bodies, wrapping Stage 2 certificates, or verifying with the official judge.
---

# Stage2 Proofbank Verify Import

Turn proof bank raw responses into deterministic attempt records using the official Stage 2 judge.

## Workflow

1. Read the proof bank run manifest, input problems, prompt pack, and raw responses.
2. Extract proof bodies from strict JSON, common proof-field aliases, nested answer payloads, fenced JSON, fenced Lean, or bare Lean fallback.
3. Run preflight for forbidden constructs.
4. Wrap proof bodies with the Stage 2 true certificate wrapper.
5. Verify with the official Stage 2 judge through the remote judge-v2 backend.
   Default `remote-http` is an alias for `remote-judge-v2` and points to
   `http://10.220.69.172:8890`. Use judge-v2 `/jobs` for Lean certificate
   verification.
6. Write `generated_attempts.jsonl`, `judge_results/`, `proof_bodies/`, `certificates/`, `extraction_errors.jsonl`, and `summary.json`.

## Constraints

Do not synthesize or repair proofs, modify `solver.py`, modify the global bank, use local Docker/Lean for batch judge verification, or treat non-accepted judge results as accepted certificates.

## Report

Report attempt count, accepted/rejected/skipped/error/timeout counts, top error kinds, and the run artifact path.
