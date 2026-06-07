# Order5 Columnar Implication Store Demo

Date: 2026-05-28

This note records a small end-to-end check that the local columnar implication
store is useful for deterministic true/false strategy mining.

## Store

Demo store:

```bash
data/processed/order5_columnar_graph_store_demo_goal
```

The store uses five mmap-backed bitset layers over the implicit directed
order<=5 pair space:

- `true`
- `false`
- `approx_true`
- `approx_false`
- `conflict`

Each layer has `3,915,693,200` bits.

## True Example

Strategy:

```text
true.proof.templatecheck.opnorm.hconst_match_collapse.varmul_top01_source0000_0500.v1
```

Pair-index cache:

```bash
data/processed/order5_strategy_registry/opnorm_hconst_varmul_top01_source0000_0500_pair_indexes_20260521.txt
```

Preview before import showed:

```json
{
  "read_count": 73400,
  "newly_set_count": 73400,
  "already_set_count": 0,
  "conflict_count": 0
}
```

Import wrote all `73,400` true edges with zero conflicts. A source-row query for
source equation `519` showed:

```json
{
  "true": 367,
  "false": 0,
  "conflict": 0,
  "exact_known_count": 367,
  "unknown_count": 62208
}
```

This is useful for true mining because the pair-index cache has a clear cluster
shape: high-frequency sources each gain `367` true targets, and high-frequency
targets each receive `200` incoming true hits. That gives a concrete frontier:
for a source like `519`, the graph can immediately separate proven targets from
the remaining unknown row.

Example solved query:

```json
{
  "eq1_id": 519,
  "eq2_id": 472,
  "pair_index": 32414321,
  "verdict": "true"
}
```

## False Example

Strategy manifest row:

```text
false.finmodel.predicatecheck.etp_prefix_family.k40.source_any_target_all_refuted.witness_shard_14_etp_refutation195.v1
```

The manifest row registers a filtered false subcluster:

```json
{
  "manifest_source_count": 6,
  "manifest_target_count": 47318,
  "manifest_coverage_count": 283908
}
```

The finite-model adapter recomputed the full satisfied/refuted partition for the
same model table:

```json
{
  "computed_source_count": 1794,
  "computed_target_count": 60782,
  "newly_set_count": 109042908,
  "conflict_count": 0
}
```

This is useful for false mining because the model table supports a much larger
deterministic false rectangle than the filtered registry row recorded. The graph
store can therefore reveal safe expansion opportunities for finite-model
counterexample strategies.

For source equation `1`, the false row now has:

```json
{
  "true": 0,
  "false": 60782,
  "conflict": 0,
  "exact_known_count": 60782,
  "unknown_count": 1793
}
```

The remaining frontier starts with:

```json
{
  "source_id": 1,
  "unknown_count": 1793,
  "targets": [40, 307, 309, 310, 312, 313, 316, 319, 320, 3253, 3255, 3256]
}
```

Example solved query:

```json
{
  "eq1_id": 1,
  "eq2_id": 2,
  "pair_index": 0,
  "verdict": "false"
}
```

## Layer Counts

After both imports:

```json
{
  "true": 73400,
  "false": 109042908,
  "approx_true": 0,
  "approx_false": 0,
  "conflict": 0
}
```

The demo store occupies about `127M` on disk because the bitset files are sparse.

## Useful Commands

Preview a pair-index-backed strategy row from `strategies.json`:

```bash
./.venv/bin/python scripts/data/build_order5_columnar_graph_store.py \
  preview-pair-index-strategy-row \
  --store-dir data/processed/order5_columnar_graph_store_demo_goal \
  --strategy-id true.proof.templatecheck.opnorm.hconst_match_collapse.varmul_top01_source0000_0500.v1
```

Preview a finite-model false strategy row from `strategies.json`:

```bash
./.venv/bin/python scripts/data/build_order5_columnar_graph_store.py \
  preview-finmodel-strategy-row \
  --store-dir data/processed/order5_columnar_graph_store_demo_goal \
  --strategy-id false.finmodel.predicatecheck.etp_prefix_family.k40.source_any_target_all_refuted.witness_shard_14_etp_refutation195.v1
```

Inspect one source row:

```bash
./.venv/bin/python scripts/data/build_order5_columnar_graph_store.py \
  row-summary \
  --store-dir data/processed/order5_columnar_graph_store_demo_goal \
  --source-id 1
```

List unknown frontier targets for a source:

```bash
./.venv/bin/python scripts/data/build_order5_columnar_graph_store.py \
  frontier \
  --store-dir data/processed/order5_columnar_graph_store_demo_goal \
  --source-id 1 \
  --limit 20
```
