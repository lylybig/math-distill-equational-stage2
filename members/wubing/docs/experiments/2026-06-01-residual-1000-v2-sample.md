# Residual-1000 v2 Sample Prep

Date: 2026-06-01

## Goal

Prepare an independent `residual-1000-v2` ProofBench sample for follow-up
comparative experiments, using the current columnar exact-unknown layer rather
than reusing the 2026-05-29 `residual-1000-v1` draw.

## Source Command

Run from `members/wubing`:

```bash
uv run python scripts/data/sample_order5_columnar_exact_unknown.py \
  --sample-size 1000 \
  --seed 20260601 \
  --output-stem current_residual_columnar_exact_unknown_1000_seed20260601_v2
```

## Source Summary

- Sampling scope: `columnar_exact_unknown_true_false_layers`
- Seed: `20260601`
- Selected rows: `1000`
- Exact true count: `1,394,642,074`
- Exact false count: `2,387,094,055`
- Conflict count: `0`
- Exact unknown count: `133,957,071`
- Random candidate draws: `28,234`
- Draw acceptance rate: `0.03541829000495856`

Strata:

| stratum | count |
| --- | ---: |
| `order4_source_to_order4_target` | `3` |
| `order4_source_to_order5_target` | `52` |
| `order5_source_to_order4_target` | `57` |
| `order5_source_to_order5_target` | `888` |

## Artifacts

Source workspace artifacts, under
`members/wubing/data/processed/order5_strategy_registry/`:

- `current_residual_columnar_exact_unknown_1000_seed20260601_v2_sample.jsonl`
- `current_residual_columnar_exact_unknown_1000_seed20260601_v2_buckets.json`
- `current_residual_columnar_exact_unknown_1000_seed20260601_v2_summary.json`

ProofBench artifacts:

- `../math-distill-stage2-proofbench/math-distill-stage2-proofbench/data/residual-1000-v2/problems.jsonl`
- `../math-distill-stage2-proofbench/math-distill-stage2-proofbench/data/residual-1000-v2/shape_buckets.json`
- `../math-distill-stage2-proofbench/math-distill-stage2-proofbench/data/residual-1000-v2/manifest.json`

Hashes:

- Source sample SHA-256:
  `85706576cf0fba61152f04c79b7ca93712fd14183363e421d90eee9e3dc777f7`
- Source buckets SHA-256:
  `547f05a23499b9f9fa852a99a17b8d3da94d94fedb670f505596ec1c9fc842de`
- ProofBench problems SHA-256:
  `e0714803405ae080eb3abf62ce34aa6b1a74f875ef19dd66596227c0435f52db`

## Validation

- `data/residual-1000-v2/problems.jsonl` has `1000` rows.
- Unique ProofBench ids: `1000`.
- Unique pair indexes: `1000`.
- Pair-index overlap with `residual-1000-v1`: `0`.
- Eq-pair overlap with `residual-1000-v1`: `0`.
- `uv run pytest tests/test_common.py tests/test_tools.py` in the ProofBench
  workspace: `14 passed`.
- `proofbench-route-problem` now routes v2 ids to
  `data/residual-1000-v2/problems.jsonl`.

Initial metadata-only route distribution:

| route kind | count |
| --- | ---: |
| `explicit_hinst_grind` | `390` |
| `z3_guided_true_then_finite` | `322` |
| `shape_playbook` | `131` |
| `finite_first` | `96` |
| `direct_true` | `61` |

## Use

For an initial v2 route recommendation:

```bash
uv run proofbench-route-problem \
  --problems data/residual-1000-v2/problems.jsonl \
  --ids 1 \
  --format json
```
