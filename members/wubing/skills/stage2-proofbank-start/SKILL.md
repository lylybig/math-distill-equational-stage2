---
name: stage2-proofbank-start
description: Use when starting or continuing offline Stage 2 GPT/Codex true certificate bank generation, targeted strategy-gate singleton seed batches, proof bank batches, or Codex-assisted Lean certificate mining.
---

# Stage2 Proofbank Start

Coordinate offline true certificate bank generation. This workflow creates and verifies certificate attempts; it does not improve or edit `solver.py`.

For overnight, 24-hour, marathon, or continuously running proofbank expansion, use `stage2-proofbank-nightly-loop` instead of turning this bounded start workflow into an implicit infinite loop.

If an active strategy candidate needs proofbank evidence, prefer a bounded targeted proofbank gate over broad/nightly exploration. Current high-priority example:

- `true.proof.templatecheck.singleton_seedbank_specialization.top3_nontrivial_seedpool.v1`
- Goal: prove selected top residual source seeds imply Equation2 `x = y`, then use accepted seeds for exact strategy union/conflict review.
- Start with the phase-1 seed pool in `data/processed/proof_banks/gpt_true_certificates/candidate_pools/order5_top3_shape_singleton_like_sources_seed20260521.jsonl`; exclude seeds already accepted or already present in current seedbank/specialization evidence.

## Goal

Build `data/processed/proof_banks/gpt_true_certificates/` from Codex-generated true proof attempts that are verified by the official Stage 2 judge.

## Load Order

1. Use `stage2-proofbank-maintain` to inspect or initialize the bank.
2. Use `stage2-proofbank-sample-candidates` to explain source provenance and create or choose a reproducible sampled candidate pool, unless continuing an existing prompt pack.
3. Build or continue a bounded prompt pack from that sampled candidate pool.
4. Use `stage2-proofbank-generate-true-certificate` for 1-3 prompt items.
5. Use `stage2-proofbank-verify-import` to extract and judge raw responses.
6. Use `stage2-proofbank-maintain` to merge, rebuild indexes, and check the bank.
7. Use `stage2-proofbank-quality-audit` when deciding whether a larger loop should continue.

For targeted strategy-gate batches:

1. Record the strategy candidate key, seed source path, seed IDs, exclusion rules, and target theorem (`source -> x = y`) in the pool manifest or run manifest.
2. Keep batches bounded: 1-3 proof-generation items per invocation, with a checkpoint after every judge/import/merge cycle.
3. After accepted seeds are merged, hand back to the strategy total-control session to recompute source closure, raw coverage, exact union increment, and conflict count.

## Autonomy

You may create proof bank run directories, prompt packs, raw responses, judge artifacts, and global bank index updates. Keep batches to 1-3 Codex proof-generation items unless the user explicitly asks for more.

## Stop And Ask

Do not edit `solver.py`. Stop before using `test_locked` individual failures, adding known-proof tables, deleting bank ledgers, running large/paid/cloud batches, converting certificates into solver templates, or starting unbounded automatic proofbank expansion without explicit user authorization.

## Report

Report generated raw responses, accepted/rejected/skipped counts, bank path, source run id, targeted seed IDs when applicable, accepted seed IDs, and confirm that no solver files changed.
