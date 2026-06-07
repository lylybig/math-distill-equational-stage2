# Residual-1000 v3 Sample Prep

Date: 2026-06-02

## Goal

Prepare an independent `residual-1000-v3` ProofBench sample for follow-up
comparative experiments. The draw uses the current columnar exact-unknown layer
and is checked against both prior 1000-row residual samples.

## Source Command

Run from `members/wubing`:

```bash
uv run python scripts/data/sample_order5_columnar_exact_unknown.py \
  --sample-size 1000 \
  --seed 20260602 \
  --output-stem current_residual_columnar_exact_unknown_1000_seed20260602_v3
```

## Source Summary

- Sampling scope: `columnar_exact_unknown_true_false_layers`
- Seed: `20260602`
- Selected rows: `1000`
- Exact true count: `1,394,642,798`
- Exact false count: `2,387,094,132`
- Conflict count: `0`
- Exact unknown count: `133,956,270`
- Random candidate draws: `28,831`
- Draw acceptance rate: `0.034684887794387984`

Strata:

| stratum | count |
| --- | ---: |
| `order4_source_to_order4_target` | `5` |
| `order4_source_to_order5_target` | `41` |
| `order5_source_to_order4_target` | `74` |
| `order5_source_to_order5_target` | `880` |

## Artifacts

Source workspace artifacts, under
`members/wubing/data/processed/order5_strategy_registry/`:

- `current_residual_columnar_exact_unknown_1000_seed20260602_v3_sample.jsonl`
- `current_residual_columnar_exact_unknown_1000_seed20260602_v3_buckets.json`
- `current_residual_columnar_exact_unknown_1000_seed20260602_v3_summary.json`

ProofBench artifacts:

- `../math-distill-stage2-proofbench/math-distill-stage2-proofbench/data/residual-1000-v3/problems.jsonl`
- `../math-distill-stage2-proofbench/math-distill-stage2-proofbench/data/residual-1000-v3/shape_buckets.json`
- `../math-distill-stage2-proofbench/math-distill-stage2-proofbench/data/residual-1000-v3/manifest.json`

Hashes:

- Source sample SHA-256:
  `d43badd98a87d673766725d68f75eeabc93fe03ba8b5352aa12487f14ef5f07e`
- Source buckets SHA-256:
  `319518a11f8cdeb8d96d8f750352e46ea3eee62669e7970cea8b4fad41480f02`
- ProofBench problems SHA-256:
  `eaf552c80b6c5cd7ad050d88a58f12240e9a87ca5e85a6adab355ed1d8f117dd`

## Validation

- `data/residual-1000-v3/problems.jsonl` has `1000` rows.
- Unique ProofBench ids: `1000`.
- Unique pair indexes: `1000`.
- Unique eq-pairs: `1000`.
- Pair-index overlap with `residual-1000-v1`: `0`.
- Eq-pair overlap with `residual-1000-v1`: `0`.
- Pair-index overlap with `residual-1000-v2`: `0`.
- Eq-pair overlap with `residual-1000-v2`: `0`.
- `uv run pytest tests/test_common.py tests/test_tools.py` in the ProofBench
  workspace: `14 passed`.
- `proofbench-route-problem` now routes v3 ids to
  `data/residual-1000-v3/problems.jsonl`.

Initial metadata-only route distribution:

| route kind | count |
| --- | ---: |
| `explicit_hinst_grind` | `410` |
| `z3_guided_true_then_finite` | `341` |
| `shape_playbook` | `114` |
| `finite_first` | `80` |
| `direct_true` | `55` |

Current-router comparison across the three 1000-row residual samples:

| sample | explicit_hinst_grind | z3_guided_true_then_finite | shape_playbook | finite_first | direct_true |
| --- | ---: | ---: | ---: | ---: | ---: |
| `residual-1000-v1` | `404` | `335` | `115` | `102` | `44` |
| `residual-1000-v2` | `390` | `322` | `131` | `96` | `61` |
| `residual-1000-v3` | `410` | `341` | `114` | `80` | `55` |

Initial metadata-only route for `residual1000_v3_0001`:

- route kind: `z3_guided_true_then_finite`
- command paths include `data/residual-1000-v3/problems.jsonl`

## Use

For an initial v3 route recommendation:

```bash
uv run proofbench-route-problem \
  --problems data/residual-1000-v3/problems.jsonl \
  --ids 1 \
  --format json
```
