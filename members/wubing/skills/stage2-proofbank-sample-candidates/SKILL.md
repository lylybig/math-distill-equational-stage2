---
name: stage2-proofbank-sample-candidates
description: Use when selecting Stage 2 true implication candidates for proof bank prompt packs, targeted strategy-gate singleton seed pools, proofbank nightly sampling, reproducible stratified random sampling, or explaining proofbank candidate pool provenance.
---

# Stage2 Proofbank Sample Candidates

Prepare true candidate pools before building proof bank prompt packs. The default method is train/run 过程数据优先的可复现分层随机抽样（reproducible stratified random sampling）. This skill samples problems only; it does not generate proofs, call the judge, merge the bank, or improve `solver.py`.

When a strategy candidate needs proofbank evidence, targeted sampling takes precedence over default broad sampling. Do not dilute a targeted singleton-seed gate with unrelated order4/direct exploration rows unless the user explicitly asks for a broad/nightly run.

## Current Provenance

- Existing pools live under `data/processed/proof_banks/gpt_true_certificates/candidate_pools/`.
- `order4_true_high_signal_failed_attempts_v1.jsonl` and `order4_true_unsolved_v1.jsonl` are derived from true failures in `artifacts/runs/2026-05-09/order4-v9-dev-main-w8-overnight` on `data/processed/order4_splits/dev_main.jsonl`.
- `dev_main` is a deterministic split sampled from `data/processed/order4_implication_problems/`, whose manifest records `22028942` order4 directed implication rows and seed `20260508`.
- Therefore current proofbank pools are downstream of the 22M order4 corpus, but they are not uniform samples from the full 22M rows.
- Long-running or nightly proofbank sampling must include direct true-row exploration from `data/processed/order4_implication_problems/`. `dev_main` should be treated as a high-signal failure source, not as the whole exploration universe.
- Smaller split sources such as `stress_true` are useful smoke pools, but they do not replace 22M direct order4 sampling.

## Targeted Strategy-Gate Pools

Use this mode when a strategy candidate needs accepted source-level certificates before exact registry review. Current example:

- candidate: `true.proof.templatecheck.singleton_seedbank_specialization.top3_nontrivial_seedpool.v1`
- seed source: `data/processed/order5_strategy_registry/top3_source_nontrivial_model_probe_120_seed20260521.json`
- phase-1 seed pool: `data/processed/proof_banks/gpt_true_certificates/candidate_pools/order5_top3_shape_singleton_like_sources_seed20260521.jsonl`
- target problem shape: `eq1_id=<seed source>`, `eq2_id=2`, `equation2="x = y"`, `expected_verdict=true`

For targeted pools:

1. Record `strategy_candidate_key`, source seed path, selected seed IDs, exclusion rules, and target theorem in the manifest.
2. Exclude seeds already accepted by the proof bank or already present in current singleton seedbank/specialization evidence. For the current top3 singleton-like pool, `10653` may already be accepted and should be excluded unless intentionally rechecked.
3. Prefer phase-1 batches of 1-3 prompt items; a pool may list more seeds, but generation remains checkpointed.
4. Do not claim finite nontrivial model probe results are proof evidence. They are prioritization only until remote judge accepts the source-level singleton certificate.
5. Do not turn accepted seed certificates into a pair-level known-proof table. The downstream use is seedbank specialization source closure and exact strategy union/conflict review.

## Default Sampling Policy

Write a sampled pool and manifest:

```text
data/processed/proof_banks/gpt_true_certificates/candidate_pools/<pool_id>.jsonl
data/processed/proof_banks/gpt_true_certificates/candidate_pools/<pool_id>.manifest.json
```

Use `scripts/lean_certificates/proof_bank_sample_candidates.py` for reproducible stratified random sampling:

1. Record `pool_id`, `seed`, source paths, source row counts, output count, selector version, stratum weights, exclusion rules, and timestamp in the manifest.
2. Deduplicate by `problem_key` recomputed from `equation1` and `equation2`; keep the row with the highest `priority_score`.
3. Exclude problems with accepted true certificates in `accepted.jsonl`, unless the user explicitly asks for revisits.
4. Exclude problems that already have too many attempts; default ceiling is 3 attempts per `problem_key`.
5. Allocate samples by strata, then sample without replacement inside each stratum using a deterministic RNG from `seed`.

Default broad/nightly strata:

```text
rejected_attempt_repair: 0.35
high_signal_failed_attempts: 0.65
unsolved_trace_or_timeout: 0.20
direct_order4_true_exploration: 0.15
```

`rejected_attempt_repair` is generated from existing non-accepted proof bank attempts with official judge feedback and is enabled by `--repair-from-bank` in the sampler and by default in the nightly loop. It carries the previous error kind, error summary, and proof excerpt when available. The high-signal and unsolved strata are train/process-data first. The 22M direct sampling stratum is a smaller exploration layer because proof generation and judge verification are slow.

For `direct_order4_true_exploration`, the sampler must draw from `data/processed/order4_implication_problems/` shards and keep only rows whose label is true. Do not satisfy this stratum from `dev_main`; using `stress_true` is acceptable only for smoke runs and must be recorded as a degraded source.

If a stratum is unavailable, redistribute its quota across available strata and record that in the manifest. Within a stratum, weight rows by `priority_score` when present; otherwise use uniform weight. Tie-break stable ordering by `problem_key` before random selection. The final candidate pool is deduplicated by `problem_key` across strata so repair candidates do not duplicate high-signal candidates in the same prompt pack.

## Workflow

1. Inspect `bank_summary.json`, `accepted.jsonl`, `attempts.jsonl`, and available `candidate_pools/`.
2. State the source provenance: whether the pool is from `dev_main` solver failures, a split such as `stress_true`, or direct 22M order4 shard sampling.
3. Choose a bounded output size. For nightly planning, 50-100 sampled candidates is reasonable; for immediate Codex generation, keep prompt generation to 1-3 items.
4. Create the sampled pool and manifest. Do not overwrite an existing pool id.
5. Build the prompt pack from the sampled pool with `scripts/lean_certificates/proof_bank_build_prompt_pack.py`. The builder embeds skill guidance by default; override `--generation-skill-path` or `--lean-proof-skill-path` for strategy experiments, and use `--no-etp-context` only for ETP ablations.
6. Hand off to `stage2-proofbank-generate-true-certificate` for raw proof responses.

## Stop And Ask

Stop before sampling from `test_locked` individual failures, running paid/cloud/bulk jobs, overwriting candidate pools, deleting bank ledgers, or converting selected/accepted certificates into solver templates.

## Constraints

Do not edit `solver.py`. Do not call the judge. Do not claim sampled candidates are solved or accepted. A sampled pool is only a reproducible input selection artifact.

## Report

Report pool path, manifest path, seed, source counts, selected count by stratum or seed list, exclusions from accepted/attempt ceilings, targeted strategy candidate key when applicable, and the exact prompt-pack command to run next.
