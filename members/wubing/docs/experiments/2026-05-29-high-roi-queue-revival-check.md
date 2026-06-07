# 2026-05-29 High ROI Queue Revival Check

## Scope

Refreshed the order5 candidate index and merge-review queue, then checked whether
the current high-ROI queue still contains actionable mainline strategy packets
against the local columnar graph store.

Commands:

```bash
./.venv/bin/python scripts/data/update_order5_strategy_mining_state.py --no-codex-sessions
./.venv/bin/python scripts/data/build_order5_strategy_merge_review_queue.py --main-gate 1000000 --tail-gate 100000
./.venv/bin/python scripts/data/build_order5_columnar_graph_store.py summary --store-dir data/processed/order5_columnar_graph_store
```

## Refreshed Queue

Baseline from the refreshed queue:

- total pairs: `3,915,693,200`
- deterministic false: `2,384,904,817`
- deterministic true: `1,394,597,946`
- unresolved estimate: `136,190,437`
- conflict count: `0`

Queue counts:

- `needs_rescore_or_smoke_main`: `19`
- `certificate_blocked_high_roi`: `29`
- `postedge7_controller_review`: `2`
- `tail_candidates`: `355`
- `register_ready_main`: `0`

## True Queue Finding

All ten `needs_rescore_or_smoke_main` true candidates with pair-index caches
were already fully covered by the current graph true layer:

- graph preview total result for each checked packet: `newly_set_count = 0`
- conflict count for each checked packet: `0`
- checked old increments ranged from `1,772,871` to `7,894,300`

Representative examples:

| candidate | old increment | remote smoke | graph newly set |
| --- | ---: | ---: | ---: |
| `true.proof.templatecheck.opnorm.hconst_combined.match_all_plus_default_sandwich_all` | `7,894,300` | `1010/1010` | `0` |
| `true.proof.templatecheck.opnorm.hconst_combined.match_all_plus_default_sandwich_ge25` | `6,985,734` | `722/722` | `0` |
| `true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.all_components` | `6,649,067` | `658/658` | `0` |
| `true.proof.templatecheck.evidence_guided.hinst_grind.ground_cc.mul_top_residual_shapes.main.v1` | `1,772,871` | not in summary | `0` |

Interpretation: these true queue rows are stale from the current graph point of
view. They should be routed to merged/subsumed or accounted-by-current-family
before spending more smoke or merge-review attention.

## False Queue Finding

Two false lanes were checked against current graph false/true layers by
recomputing finite-model partitions and doing a read-only source-target block
preview.

### `mod17` accepted packet

Input:

```text
data/processed/order5_strategy_registry/candidates/false_high_fin_mod17_accepted_1_2_5_6_7_8_exact_rescore_smoke_accepted_packet_20260526.jsonl
```

Result:

- rows scanned: `6`
- greedy new false vs graph: `2,189,171`
- conflict vs graph true: `0`
- existing remote smoke evidence: accepted packet, `20` accepted representative rows

The fourth row in the old packet is already graph-covered, but the other five
still leave a mainline-sized exact false packet. This is the best revival target
from this pass.

### `non_affine_all4x4` full80

Input:

```text
data/processed/order5_strategy_registry/candidates/false_non_affine_all4x4_remaining_current_batch_selection_full80_20260526.jsonl
```

Result:

- rows scanned: `80`
- positive rows: `78`
- greedy new false vs graph: `795,602`
- conflict vs graph true: `0`
- top single row after current graph: `29,186`

Interpretation: this lane is still sound-looking but no longer clears the
`1,000,000` mainline gate against the graph. Treat it as a tail packet unless
combined with another false lane.

## Recommendation

Immediate revival order:

1. Promote or controller-review the `mod17` accepted packet as the one surviving
   mainline high-ROI false packet from this pass: `2.19M` graph-new, zero conflict,
   accepted smoke evidence already present.
2. Mark the checked true pair-cache high-ROI rows as stale/subsumed from the graph
   perspective; they are not current-new.
3. Move `non_affine_all4x4 full80` from mainline to tail or combine it with another
   compatible false packet, because graph-new coverage is now `795,602`.

## Follow-up: `mod17` packet revived

Implemented the recommendation by registering the five still-new rows from the
accepted `mod17` packet into the discovered setcheck bank:

- `false.finmodel.setcheck.affine_mod_probe.mod17.a7.b11.c0.all_equations.v1`
- `false.finmodel.setcheck.affine_mod_probe.mod17.a11.b7.c0.all_equations.v1`
- `false.finmodel.setcheck.affine_mod_probe.mod17.a9.b2.c0.all_equations.v1`
- `false.finmodel.setcheck.affine_mod_probe.mod17.a8.b7.c0.all_equations.v1`
- `false.finmodel.setcheck.affine_mod_probe.mod17.a7.b8.c0.all_equations.v1`

The old `(a,b,c)=(2,9,0)` row was not duplicated because it is already active as
`false.finmodel.setcheck.affine_mod17_candidate6_sourcefirst_addon_20260526.v1`.

Registry output after recomputing false coverage with current true output reused:

- raw false union: `2,387,093,988`
- false union increase: `2,189,171`
- raw true union reused from output: `1,394,597,946`
- unresolved estimate: `134,001,266`
- conflict count: `0`

Columnar graph store import results matched the revival preview:

| strategy | graph newly set | conflict |
| --- | ---: | ---: |
| `mod17.a7.b11.c0` | `499,156` | `0` |
| `mod17.a11.b7.c0` | `498,349` | `0` |
| `mod17.a9.b2.c0` | `438,605` | `0` |
| `mod17.a8.b7.c0` | `376,527` | `0` |
| `mod17.a7.b8.c0` | `376,534` | `0` |

After rebuilding conflicts, graph bit counts are:

- false: `2,387,093,988`
- true: `1,394,641,181`
- conflict: `0`
- exact unknown by graph count: `133,958,031`

Concrete graph status check after import:

```bash
./.venv/bin/python scripts/data/build_order5_columnar_graph_store.py status --eq-pair 4795 3079
```

Result: pair index `299,987,628` is `false`, with `false=true`,
`true=false`, and `conflict=false`.

Queue refresh after the revival:

- `certificate_blocked_high_roi`: `16`
- `needs_rescore_or_smoke_main`: `19`
- `postedge7_controller_review`: `2`
- `tail_candidates`: `355`
- `register_ready_main`: `0`
- `stale_or_subsumed`: `407`
- unresolved estimate: `134,001,266`

## Follow-up: `postedge7` controller review closed

Reviewed the two remaining `postedge7_controller_review` entries against the
current columnar graph. Both were stale from the current graph point of view:

- `current_residual_postedge7_key_collision_audit` was a route-audit artifact;
  its own summary says all >=100k false-like rows are already routed.
- `false.finmodel.setcheck.non_affine_all4x4_remaining_current_20260525.etp_refutation659`
  was the head of the old `non_affine_all4x4` full80 packet, but current graph
  novelty dropped below the mainline gate.

Current graph preview/rescore evidence:

- single `etp_refutation659`: `24,563` new false, `0` conflict
- full80 greedy union: `795,268` new false, `0` conflict
- rows scanned: `80`
- positive greedy rows: `78`
- independent new sum, not union-deduped: `1,383,316`

Recorded the current-graph tail route in:

```text
members/wubing/data/processed/order5_strategy_registry/candidates/controller_false_non_affine_all4x4_full80_current_graph_tail_rescore_20260529_summary.json
```

That summary explicitly absorbs four superseded high-score artifacts:

- `false_candidate_index_ge100k_false_like_consolidated_route_audit_20260528_summary.json`
- `false_candidate_index_high_priority_status_residual_crosswalk_20260528_summary.json`
- `false_high_increment_nonmerged_candidate_index_table_substrate_scan_20260527_summary.json`
- `false_non_affine_all4x4_remaining_current_batch_selection_full80_20260526_summary.json`

Queue refresh after the controller review:

- `postedge7_controller_review`: `0`
- `register_ready_main`: `0`
- `needs_rescore_or_smoke_main`: `17`
- `certificate_blocked_high_roi`: `14`
- `tail_candidates`: `356`
- `stale_or_subsumed`: `411`
- unresolved estimate: `134,001,266`

The `non_affine_all4x4` full80 packet remains useful only as a tail candidate
at `795,268`; do not register or smoke it as a mainline packet.

## Follow-up: `needs_rescore_or_smoke_main` closed

Reviewed all `17` remaining `needs_rescore_or_smoke_main` rows against the
current columnar graph.

Current graph findings:

- `13` previewable true rows had `newly_set_count = 0` and `conflict_count = 0`
  over `84,116,532` not-union-deduped inspected pair reads.
- The three false accepted/rescore audit rows were not standalone packets; their
  own closure artifacts route them to current family closures or require fresh
  current-residual evidence before reopening.
- The projected hconst+ready-tail union dropped from `1,454,802` to a tail-only
  remnant: hconst+hstp was fully graph-covered, and ready-tail varroot+hconst
  left `125,201` new true pairs with `0` conflict.

Recorded the closeout in:

```text
members/wubing/data/processed/order5_strategy_registry/candidates/controller_needs_rescore_smoke_main_current_graph_closeout_20260529_summary.json
members/wubing/data/processed/order5_strategy_registry/candidates/controller_ready_tail_varroot_hconst87_143_current_graph_tail_20260529_summary.json
```

Queue refresh after this closeout:

- `postedge7_controller_review`: `0`
- `register_ready_main`: `0`
- `needs_rescore_or_smoke_main`: `0`
- `certificate_blocked_high_roi`: `14`
- `tail_candidates`: `357`
- `stale_or_subsumed`: `429`
- unresolved estimate: `134,001,266`

Interpretation: the revive/review pass has cleared the main merge queue. The
next work should be either certificate-blocked debugging or deliberate tail-batch
packing, not direct registry merge from old high-score summaries.

## Follow-up: `certificate_blocked_high_roi` closed

Reviewed the `14` remaining certificate-blocked high-ROI rows. None should stay
as an actionable high-ROI queue item:

- `recursive_anchor.binary_grind_seedpool` is not mergeable: its soundness gate
  had `0/44` accepted remote smoke, and the later proofbank top100 audit found
  accepted-source coverage had `0` current delta and `0` conflict.
- The old affine `mod17` certificate-blocked artifacts are superseded by the
  canonical `mod17` revival and graph import from this session.
- The accepted false handoff / false-only rescore rows are closure artifacts, not
  standalone packets; they require fresh current-residual evidence before reopen.
- The predicate/postedge2 and old mod17 gate audits are closed by a registered
  accepted package, below-gate rechecks, or incomplete/rejected smoke.
- The old high-fin `fin13_25_43` partial-smoke summary is replaced by its
  excluding-slow45 accepted tail packet; keep that work in tail, not
  certificate-blocked high ROI.

Recorded the closeout in:

```text
members/wubing/data/processed/order5_strategy_registry/candidates/controller_certificate_blocked_high_roi_current_closeout_20260529_summary.json
```

Queue refresh after this closeout:

- `postedge7_controller_review`: `0`
- `register_ready_main`: `0`
- `needs_rescore_or_smoke_main`: `0`
- `certificate_blocked_high_roi`: `0`
- `tail_candidates`: `357`
- `stale_or_subsumed`: `444`
- unresolved estimate: `134,001,266`

Interpretation: the high-ROI revival/review queue is now exhausted. Remaining
work should be planned as metadata triage or explicit tail-batch packing.

Verification:

```bash
./.venv/bin/pytest tests/order5_strategy_registry/test_structured_setcheck_strategy.py -q
```

Result: `6 passed in 128.08s`.

```bash
./.venv/bin/pytest tests/data/test_order5_strategy_mining_state.py -q
```

Result: `20 passed in 0.07s`.

## Follow-up: tail-pack preview after high-ROI closeout

The main high-ROI queues are empty, so I started packing the largest tail
candidates against the current columnar graph.

Current tail preview results:

- Top old true hconst tails are stale: sampled `~0.6M` to `0.9M` old-score
  pair-index files now preview at `0` current-new pairs and `0` conflicts.
- The ready-tail varroot+hconst rollup remains a true tail only:
  `125,201` current-new pairs, `0` conflicts.
- Old structured affine false candidates at the top of the tail queue also
  preview as graph-covered; e.g. the old `affine_mod7_a2_b5_c6` and
  `affine_mod11_a7_b9_c9` reranks now have `0` current-new pairs.
- The best live false pack is the accepted non-mod17 true-clean worklist:
  `91` rows, `891,916` current-new false pairs, `0` conflicts.
- The oldhigh `mod17/nonmod17 top5` packet is fully graph-covered now:
  `5` rows, `0` current-new false pairs, `0` conflicts.

Gap check:

- Main gate: `1,000,000`
- Best accepted false tail pack: `891,916`
- Remaining gap: `108,084`

I also tested likely filler packets after the accepted worklist:

- `round2_fresh_top100_needs_smoke`: `0` additional current-new pairs.
- `round46_old_smoked_packet`: `0` additional current-new pairs.
- `predicate_top80_mutated_sample180_needs_smoke`: only `18,400` additional
  current-new pairs.

Interpretation: the old high-score tail artifacts are mostly graph-covered or
covered by the accepted worklist. The next real move is fresh false residual
mining for a clean `108k+` filler outside the non-mod17 worklist rectangles, not
remote-smoking old parking packets.

Recorded the tail-pack rescore in:

```text
members/wubing/data/processed/order5_strategy_registry/candidates/controller_false_nonmod17_tail_worklist_current_graph_pack_20260529_summary.json
```

I also recorded a stale closeout for the top old-score tail shells that now
preview at `0` current-new pairs:

```text
members/wubing/data/processed/order5_strategy_registry/candidates/controller_tail_top_old_score_current_graph_stale_closeout_20260529_summary.json
```

Queue refresh after this tail-pack closeout:

- `postedge7_controller_review`: `0`
- `register_ready_main`: `0`
- `needs_rescore_or_smoke_main`: `0`
- `certificate_blocked_high_roi`: `0`
- `tail_candidates`: `317`
- `stale_or_subsumed`: `486`

Verification:

```bash
./.venv/bin/pytest tests/data/test_order5_strategy_mining_state.py -q
```

Result: `20 passed in 0.09s`.

## Fresh false filler probe for the 108k gap

I sampled the current exact-unknown graph residual after the accepted non-mod17
tail pack left a `108,084` gap to the `1,000,000` main gate.

Residual sample:

- `5,000` exact-unknown directed pairs from the current true/false graph.
- Strata: `24` o4->o4, `228` o4->o5, `372` o5->o4, `4,376` o5->o5.

The old affine `mod17` top shell was the only thing that still looked big
enough on current graph preview, but it does not give a usable filler:

- `a4,b14,c0` and `a14,b4,c0` each preview at `373,254` current-new pairs,
  `0` conflicts, but both are remote rejected. A fresh affine-formula smoke on
  2026-05-29 returned `0/6` accepted with `REMOTE_SIMPLE_API_REJECTED`.
- `a6,b12,c0` and `a12,b6,c0` each preview at `73,092` current-new pairs,
  `0` conflicts. Their table smoke returned `4/8` accepted: order4-source and
  overlap rows pass, while both order5-source tiers are rejected. The order4
  source slice has `0` current-new pairs, so the accepted part is already
  graph-covered.
- The top20 current graph recheck of
  `false_affine_structured_top200_after_mod11_top2_current_rerank_20260519`
  found no usable main filler: live mass is either already covered, below the
  gap, or rejected by smoke.

Other filler lanes were also too small:

- Low-order model pool: `282` models checked against the 5k residual sample;
  only `16` hit at all, and the best model hit `4/5000`.
- Latest order6/PySAT virtual lane through `v205`: `60` accepted packet rows,
  `82,872` row-sum virtual pairs, only `14,055` unique virtual pairs, and only
  `+14` unique pairs over the previous combined virtual summary.

Recorded this closeout in:

```text
members/wubing/data/processed/order5_strategy_registry/candidates/controller_false_current_graph_gap108k_filler_probe_20260529_summary.json
```

Interpretation: no accepted false filler currently closes the `108,084` gap.
The next useful move is not to re-smoke the old affine tail shell; it should
either switch to a new high-order certificate-aware false search, or promote a
separate true tail lane.

## Top true tail current-graph stale check

After the false filler closeout, the next largest visible queue entries were
old true tails. I previewed their pair-index caches directly against the current
columnar graph true layer:

- `d14vc3 -> d23vc4`: `428,720` read, `0` current-new, `0` conflicts.
- `d14vc3 -> d14vc4`: `428,720` read, `0` current-new, `0` conflicts.
- `d13vc4 -> d23vc3` extension: `716,044` read, `0` current-new, `0`
  conflicts.
- hinst mulroot d13 component: `450,704` read, `0` current-new, `0` conflicts.
- hinst mulroot d14 component: `277,678` read, `0` current-new, `0` conflicts.
- v18 top28 d13vc4->d23vc5: `617,065` read, `0` current-new, `0` conflicts.

Recorded the stale closeout in:

```text
members/wubing/data/processed/order5_strategy_registry/candidates/controller_true_tail_top_current_graph_stale_closeout_20260529_summary.json
```

Interpretation: the apparent true tail queue head is also old-score residue
that is already present in the current graph.
