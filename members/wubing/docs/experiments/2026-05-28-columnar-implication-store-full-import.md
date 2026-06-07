# Columnar Implication Store Full Import

Date: 2026-05-28

Store: `data/processed/order5_columnar_graph_store`

## Scope

Imported the active Stage 2/order5 strategy registry into the local columnar implication graph store:

- true `compiler_pair_indexes`: 27 active strategy rows
- true `explicit_pairs`: 1 active strategy row
- true `source_target_sets`: 22 active strategy rows
- false `explicit_pairs`: 1 active strategy row
- false finite-model/source-target `source_target_sets`: 305 active strategy rows
- final `rebuild-conflicts`

All active expected strategy ids had at least one evidence batch in the store after import.

## Final Counts

`summary --count-bits`:

```json
{
  "pair_count": 3915693200,
  "law_count": 62576,
  "layer_counts": {
    "true": 1386445377,
    "false": 2384904817,
    "approx_true": 0,
    "approx_false": 0,
    "conflict": 0
  }
}
```

Exact known pairs: 3,771,350,194.
Exact unknown pairs: 144,343,006.

Evidence batches: 404 JSONL rows.

## Import Notes

The false finite-model/source-target import used the live registry rules for the final pass. This matters for predicate-family rows, where the registered target set is the intersection refuted by all family models and the source set is a first-satisfying-model shard, not the full target complement for a single model.

The final `rebuild-conflicts` result:

```json
{
  "conflict_count": 0,
  "source_id": "rebuild_conflicts",
  "source_kind": "bitset_and"
}
```

## Representative Queries

True example:

```json
{
  "eq1_id": 519,
  "eq2_id": 472,
  "verdict": "true"
}
```

False example:

```json
{
  "eq1_id": 1,
  "eq2_id": 2,
  "verdict": "false"
}
```

Solved-row examples:

- source `519`: 62,575 true, 0 unknown
- source `472`: 62,575 true, 0 unknown
- source `1`: 62,575 false, 0 unknown

Frontier example for further mining:

- source `10000`: 4 true, 62,414 false, 157 unknown
- first frontier targets: `1, 47, 49, 359, 375, 614, 616, 619, 622, 625, 817, 819`
- `10000 -> 1` is unknown; `10000 -> 2` is false

## Verification

```text
18 passed in 0.53s
```

Tests:

- `tests/data/test_order5_columnar_graph_store.py`
- `tests/data/test_order5_pair_space.py`
