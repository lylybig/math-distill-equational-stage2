# ETP Lifting-Family Infinite Counterexamples

Date: 2026-05-28

This note records a scan of the non-finite counterexample patterns referenced
from the upstream Equational Theories Lean files:

- `equational_theories/LiftingMagmaFamilies.lean`
- `equational_theories/Generated/InvariantMetatheoremNonimplications/instLiftingMagmaFamilyList_counterexamples.lean`
- `equational_theories/Generated/InvariantMetatheoremNonimplications/instLiftingMagmaFamilyMultiset_counterexamples.lean`
- `equational_theories/Generated/InvariantMetatheoremNonimplications/instLiftingMagmaFamilyFinset_counterexamples.lean`
- `equational_theories/Generated/InvariantMetatheoremNonimplications/instLiftingMagmaFamilyLeftProj_counterexamples.lean`
- `equational_theories/Generated/InvariantMetatheoremNonimplications/instLiftingMagmaFamilyRightProj_counterexamples.lean`

## Scan

Command:

```bash
uv run python scripts/data/build_order5_infinite_model_counterexamples.py \
  --coverage-profile-json data/processed/order5_strategy_registry/candidates/current_coverage_profile_v29_active_true_tail_rescore_20260528.json
```

Generated files:

```text
data/processed/order5_strategy_registry/candidates/false_infinite_model_lifting_families_20260528.jsonl
data/processed/order5_strategy_registry/candidates/false_infinite_model_lifting_families_20260528_summary.json
```

The scanner treats an equation as satisfied by a lifting family when its two
sides have the same normal form:

- List append: leaf sequence
- Multiset add: variable-count multiset
- Finset union: variable set
- Left projection: leftmost leaf
- Right projection: rightmost leaf

For an implication `source -> target`, any family satisfying the source and
refuting the target gives an exact false source/target rectangle.

## Results

Compared with
`current_coverage_profile_v29_active_true_tail_rescore_20260528.json`, all five
families had zero incremental false coverage and zero conflicts:

| family | source count | target count | raw coverage | current union increment |
| --- | ---: | ---: | ---: | ---: |
| list_append | 6 | 62570 | 375420 | 0 |
| multiset_add | 32 | 62544 | 2001408 | 0 |
| finset_union | 1430 | 61146 | 87438780 | 0 |
| left_projection | 14612 | 47964 | 700849968 | 0 |
| right_projection | 14612 | 47964 | 700849968 | 0 |

The projection families are expected to overlap heavily with existing finite
projection/setcheck countermodels. The scan confirms that, in the current v29
coverage profile, the list, multiset, and finset lifting-family rectangles are
also already covered by active false strategies.

## Usefulness

These Lean references are still useful as semantic documentation and as a
sanity check that Stage 2 false goals can be witnessed by non-finite models, but
they are not a new direct coverage source against the current registry snapshot.

The most practical follow-up is to keep the scanner available for future
coverage profiles: if finite/setcheck strategy selection changes, these
families provide a quick exact audit for missed non-finite counterexamples.

## Subgraph.lean Check

`Subgraph.lean` is different from the lifting-family files: it contains a small
curated subgraph, mostly one theorem per implication/nonimplication, not a large
normal-form family.

Parsing the actual theorem statements, including the `Facts G [5] [42, 43,
4513]` theorem and one name/statement mismatch on
`Equation43_not_implies_Equation39`, gives 53 Stage2-range false pairs. Against
the v29 profile, 52 are already covered and there are no true conflicts. The
only missing direct pair is:

```text
4582 -> 43
```

The Lean proof for `Equation4582_not_implies_Equation43` uses `Nat` with

```text
x * y = if x = 1 and y = 2 then 3 else 4
```

This witness compresses to the finite `Fin 5` table with the same operation. On
the full order<=5 equation list, that table satisfies 12,331 equations and
refutes 50,245 equations, for 619,571,095 raw false pairs. Compared with v29 it
adds 26 deterministic false pairs and has zero conflicts:

```text
(314, 4131), (318, 4131), (321, 4131),
(363, 3306), (366, 3306), (373, 3306),
(4526, 43), (4531, 43), (4534, 43), (4535, 43),
(4539, 43), (4543, 43), (4547, 43), (4552, 43),
(4553, 43), (4556, 43), (4558, 43), (4561, 43),
(4562, 43), (4566, 43), (4567, 43), (4568, 43),
(4571, 43), (4577, 43), (4578, 43), (4582, 43)
```

So `Subgraph.lean` is the more actionable reference from this pass: not a broad
new family, but it reveals one compact finite model whose active-registry delta
is 26 false edges.

Generated candidate summary:

```text
data/processed/order5_strategy_registry/candidates/false_etp_subgraph_fin5_4582_countermodel_delta_20260528.json
```

## Formal InfModel Counterexamples

`InfModel.lean` contains the formal Lean examples for Austin-style phenomena:
finite magmas can force an implication, while an infinite magma refutes it in
ordinary magma semantics.

Command:

```bash
uv run python scripts/data/build_order5_etp_infinite_fact_candidates.py
```

Generated files:

```text
data/processed/order5_strategy_registry/candidates/false_etp_infmodel_counterexamples_20260528.jsonl
data/processed/order5_strategy_registry/candidates/false_etp_infmodel_counterexamples_20260528_summary.json
```

Against v29, the formal `InfModel.*_not_implies_*` facts add three false edges
and have zero conflicts:

| theorem | false pair | current union increment |
| --- | ---: | ---: |
| `InfModel.Equation28770_not_implies_Equation2` | `28770 -> 2` | 1 |
| `InfModel.Equation3994_not_implies_Equation3588` | `3994 -> 3588` | 1 |
| `InfModel.Equation3588_not_implies_Equation3994` | `3588 -> 3994` | 1 |

The order<=4 `data/Austin_implications.txt` file has 820 pairs. A v29 profile
check reports all 820 as currently unknown in the ordinary true/false profile:
zero are marked true and zero are marked false. That is expected because these
are finite-model implications but ordinary-magma nonimplications. They should
not be solved by finite countermodel search, and they should not be imported as
ordinary true implications.

For exact registry promotion, use the formal Lean facts where available
(`InfModel.lean` today exposes only a small subset as structured entries), or
add a separate certificate policy for the Austin data file.
