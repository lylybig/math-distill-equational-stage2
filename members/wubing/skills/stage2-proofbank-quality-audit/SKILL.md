---
name: stage2-proofbank-quality-audit
description: Use when auditing Stage 2 proofbank quality, accepted yield, targeted strategy-gate seed progress, source balance, candidate diversity, long-running proofbank health, or readiness to continue a proofbank loop.
---

# Stage2 Proofbank Quality Audit

Audit proofbank quality beyond structural ledger checks. Use this after merge/check in long-running loops and before deciding whether to continue generation.

Use `scripts/lean_certificates/proof_bank_quality_audit.py` for the executable audit. It reads existing artifacts only; it does not call the judge or generate proofs.

## Inputs

Inspect:

- `data/processed/proof_banks/gpt_true_certificates/bank_summary.json`
- `accepted.jsonl`, `attempts.jsonl`, `latest_by_problem.jsonl`
- current sampled pool manifest
- current proof bank run `summary.json`
- `marathon_state.json` when present
- strategy candidate file/summary when the run is a targeted strategy gate

## Checks

- accepted yield: accepted attempts divided by generated attempts for the current cycle and recent window
- source balance: for broad/nightly loops, high-signal failures, unsolved trace/timeouts, and direct 22M order4 true exploration are all represented over the recent window
- targeted strategy-gate progress: accepted seed IDs, rejected/timeout seed IDs, remaining seed IDs, and whether the accepted set is sufficient to hand back to exact strategy union/conflict review
- diversity: avoid overconcentration by repeated `eq1_id`, `eq2_id`, source split, or identical equation signatures
- freshness: accepted problems are excluded from later sampled pools unless revisits were explicitly requested
- attempt pressure: problems over the attempt ceiling are not repeatedly resampled
- evidence: every accepted true certificate has official judge `accepted` evidence
- error mix: malformed, timeout, judge, and Lean error rates are not dominated by one broken mode

## Decisions

- `continue`: quality gates are healthy.
- `continue_with_adjusted_sampling`: continue after shifting weights toward underrepresented strata.
- `handoff_to_strategy_gate`: targeted proofbank accepted enough seed evidence; stop proof generation and ask total-control to recompute source closure, exact union increment, and conflict count.
- `pause_for_debug`: stop the loop and inspect generator, judge, or candidate selection.
- `stop_complete`: timebox or target count reached.

## Constraints

Do not edit `solver.py`, modify bank ledgers, call the judge, synthesize proofs, use `test_locked` individual failures, or select solver templates.

## Report

Report accepted yield, source balance or targeted seed progress, diversity notes, top error kinds, exclusions, recommended decision, and the exact artifact paths inspected.
