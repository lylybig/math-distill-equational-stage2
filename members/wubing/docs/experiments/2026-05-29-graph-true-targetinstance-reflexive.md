# 2026-05-29 Graph True Mining: Target-Instance O4O4 + Reflexive Target

## Summary

Graph-assisted true mining found a clean deterministic packet made from two simple proof-template slices:

- `true.proof.templatecheck.law_instance.target_instance_of_source.order4_to_order4_excluded.v1`
- `true.proof.templatecheck.reflexive_target.xeqx.all_sources.v1`

Both were audited against a rebuilt current active-registry coverage profile:

- profile: `data/processed/order5_strategy_registry/candidates/current_coverage_profile_active_registry_20260529.json`
- target-instance O4O4 raw pairs: `93,871`
- target-instance O4O4 current increment: `17,202`
- reflexive target raw pairs: `62,575`
- reflexive target current increment: `21,623`
- joint raw pairs: `156,445`
- joint current increment: `38,825`
- joint conflict increment: `0`

The old hinst/varroot post-joint residual cache had `648` current-new pairs; all `648` are explained by the joint target-instance/reflexive packet, leaving `0` remaining.

## Follow-Up: Congr Context Source Instance

The post-joint tiny-frontier scan found another exact true template:

- strategy id: `true.proof.templatecheck.congr_context.source_instance.nontrivial_context.all_order5.v1`
- rule: target has form `C[Lσ] = C[Rσ]` or the reversed subequation inside the same non-hole one-hole context `C`, where source is `L = R`
- proof surface: `congrArg (fun hole => C[hole]) (h σ)`, with `.symm` for reversed subequation orientation

Counts against the rebuilt current active-registry profile:

- raw pairs: `32,376`
- current increment: `4,355`
- marginal after the target-instance/reflexive joint packet: `4,341`
- conflict increment: `0`

Graph preview:

- `data/processed/order5_strategy_registry/candidates/true_template_congr_context_source_instance_all_order5_graph_preview_current_store_20260529.json`
  - read: `32,376`
  - newly set: `4,355`
  - conflict: `0`

Remote smoke:

- input: `data/processed/order5_strategy_registry/candidates/true_template_congr_context_source_instance_smoke_input_20260529.jsonl`
- results: `data/processed/order5_strategy_registry/candidates/true_template_congr_context_source_instance_smoke_results_20260529.jsonl`
- summary: `data/processed/order5_strategy_registry/candidates/true_template_congr_context_source_instance_smoke_results_20260529_summary.json`
- accepted: `16/16`

Combined rollup:

- pair cache: `data/processed/order5_strategy_registry/candidates/true_template_joint_targetinst_reflexive_plus_congr_context_pair_indexes_20260529.txt`
- current profile audit: `data/processed/order5_strategy_registry/candidates/true_template_joint_targetinst_reflexive_plus_congr_context_current_profile_audit_20260529.json`
- graph preview: `data/processed/order5_strategy_registry/candidates/true_template_joint_targetinst_reflexive_plus_congr_context_graph_preview_current_store_20260529.json`
- raw pairs: `188,019`
- current increment: `43,166`
- conflict increment: `0`

## Follow-Up: Recursive Congruence Closure

A broader compiler-style template nearly subsumes the smaller packets:

- strategy id: `true.proof.templatecheck.recursive_congruence.symmetric_source_instance.all_order5.v1`
- rule: recursively relate target terms using syntactic equality, a source instance, a reversed source instance, or binary congruence over both children
- proof surface: recursively combine `rfl`, `h σ`, `(h σ).symm`, and `congrArg`/`.trans` over multiplication contexts

Counts against the rebuilt current active-registry profile:

- raw pairs: `2,505,434`
- current increment: `43,169`
- conflict increment: `0`
- current-new explained by the previous `targetinst/reflexive + congr-context` combined packet: `43,166`
- marginal after that combined packet: `3`

Graph preview:

- `data/processed/order5_strategy_registry/candidates/true_template_recursive_congruence_symmetric_source_instance_all_order5_graph_preview_current_store_20260529.json`
  - read: `2,505,434`
  - newly set: `43,169`
  - conflict: `0`

Remote smoke:

- input: `data/processed/order5_strategy_registry/candidates/true_template_recursive_congruence_symmetric_source_instance_smoke_input_20260529.jsonl`
- results: `data/processed/order5_strategy_registry/candidates/true_template_recursive_congruence_symmetric_source_instance_smoke_results_20260529.jsonl`
- summary: `data/processed/order5_strategy_registry/candidates/true_template_recursive_congruence_symmetric_source_instance_smoke_results_20260529_summary.json`
- accepted: `3/3`

The three marginal pairs after the previous combined packet are:

- `3 -> 3715`: `x = x * x` proves `x * y = (x * x) * (y * y)`
- `3 -> 4380`: `x = x * x` proves `x * (x * x) = (x * x) * x`
- `3 -> 4470`: `x = x * x` proves `x * (y * y) = (x * x) * y`

## Follow-Up: Tiny-Frontier Egraph + Hinst Grind

After importing recursive congruence into the graph true layer, the exact graph frontier had:

- zero-unknown source rows: `24,122`
- tiny-frontier source rows: `3,289`
- tiny-frontier unknown pairs: `14,860`

A bounded egraph rewrite compiler found the six remaining pairs in source rows `8` and `23`. The first remote run exposed a Lean renderer bug: context lambdas like `fun t => (t ◇ x ◇ x)` lost nested non-hole parentheses. The fix is in `src/math_distill_stage2/order5_egraph_proof_search.py`, covered by `tests/order5_strategy_registry/test_order5_egraph_proof_search.py`.

Egraph rewrite evidence:

- pair cache: `data/processed/order5_strategy_registry/candidates/true_template_egraph_rewrite_search_after_recursive_tiny_frontier_pair_indexes_20260529.txt`
- remote smoke v2: `data/processed/order5_strategy_registry/candidates/true_template_egraph_rewrite_search_after_recursive_tiny_frontier_v2_smoke_results_20260529_summary.json`
- accepted: `6/6`
- graph import: read `6`, newly set `6`, conflict `0`
- closed source rows: `8`, `23`

Using the proofbench h-instantiation/grind pattern against high-frequency graph targets then found a small exact accepted packet:

- high-frequency probe: `11/24` accepted
- accepted-source frontier expansion: `23/35` accepted
- wide repair of previous rejects: `0/25` accepted, so the rejected side is a real boundary for the simple bounded hinst surface
- imported accepted hinst pairs: `34`
- graph import conflicts: `0`
- additionally closed source rows: `152`, `166`

Packet summary:

- `data/processed/order5_strategy_registry/candidates/true_template_graph_tiny_frontier_egraph_hinst_packet_20260529_summary.json`

Graph frontier after the egraph+hinst packet:

- zero-unknown source rows: `24,127`
- tiny-frontier source rows: `3,284`
- tiny-frontier unknown pairs: `14,820`

## Later Graph-Guided H-Instantiation

Wave2 high-frequency tiny-frontier probing used the same explicit
`have h_i := h ...; grind` proof surface, but selected from the latest graph
frontier and excluded previously smoked hinst pairs.

Remote results:

- `true_template_hinst_grind_highfreq_tiny_frontier_wave2_probe_20260529.jsonl`
  - accepted: `6/40`
  - graph import: read `6`, newly set `6`, conflict `0`
- `true_template_hinst_grind_wave2_accepted_sources_frontier_expansion_20260529.jsonl`
  - accepted: `15/21`
  - graph import: read `15`, newly set `15`, conflict `0`
- `true_template_hinst_grind_rejected_wide_repair_probe_20260529.jsonl`
  - accepted: `0/25`
  - interpretation: adding more broad h-instantiations did not repair rejected
    neighbors.

After wave2, one-unknown graph rows became a useful queue:

- `true_template_hinst_grind_one_unknown_frontier_probe_20260529.jsonl`
  - accepted: `5/60`
  - graph import: read `5`, newly set `5`, conflict `0`
  - effect: closed `5` source rows.
- `true_template_hinst_grind_one_unknown_target3659_probe_20260529.jsonl`
  - accepted: `7/31`
  - graph import: read `7`, newly set `7`, conflict `0`
  - useful target family: `3659`, equation `x * x = (x * x) * (x * x)`.
- `true_template_hinst_grind_one_unknown_targets3253_4065_probe_20260529.jsonl`
  - accepted: `0/8`
- `true_template_hinst_grind_one_unknown_target51176_probe_20260529.jsonl`
  - accepted: `0/10`, with `1` timeout.

Latest frontier after target `3659` imports and proofbench evidence import:

- zero-unknown source rows: `24,152`
- tiny-frontier source rows: `3,296`
- tiny-frontier unknown pairs: `14,913`
- one-unknown source rows: `559`

The target `3659` family is the strongest graph-assisted hinst signal so far.
Nearby accepted-target families `3253`, `4065`, and `51176` did not generalize
under the same proof surface.

## ProofBench Residual1000 Accepted Evidence

The sibling proofbench run snapshot
`artifacts/proofbench_runs/20260529-residual1000-accepted/accepted.jsonl`
was read while it was still growing. The latest local snapshot copied into this
repo had `729`
accepted rows:

- true: `662`
- false: `67`

Exact pair-index caches extracted into this repo:

- `data/processed/order5_strategy_registry/candidates/proofbench_residual1000_accepted_snapshot_20260529.jsonl`
- `data/processed/order5_strategy_registry/candidates/proofbench_residual1000_accepted_true_pair_indexes_20260529.txt`
- `data/processed/order5_strategy_registry/candidates/proofbench_residual1000_accepted_false_pair_indexes_20260529.txt`
- summary:
  `data/processed/order5_strategy_registry/candidates/proofbench_residual1000_accepted_strategy_mining_summary_20260529.json`

Graph refresh previews were clean:

- true cache: read `662`, newly set `17`, conflict `0`
- false cache: read `67`, newly set `0`, conflict `0`

The new true rows were imported as exact graph evidence:

- true refresh import sha256:
  `573878db3c947bda0b317b98da198ee9a2ce45af88df404b6b23a1e5be7321a8`

Graph layer counts after the proofbench refresh and Z3-guided frontier imports:

- true: `1,394,641,881`
- false: `2,387,094,055`
- conflict: `0`

The June 1 proofbench true refresh did not change the tiny-frontier histogram,
so its immediate value is mostly global exact-evidence coverage and wider-row
unknown shrinkage rather than row-closing.

Frontier after refresh:

- zero-unknown source rows: `24,161`
- tiny-frontier source rows: `3,287`
- tiny-frontier unknown pairs: `14,904`
- one-unknown source rows: `550`

Accepted true proof-surface families in the latest snapshot:

- `z3_proof_guided_letshared_grind`: `363`
- `hinst_var_anchor_grind`: `204`
- `hinst_subterm_anchor_grind`: `86`
- `hinst_paircube_grind`: `7`
- `rewrite_chain_calc`: `1`
- `unknown`: `1`

False accepted certificates:

- `finite_countermodel_false`: `67`

Lean surface counts:

- `have ...; grind`: `644`
- local `let` sharing: `350`
- finite certificate surface: `67`
- explicit `calc`: `1`

Strategy implications:

- Continue using graph frontiers to choose small hinst batches, but prioritize
  families with evidence. The proofbench sample says anchor hinst and subterm
  hinst are robust surfaces, while blind widening can be slow or rejected.
- Port or adapt the proofbench `z3_proof_guided_letshared.py` extractor for
  order5 graph frontier rows. This is the strongest true signal in the 1000
  sample: it contributes `363/662` accepted true certificates and still emits
  judge-compatible `have` plus `grind` code.
- Keep finite-model false evidence in the exact false graph layer when remotely
  accepted; it improves future true mining by shrinking unknown frontiers.

Immediate migration trial:

- input problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_trial_one_unknown20_problems_20260529.jsonl`
- generator:
  proofbench `.codex/skills/stage2-proofbench-solver/scripts/z3_proof_guided_letshared.py`
- local candidates:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_trial_one_unknown20_candidates_20260529.jsonl`
- result: `2` candidates from `20` one-unknown graph rows.
- remote smoke:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_trial_one_unknown20_smoke_results_20260529.jsonl`
  - accepted: `2/2`
- graph import:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_trial_one_unknown20_accepted_pair_indexes_20260529.txt`
  - read: `2`
  - newly set: `2`
  - conflict: `0`
  - sha256:
    `f6c568a07d7f94590ca3e94af8174f13d4f6048e2c6d95573990bdb634057c10`

Frontier after the Z3-guided import:

- zero-unknown source rows: `24,154`
- tiny-frontier source rows: `3,294`
- tiny-frontier unknown pairs: `14,911`
- one-unknown source rows: `557`

This validates the migration path: proofbench's Z3-guided instance extractor can
produce small order5 graph-frontier true certificates, and remotely accepted
pairs immediately close one-unknown rows.

Second Z3-guided frontier batch:

- input problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_one_unknown_next80_problems_20260529.jsonl`
- local candidates: `7/80`
- remote smoke accepted: `7/7`
- graph import: read `7`, newly set `7`, conflict `0`
- accepted pairs:
  `(3331,3534)`, `(4200,3997)`, `(4204,56433)`, `(4456,61671)`,
  `(4490,61671)`, `(13471,614)`, `(13857,614)`

Frontier after this import:

- zero-unknown source rows: `24,161`
- tiny-frontier source rows: `3,287`
- tiny-frontier unknown pairs: `14,904`
- one-unknown source rows: `550`

Third Z3-guided frontier batch:

- input problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_one_unknown_next80b_problems_20260529.jsonl`
- local candidates: `0/80`
- status rows: `80/80` candidate false

Proofbench-shape ranked Z3-guided frontier batch:

- ranking artifacts:
  `data/processed/order5_strategy_registry/candidates/proofbench_guided_one_unknown_frontier_ranked_candidates_20260529.jsonl`
  and
  `data/processed/order5_strategy_registry/candidates/proofbench_guided_one_unknown_frontier_ranked_summary_20260529.json`
- queue: `379` one-unknown rows after excluding the first `180` Z3 attempts
- ranking signal: proofbench accepted source/target/pair shape counts, weighted
  toward `z3_proof_guided` successes
- input problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_one_unknown_shape_ranked40_problems_20260529.jsonl`
- local candidates: `4/40`
- remote smoke accepted: `4/4`
- graph import: read `4`, newly set `4`, conflict `0`
- accepted pairs:
  `(46029,46037)`, `(46897,46911)`, `(60859,60871)`, `(56922,56937)`

Frontier after this import:

- zero-unknown source rows: `24,165`
- tiny-frontier source rows: `3,283`
- tiny-frontier unknown pairs: `14,900`
- one-unknown source rows: `546`

Low-score proofbench-shape ranked Z3-guided frontier batch:

- ranking artifacts:
  `data/processed/order5_strategy_registry/candidates/proofbench_guided_one_unknown_frontier_ranked_after_false_refresh_candidates_20260529.jsonl`
  and
  `data/processed/order5_strategy_registry/candidates/proofbench_guided_one_unknown_frontier_ranked_after_false_refresh_summary_20260529.json`
- queue: `339` one-unknown rows after excluding the first `220` Z3 attempts
- input problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_one_unknown_shape_ranked80_low_score_problems_20260529.jsonl`
- local candidates: `4/80`
- remote smoke accepted: `4/4`
- graph import: read `4`, newly set `4`, conflict `0`
- accepted pairs:
  `(51271,51194)`, `(60236,60299)`, `(51285,51238)`, `(57851,55220)`

Frontier after this import:

- zero-unknown source rows: `24,169`
- tiny-frontier source rows: `3,279`
- tiny-frontier unknown pairs: `14,896`
- one-unknown source rows: `542`

Very-low-score threshold probe:

- ranking artifacts:
  `data/processed/order5_strategy_registry/candidates/proofbench_guided_one_unknown_frontier_ranked_after_ranked80_low_score_import_candidates_20260529.jsonl`
  and
  `data/processed/order5_strategy_registry/candidates/proofbench_guided_one_unknown_frontier_ranked_after_ranked80_low_score_import_summary_20260529.json`
- remaining ranked one-unknown rows: `259`
- top score after prior imports: `58`
- input problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_one_unknown_shape_ranked20_very_low_score_problems_20260529.jsonl`
- local candidates: `1/20`
- remote smoke accepted: `1/1`
- graph import: read `1`, newly set `1`, conflict `0`
- accepted pair: `(33641,2644)`

Frontier after this import:

- zero-unknown source rows: `24,170`
- tiny-frontier source rows: `3,278`
- tiny-frontier unknown pairs: `14,895`
- one-unknown source rows: `541`

Cluster-guided frontier batch:

- ranking artifacts:
  `data/processed/order5_strategy_registry/candidates/proofbench_cluster_guided_one_unknown_frontier_ranked_candidates_20260529.jsonl`
  and
  `data/processed/order5_strategy_registry/candidates/proofbench_cluster_guided_one_unknown_frontier_ranked_summary_20260529.json`
- training set: `18` remote-accepted Z3 frontier pairs
- ranking signal: accepted pair/source/target shapes plus source/target id
  neighborhoods and reciprocal checks
- input problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_one_unknown_cluster_ranked60_problems_20260529.jsonl`
- local candidates: `3/60`
- remote smoke accepted: `3/3`
- graph import: read `3`, newly set `3`, conflict `0`
- accepted pairs:
  `(32099,2847)`, `(44165,3456)`, `(45977,48545)`
- tag diagnostics:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_one_unknown_cluster_ranked60_tag_diagnostics_20260529.json`
  showed `accepted_pair_shape` as the strongest small-sample signal, while
  `target_block`, `source_block`, `target_near25`, and `source_near25` produced
  no local candidates in this batch.

Frontier after this import:

- zero-unknown source rows: `24,173`
- tiny-frontier source rows: `3,275`
- tiny-frontier unknown pairs: `14,892`
- one-unknown source rows: `538`

Feedback-ranked frontier batch:

- ranking artifacts:
  `data/processed/order5_strategy_registry/candidates/proofbench_feedback_guided_one_unknown_frontier_ranked_candidates_20260529.jsonl`
  and
  `data/processed/order5_strategy_registry/candidates/proofbench_feedback_guided_one_unknown_frontier_ranked_summary_20260529.json`
- training set: `21` remote-accepted Z3 frontier pairs
- ranking signal: reward accepted pair/source/target shape intersections and
  weak `near100`; penalize source/target ids that appeared repeatedly in the
  cluster batch with candidate false
- input problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_one_unknown_feedback_ranked40_problems_20260529.jsonl`
- local candidates: `3/40`
- remote smoke accepted: `3/3`
- graph import: read `3`, newly set `3`, conflict `0`
- accepted pairs:
  `(50304,3862)`, `(48608,45914)`, `(32122,2847)`

Frontier after this import:

- zero-unknown source rows: `24,176`
- tiny-frontier source rows: `3,272`
- tiny-frontier unknown pairs: `14,889`
- one-unknown source rows: `535`

June 1 proofbench true refresh:

- latest snapshot: `729` accepted rows, with `662` true and `67` false
- true refresh import: read `662`, newly set `17`, conflict `0`
- false refresh preview: read `67`, newly set `0`, conflict `0`
- import sha256:
  `573878db3c947bda0b317b98da198ee9a2ce45af88df404b6b23a1e5be7321a8`
- frontier after refresh:
  - zero-unknown source rows: `24,176`
  - tiny-frontier source rows: `3,272`
  - tiny-frontier unknown pairs: `14,889`
  - one-unknown source rows: `535`

Tiny-frontier strong-shape ranked batch:

- ranking artifacts:
  `data/processed/order5_strategy_registry/candidates/proofbench_strong_shape_intersection_tiny_frontier_ranked_candidates_20260601.jsonl`
  and
  `data/processed/order5_strategy_registry/candidates/proofbench_strong_shape_intersection_tiny_frontier_ranked_summary_20260601.json`
- queue: `3,433` ranked tiny-frontier pairs after excluding prior Z3 attempts
- ranking signal: strong pair/source/target shape intersections from
  proofbench and remote-accepted frontier positives; weak neighborhood bonuses
  only after positive shape support
- input problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_tiny_frontier_strong_shape_ranked60_problems_20260601.jsonl`
- local candidates: `7/60`
- remote smoke accepted: `7/7`
- graph import: read `7`, newly set `7`, conflict `0`
- accepted pairs:
  `(46906,46911)`, `(46906,46914)`, `(46032,46034)`,
  `(8595,411)`, `(37361,3050)`, `(16454,614)`, `(29609,2847)`

Frontier after this import:

- zero-unknown source rows: `24,177`
- tiny-frontier source rows: `3,271`
- tiny-frontier unknown pairs: `14,882`
- one-unknown source rows: `535`

Tiny-frontier strong-shape ranked continuation:

- ranked queue after prior strong60 import:
  `data/processed/order5_strategy_registry/candidates/proofbench_strong_shape_intersection_tiny_frontier_ranked_after_strong60_candidates_20260601.jsonl`
  and
  `data/processed/order5_strategy_registry/candidates/proofbench_strong_shape_intersection_tiny_frontier_ranked_after_strong60_summary_20260601.json`
- queue stats: `14,882` tiny-frontier pairs, `480` attempted pairs,
  `31` accepted training pairs, `3,373` ranked pairs
- input problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_tiny_frontier_strong_shape_ranked_next60_problems_20260601.jsonl`
- local candidates: `9/60`
- remote smoke accepted: `9/9`
- graph import: read `9`, newly set `9`, conflict `0`
- import sha256:
  `3759a75ca7dd0d26610050a214a682491f2ba1ab5e3e9c9675a27f017c598619`
- accepted pairs:
  `(16491,17850)`, `(29619,27497)`, `(4348,55442)`,
  `(4348,55468)`, `(4348,55494)`, `(4348,55526)`,
  `(4348,55532)`, `(4348,55538)`, `(4348,55544)`
- top source concentration: source `4348` contributed `7/9` accepted pairs
  with compact `4`-instance, `1`-let certificates

Frontier after this import:

- zero-unknown source rows: `24,177`
- tiny-frontier source rows: `3,271`
- tiny-frontier unknown pairs: `14,873`
- one-unknown source rows: `535`
- graph bit counts: true `1,394,641,890`, false `2,387,094,055`,
  conflict `0`

Source `4348` residual tail closure:

- after the continuation import, source `4348` still had exactly `3` unknown
  targets: `55550`, `55556`, and `56433`
- input problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_source4348_tail3_problems_20260601.jsonl`
- local candidates: `3/3`
- remote smoke accepted: `3/3`
- graph preview: read `3`, newly set `3`, conflict `0`
- graph import: read `3`, newly set `3`, conflict `0`
- import sha256:
  `ea12caddef16e317c12415a622b4b9e7f42f03c687741ed10e613f424ab24e07`
- accepted pairs:
  `(4348,55550)`, `(4348,55556)`, `(4348,56433)`
- representative status query after import:
  `(4348,56433)` has exact verdict `true`

Frontier after source `4348` tail closure:

- source `4348` row summary: true `433`, false `62,142`, conflict `0`,
  unknown `0`
- zero-unknown source rows: `24,178`
- tiny-frontier source rows: `3,270`
- tiny-frontier unknown pairs: `14,870`
- one-unknown source rows: `535`
- graph bit counts: true `1,394,641,893`, false `2,387,094,055`,
  conflict `0`

After-`4348` strong-shape continuation:

- ranking artifacts:
  `data/processed/order5_strategy_registry/candidates/proofbench_strong_shape_intersection_tiny_frontier_ranked_after_source4348_tail3_candidates_20260601.jsonl`
  and
  `data/processed/order5_strategy_registry/candidates/proofbench_strong_shape_intersection_tiny_frontier_ranked_after_source4348_tail3_summary_20260601.json`
- queue stats: `14,870` tiny-frontier pairs, `543` attempted pairs,
  `43` frontier accepted training rows, `661` proofbench accepted true
  shape-usable rows, `1,427` ranked pairs
- input problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_tiny_frontier_strong_shape_ranked_after_source4348_tail3_next60_problems_20260601.jsonl`
- local partial run: `22/60` attempted, `10` candidates
- remote smoke accepted: `10/10`
- graph preview/import: read `10`, newly set `10`, conflict `0`
- import sha256:
  `f5d6e89fe117fa0a1acdbcb805d10e63fc57eeb4181259cbca9db5df9806b011`
- source concentration:
  source `4663` contributed `8/10` accepted pairs with the same compact
  `4`-instance, `1`-let certificate family that closed source `4348`
- accepted pairs:
  `(4663,61581)`, `(4663,61607)`, `(4663,61633)`, `(4663,61665)`,
  `(4663,61671)`, `(4663,61677)`, `(4663,61683)`, `(4663,61689)`,
  `(3617,4226)`, `(56895,56937)`

Tail closure for newly concentrated sources:

- after the partial import, source `4663` had exactly `2` unknown targets and
  source `56895` had exactly `4`; source `3617` had one remaining target but
  produced no Z3-guided candidate in this surface
- input problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_after_source4348_partial22_tail_sources_4663_3617_56895_problems_20260601.jsonl`
- local candidates: `6/7`
- remote smoke accepted: `6/6`
- graph preview/import: read `6`, newly set `6`, conflict `0`
- import sha256:
  `913eb98646f382c69a79afb00ff6dcbc0958c424645632229d735ceba3528c0c`
- accepted pairs:
  `(4663,61695)`, `(4663,62572)`, `(56895,56917)`,
  `(56895,56922)`, `(56895,56927)`, `(56895,56932)`
- representative status query after import:
  `(4663,62572)` has exact verdict `true`

Frontier after `4663`/`56895` tail closure:

- source `4663` row summary: true `433`, false `62,142`, conflict `0`,
  unknown `0`
- source `56895` row summary: true `54`, false `62,521`, conflict `0`,
  unknown `0`
- zero-unknown source rows: `24,180`
- tiny-frontier source rows: `3,268`
- tiny-frontier unknown pairs: `14,854`
- one-unknown source rows: `536`
- graph bit counts: true `1,394,641,909`, false `2,387,094,055`,
  conflict `0`

Interpretation: the migrated proofbench Z3-guided extractor is high-precision
when it emits a certificate (`59/59` remote accepted so far in this
graph-assisted frontier channel). Plain pair-order
scanning hit a timeout-heavy region (`0/80`), but proofbench accepted-shape
ranking immediately recovered `4/40` candidates and all passed the remote
judge. Lower-score ranked batches still produced accepted pairs (`4/80` and
`1/20`), but the candidate rate dropped sharply once only target/source-shape
weak matches remained. Cluster and feedback ranking recovered another `6`
accepted pairs. Expanding the same strong shape-intersection rule from
one-unknown rows to the full tiny frontier recovered `7/60`, then the next
ranked continuation recovered `9/60`. The `4348` concentration shows the
strongest strategic use of the proofbench 1000-sample accepted pool: use
accepted source/target shape intersections to find a same-template multi-target
cluster, then use graph row summaries to finish the row tail instead of broad
search. The after-`4348` continuation repeated the same pattern on source
`4663` and fully closed source `56895`, so this is now a reusable mining loop:
accepted-shape ranking -> compact Z3 certificates -> graph import -> source-tail
closure. The strongest next direction is not broad id-neighborhood expansion;
it is accepted pair/source/target shape intersections with explicit negative
feedback from local candidate-false batches, especially prioritizing small
`source_unknown_count` inside the tiny frontier and stopping partial top-N runs
once they enter timeout-heavy shape families.

Source-cluster continuation after the `4663`/`56895` tail closure:

- cluster-ranking artifacts:
  `data/processed/order5_strategy_registry/candidates/proofbench_strong_shape_intersection_tiny_frontier_ranked_after_tail_sources_20260601.jsonl`
  and
  `data/processed/order5_strategy_registry/candidates/proofbench_strong_shape_intersection_tiny_frontier_source_clusters_after_tail_sources_summary_20260601.json`
- queue stats: `14,854` tiny-frontier pairs, `610` attempted pairs,
  `661` proofbench accepted true shape-usable rows, `1,361` ranked pairs
- input problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_tiny_frontier_source_cluster_after_tail_sources_top48_problems_20260601.jsonl`
- local candidates: `12/48`
- remote smoke accepted: `12/12`
- graph preview/import: read `12`, newly set `12`, conflict `0`
- import sha256:
  `18d6bb573b526c6181e84d907a17bd857fe35d4facc37c553851baec8a10caf5`
- source concentration:
  source `46913` contributed `6/12`, source `46036` contributed `5/12`,
  and source `46863` contributed `1/12`
- accepted pairs:
  `(46913,46889)`, `(46913,46899)`, `(46913,46903)`,
  `(46913,46907)`, `(46913,46911)`, `(46913,46915)`,
  `(46036,46012)`, `(46036,46022)`, `(46036,46026)`,
  `(46036,46030)`, `(46036,46034)`, `(46863,47720)`

Tail closure for sources `46913` and `46036`:

- after the cluster import, each source had exactly `2` unknown targets
- input problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_source_clusters_46913_46036_tail4_problems_20260601.jsonl`
- local candidates: `4/4`
- remote smoke accepted: `4/4`
- graph preview/import: read `4`, newly set `4`, conflict `0`
- import sha256:
  `3577db0d1099c10e124128c40a6edb812c55f37b25cf1cdde4b630197ee14d6d`
- accepted pairs:
  `(46913,46805)`, `(46913,46916)`, `(46036,45928)`,
  `(46036,46039)`
- both source rows closed to zero unknown

The `vc=4`, `lm=0`, `rm=0`, same-shape family extension:

- family bucket:
  `roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0`
- after closing `46913` and `46036`, this family had only `9`
  unattempted tiny-frontier pairs across `6` sources
- input problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_vc4_lm0rm0_same_shape_extension9_problems_20260601.jsonl`
- local candidates: `7/9`
- remote smoke accepted: `7/7`
- graph preview/import: read `7`, newly set `7`, conflict `0`
- import sha256:
  `3bc1adfdaee13168d8191cf182893ef91785b21aea0cc087801b6962b0037405`
- accepted pairs:
  `(46030,46036)`, `(46030,46037)`, `(46907,46913)`,
  `(46907,46914)`, `(46907,46915)`, `(46072,48669)`,
  `(48668,46038)`

Tail closure for sources `46907` and `46030`:

- after the same-shape extension, both sources had exactly `2` unknown targets
- input problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_vc4_lm0rm0_sources_46907_46030_tail4_problems_20260601.jsonl`
- local candidates: `4/4`
- remote smoke accepted: `4/4`
- graph preview/import: read `4`, newly set `4`, conflict `0`
- import sha256:
  `fdf3894a555efaa4106d4440f6012d5b98d06c8e996383b4c5a08d061364f907`
- accepted pairs:
  `(46907,46912)`, `(46907,46916)`, `(46030,46035)`,
  `(46030,46039)`
- representative status queries after import:
  `(46907,46916)` and `(46030,46039)` have exact verdict `true`
- both source rows closed to zero unknown

Higher-budget retry for the two remaining same-shape family points:

- input problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_vc4_lm0rm0_same_shape_remaining2_problems_20260601.jsonl`
- local candidates with `timeout-ms=10000`, `seed-count=24`: `0/2`
- remaining same-shape family frontier:
  `(46911,46914)` and `(47843,47826)`

Frontier after the same-shape extension and tail closure:

- zero-unknown source rows: `24,184`
- tiny-frontier source rows: `3,264`
- tiny-frontier unknown pairs: `14,827`
- one-unknown source rows: `536`
- graph bit counts: true `1,394,641,936`, false `2,387,094,055`,
  conflict `0`

Updated interpretation: the proofbench 1000-sample accepted pool is useful in
two distinct ways. First, accepted source/target shape intersections identify
which tiny-frontier rows deserve Z3-guided proof search. Second, once one
same-shape family is confirmed, the graph frontier can enumerate the full
family tail and turn it into a near-deterministic closure loop. In this round,
the proofbench-guided cluster path added `12 + 4 + 7 + 4 = 27` exact true
edges after the previous `4663`/`56895` closure, closed four more source rows
(`46913`, `46036`, `46907`, `46030`), and kept remote precision at `27/27`
for emitted certificates with zero conflicts. The two remaining same-shape
points give a clear boundary for this template rather than an open broad-search
queue.

## 2026-06-01 Proofbench Current Accepted Refresh

The external residual1000 proofbench run advanced beyond the earlier snapshot:

- accepted snapshot:
  `data/processed/order5_strategy_registry/candidates/proofbench_residual1000_accepted_snapshot_current_20260601.jsonl`
- accepted rows: `734/1000`
- accepted true pair-index rows: `667`
- accepted false pair-index rows: `67`
- graph preview for true refresh: read `667`, already set `662`,
  newly set `5`, conflict `0`
- graph import for true refresh:
  source id `proofbench_residual1000_accepted_current_true_refresh_20260601`,
  sha256 `602b7205d0a2260a3db55ed29015dd99f4418e1a64a037673064c450567b2186`

The current proofbench accepted pool was then used as shape-feedback over the
graph tiny frontier:

- evidence-only ranking:
  `data/processed/order5_strategy_registry/candidates/proofbench_current_evidence_shape_feedback_tiny_frontier_ranked_20260601.jsonl`
- summary:
  `data/processed/order5_strategy_registry/candidates/proofbench_current_evidence_shape_feedback_tiny_frontier_ranked_summary_20260601.json`
- top30 problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_current_evidence_shape_feedback_top30_problems_20260601.jsonl`
- local Z3-guided candidates: `4/30`
- remote smoke accepted: `4/4`
- graph preview/import: read `4`, newly set `4`, conflict `0`
- import sha256:
  `443205e438c08705d5550af18b993df259e216c10de097eaea7693db90f36b52`
- accepted pairs:
  `(57738,56932)`, `(46849,47720)`, `(47785,46013)`,
  `(47785,46893)`

Source-tail closure from the accepted top30 rows produced additional exact
true edges:

- `47785` tail5 problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_current_feedback_source47785_tail5_problems_20260601.jsonl`
- local candidates: `4/5`
- remote smoke accepted: `4/4`
- graph preview/import: read `4`, newly set `4`, conflict `0`
- import sha256:
  `c32181477f32ca4db65cf49c76336ddb1dc2e1be3e8211e022469441e3391bed`
- accepted pairs:
  `(47785,3659)`, `(47785,3687)`, `(47785,45914)`,
  `(47785,46791)`
- high-budget retry for the remaining `(47785,45922)` with
  `timeout-ms=10000`, `seed-count=24`, `pattern-mode=all`: `0/1`
- `47785` remains exact unknown on `(47785,45922)` only

A second tail pass over sources `46849` and `57738`:

- tail11 problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_current_feedback_sources46849_57738_tail11_problems_20260601.jsonl`
- local candidates: `2/11`
- remote smoke accepted: `2/2`
- graph preview/import: read `2`, newly set `2`, conflict `0`
- import sha256:
  `059775c3a8fff832cc0f4a8bfee168292ec0c73fa07cb9002abfe8c3caa7750d`
- accepted pairs:
  `(46849,3659)`, `(46849,47668)`
- `46849` moved from `5` unknown targets to `3`; `57738` stayed at `6`

Final graph state after this proofbench-current pass:

- new exact true edges this pass: `5 + 4 + 4 + 2 = 15`
- zero-unknown source rows: `24,184`
- tiny-frontier source rows: `3,264`
- tiny-frontier unknown pairs: `14,817`
- one-unknown source rows: `537`
- graph bit counts: true `1,394,641,951`, false `2,387,094,055`,
  conflict `0`

Interpretation: the residual1000 accepted pool is not just a source of direct
already-certified pairs. It is useful as a deterministic ranking signal when
intersected with graph tiny frontiers. The strongest current pattern is:
import newly accepted true pairs, rank unresolved tiny-frontier pairs by
accepted source/target shape evidence, run Z3-guided proof search on a small
frontier batch, then use the graph frontier to perform per-source tail closure.
In this pass, that pipeline had high precision for emitted certificates
(`10/10` remote accepted after the direct refresh) and exposed clear hard
boundaries such as `(47785,45922)`.

## 2026-06-01 Proofbench 735 Refresh And Family Extension

The external residual1000 accepted set advanced again:

- accepted snapshot:
  `data/processed/order5_strategy_registry/candidates/proofbench_residual1000_accepted_snapshot_735_20260601.jsonl`
- accepted rows: `735/1000`
- accepted true pair-index rows: `668`
- accepted false pair-index rows: `67`
- new direct true pair vs the previous snapshot:
  `(20143,22237)` / pair index `1260407885`
- graph preview/import for the 735 true refresh: read `668`, already set
  `667`, newly set `1`, conflict `0`
- import sha256:
  `3ad96668e7f15b13a9da0caccbf3ce99da8e9db53e2b10c7dff9f8d74cd83267`

The new accepted pool and the current graph frontier were reranked after the
tail11 import:

- ranking:
  `data/processed/order5_strategy_registry/candidates/proofbench_735_current_tail11_frontier_ranked_unattempted_20260601.jsonl`
- summary:
  `data/processed/order5_strategy_registry/candidates/proofbench_735_current_tail11_frontier_ranked_unattempted_summary_20260601.json`
- top40 problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_735_current_tail11_frontier_top40_problems_20260601.jsonl`
- local candidates: `4/40`
- remote smoke accepted: `4/4`
- graph preview/import: read `4`, newly set `4`, conflict `0`
- import sha256:
  `566ff51cf3f170936be833200ec93a2d031a4b1d3ed78caef821c5d5c45ef384`
- accepted pairs:
  `(48696,46013)`, `(48696,46893)`, `(48709,46893)`,
  `(46871,47720)`

The accepted top40 rows opened another source-tail pass:

- tail18 problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_735_current_sources48696_48709_46871_tail18_problems_20260601.jsonl`
- local candidates: `7/18`
- remote smoke accepted: `7/7`
- graph preview/import: read `7`, newly set `7`, conflict `0`
- import sha256:
  `cfc45fb2207da704885e0adcbb75bed74cfd9c06cfd01e69c77db527ab133726`
- accepted pairs:
  `(48696,3659)`, `(48696,3687)`, `(48696,45914)`,
  `(48696,46791)`, `(48709,46791)`, `(46871,3659)`,
  `(46871,47668)`
- `48696` moved to a one-unknown row whose only remaining target is `45922`
- high-budget retry for `(48696,45922)` with `timeout-ms=10000`,
  `seed-count=24`, `pattern-mode=all`: `0/1`
- representative status query: `(48696,45922)` remains exact `unknown`

Final graph state after this continuation:

- new exact true edges since the 734 snapshot pass: `1 + 4 + 7 = 12`
- zero-unknown source rows: `24,184`
- tiny-frontier source rows: `3,264`
- tiny-frontier unknown pairs: `14,806`
- one-unknown source rows: `538`
- graph bit counts: true `1,394,641,963`, false `2,387,094,055`,
  conflict `0`

Interpretation update: the family
`roots=mul>mul|d=1>3|vc=3|lm=0|rm=1|vs=0 -> ...` is now a stable
deterministic mining surface. It repeatedly yields short Z3-guided Lean
certificates for targets such as `3659`, `3687`, `45914`, `46791`, `46893`,
`46013`, `47668`, and `47720`, while target `45922` failed high-budget retries
for both `47785` and `48696`. That makes `45922` a concrete boundary for this
proof surface rather than an undifferentiated missing search-budget case.

## 2026-06-01 vc3/rm1 Easy-Target Extension

After the proofbench735 tail18 import, the current graph frontier still had
`167` unattempted pairs in the source family
`roots=mul>mul|d=1>3|vc=3|lm=0|rm=1|vs=0`. Restricting to already-successful
easy targets and excluding the repeated hard target `45922` produced a narrow
extension queue:

- problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_vc3rm1_easy_targets_unattempted32_problems_20260601.jsonl`
- selected pairs: `32`
- local candidates: `11/32`
- remote smoke accepted: `11/11`
- graph preview/import: read `11`, newly set `11`, conflict `0`
- import sha256:
  `b8ce2391b51ea74de1877c0375bae22d9035f17627831417201d8903501011ed`
- accepted pairs:
  `(48654,3659)`, `(47740,3659)`, `(47828,3659)`,
  `(48688,3659)`, `(48705,3659)`, `(47819,3659)`,
  `(47819,45914)`, `(47819,46791)`, `(47798,46791)`,
  `(46863,3659)`, `(46863,47668)`

The accepted rows opened a second small tail queue over newly active sources:

- problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_vc3rm1_new_sources_tail_unattempted_no45922_problems_20260601.jsonl`
- selected pairs: `22`
- local candidates: `4/22`
- remote smoke accepted: `4/4`
- graph preview/import: read `4`, newly set `4`, conflict `0`
- import sha256:
  `cbdd1a7c785452fba420b198d0a45994fd9a332ab995b1add348518666b9d544`
- accepted pairs:
  `(48654,3684)`, `(47828,3684)`, `(48688,3684)`,
  `(48705,3684)`
- source `48654` closed to zero unknown after `(48654,3684)` was imported

Final graph state after this extension:

- new exact true edges this pass: `11 + 4 = 15`
- zero-unknown source rows: `24,185`
- tiny-frontier source rows: `3,263`
- tiny-frontier unknown pairs: `14,791`
- one-unknown source rows: `538`
- graph bit counts: true `1,394,641,978`, false `2,387,094,055`,
  conflict `0`

Interpretation update: within the vc3/rm1 source family, target `3659` is a
high-yield extension target, and target `3684` is now also prover-confirmed
for four newly active sources. The new reliable target set is therefore not
only the earlier `3659/3687/45914/46791/...` pocket; `3684` should be included
in the next deterministic source-tail closure pass. Emitted certificates in
this extension remained remote-precise (`15/15`) with zero graph conflicts.

## 2026-06-01 Proofbench Accepted Pair-Shape Feedback

The proofbench accepted pool was useful as a graph-ranking signal after the
vc3/rm1 extension, but not as an unconditional target template. A strict
follow-up over the four remaining `3684` rows in the vc3/rm1 easy-target set
produced no local certificates:

- problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_vc3rm1_target3684_remaining4_problems_20260601.jsonl`
- local candidates: `0/4`
- interpretation: target `3684` is source-conditional inside this family, not
  a blanket closure target.

Reranking the current graph frontier by pair-shape evidence from the accepted
proofbench pool gave a better next queue:

- ranking:
  `data/processed/order5_strategy_registry/candidates/proofbench735_after_vc3rm1_pairshape_frontier_ranked_20260601.jsonl`
- summary:
  `data/processed/order5_strategy_registry/candidates/proofbench735_after_vc3rm1_pairshape_frontier_ranked_summary_20260601.json`
- proofbench accepted true rows used as evidence: `668`
- frontier accepted-training rows: `98`
- attempted-pair exclusions: `414`
- ranked frontier pairs: `466`
- selected top problems: `40`
- local candidates: `9/40`
- remote smoke accepted: `9/9`
- graph preview/import: read `9`, newly set `9`, conflict `0`
- import sha256:
  `f58770218aeee123fbcd99cbe7171ddec6c61db53a26e625dcef2d7340a241fe`
- accepted pairs:
  `(46072,48654)`, `(48668,46023)`, `(60857,61730)`,
  `(60865,61730)`, `(56912,56857)`, `(56912,56866)`,
  `(56917,56857)`, `(56917,56887)`, `(61750,61730)`

Representative graph status after import:

```bash
./.venv/bin/python scripts/data/build_order5_columnar_graph_store.py status \
  --store-dir data/processed/order5_columnar_graph_store \
  --pair-index 2882941477
```

returned verdict `true` for `(46072,48654)`.

Final graph state after this pair-shape feedback import:

- zero-unknown source rows: `24,185`
- tiny-frontier source rows: `3,263`
- tiny-frontier unknown pairs: `14,782`
- one-unknown source rows: `538`
- graph bit counts: true `1,394,641,987`, false `2,387,094,055`,
  conflict `0`

Interpretation update: the accepted proofbench sample is now acting as a
precision reranker for deterministic true mining. It exposed a second
successful surface involving `d=2>3` / `vc=4` sources into `d=2>3` / `vc=3`
targets, plus second-layer propagation rows such as `(46072,48654)` and
`(48668,46023)`. The right use is therefore to score graph tiny-frontier
pairs by accepted pair-shape evidence, then require local proof generation and
remote Lean acceptance before importing exact true edges.

The nine imported pair-shape rows also opened a compact second-hop tail over
seven sources. Excluding previously attempted proofbench-guided pairs produced
a `45`-problem queue:

- problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_pairshape_new_sources_tail_unattempted45_problems_20260601.jsonl`
- summary:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_pairshape_new_sources_tail_unattempted45_summary_20260601.json`
- selected unattempted pairs: `45`
- local candidates: `36/45`
- remote smoke accepted: `36/36`
- graph preview/import: read `36`, newly set `36`, conflict `0`
- import sha256:
  `3ccc0ae2196e68f3b18cebe5c4f22a7db0957f7ba01f8c7416608e32c54ae375`
- accepted target groups:
  `46072 -> {48545,48548,48550,48554,48558}`,
  `48668 -> {45914,45917,45919,45923,45927}`,
  `60857 -> {61700,61701,61728,61729}`,
  `60865 -> {61700,61701,61728,61729}`,
  `56912 -> {4270,4341,56446,56453,56481,56805,56829,56887}`,
  `56917 -> {4270,4341,56446,56466,56481,56805,56842,56908}`,
  `61750 -> {61701,61728}`

This second-hop import closed four rows completely: `46072`, `48668`, `56912`,
and `56917`. The remaining focused tails are:

- `60857 -> {60831,60839,60867}`
- `60865 -> {60831,60839,60867}`
- `61750 -> {61708,61710,61716,61717,61743,61744,61746}`

Final graph state after the second-hop import:

- zero-unknown source rows: `24,189`
- tiny-frontier source rows: `3,259`
- tiny-frontier unknown pairs: `14,746`
- one-unknown source rows: `538`
- graph bit counts: true `1,394,642,023`, false `2,387,094,055`,
  conflict `0`

Interpretation update: proofbench accepted rows are most valuable when used
iteratively. The first pair-shape pass found new true edges; those edges
identified near-closed source rows; the second-hop pass closed four of those
rows with another `36` remote-accepted certificates and no conflicts. This is
a reproducible deterministic mining loop rather than a one-off certificate
harvest.

The focused second-hop pass left a small boundary tail:

- `60857 -> {60831,60839,60867}`
- `60865 -> {60831,60839,60867}`
- `61750 -> {61708,61710,61716,61717,61743,61744,61746}`

All of these remaining rows had prior minimized auto-pattern Z3 statuses of
`sat` rather than `unknown`, so they are not good immediate targets for the
same `have h_i := h ...; grind` true-proof surface. Treat them as boundary
rows for now, and prefer reranking the broader current frontier with the
accepted shape evidence.

After the tail45 import, the current tiny frontier was reranked again using the
proofbench accepted true rows plus the remote-smoked graph-frontier true rows:

- ranking:
  `data/processed/order5_strategy_registry/candidates/proofbench735_after_pairshape_tail45_frontier_ranked_20260601.jsonl`
- summary:
  `data/processed/order5_strategy_registry/candidates/proofbench735_after_pairshape_tail45_frontier_ranked_summary_20260601.json`
- evidence rows: `749`
- frontier pairs scanned: `14,746`
- attempted-pair exclusions: `911`
- ranked frontier pairs: `1,296`
- selected top problems: `40`
- local candidates: `9/40`
- remote smoke accepted: `9/9`
- graph preview/import: read `9`, newly set `9`, conflict `0`
- import sha256:
  `0ab2e47634de2a937c26ab7b21269ef9bf8d5d043346b29dce9456926bf1a51a`
- accepted pairs:
  `(53841,53852)`, `(53841,53822)`, `(56932,4341)`,
  `(17080,29369)`, `(17965,30280)`, `(17968,30293)`,
  `(33755,37313)`, `(8900,12130)`, `(15839,28121)`

Graph state after this broader rerank import:

- zero-unknown source rows: `24,189`
- tiny-frontier source rows: `3,259`
- tiny-frontier unknown pairs: `14,737`
- one-unknown source rows: `538`
- graph bit counts: true `1,394,642,032`, false `2,387,094,055`,
  conflict `0`

Interpretation update: once a local tail starts producing `sat` statuses, the
better true-mining move is to widen back out through graph-assisted
pair-shape reranking. The accepted proofbench sample plus the newly accepted
frontier certificates still selected a high-signal top40 (`9/40` local,
`9/9` remote), adding new exact true rows without touching approximate layers.

The nine broader-rerank imports opened eight new source tails. Exhausting their
currently unattempted exact-unknown frontier rows produced a much stronger
source-tail batch:

- problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_after_tail45_top40_new_sources_tail_unattempted59_problems_20260601.jsonl`
- summary:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_after_tail45_top40_new_sources_tail_unattempted59_summary_20260601.json`
- selected unattempted pairs: `59`
- local candidates: `33/59`
- remote smoke accepted: `33/33`
- graph preview/import: read `33`, newly set `33`, conflict `0`
- import sha256:
  `986bd06f71f89dc5a67d5507f80409332a4dbf3038849f11be1a43466dff9a9d`
- accepted target groups:
  `53841 -> {53816}`,
  `56932 -> {4270}`,
  `17080 -> {29251,29259,29341,29354}`,
  `17965 -> {30128,30146,30191,30231}`,
  `17968 -> {30128,30153,30184,30231}`,
  `33755 -> {23112,23137,23168,23215,23277,37144,37172,37197,37247}`,
  `8900 -> {11711,11719,12102,12115,23112,23469,23516,23578}`,
  `15839 -> {27497,27562}`

The source `33755` closed completely. Source `8900` became a one-unknown row
whose only remaining target is `23137`; a focused source-pattern retry with
`timeout-ms=10000`, `seed-count=8`, and `max-patterns=4` produced no candidate,
so `(8900,23137)` is the current boundary for that source-tail surface.

Graph state after this source-tail import:

- zero-unknown source rows: `24,190`
- tiny-frontier source rows: `3,258`
- tiny-frontier unknown pairs: `14,704`
- one-unknown source rows: `539`
- graph bit counts: true `1,394,642,065`, false `2,387,094,055`,
  conflict `0`

Interpretation update: graph-rerank followed by source-tail exhaustion is a
reproducible loop. The global rerank found a small set of new source rows; the
source-tail pass then converted one of them (`33755`) into a fully classified
row and nearly closed another (`8900`) while preserving zero conflicts.

The source-tail59 import was followed by another global rerank using the
expanded accepted evidence pool:

- ranking:
  `data/processed/order5_strategy_registry/candidates/proofbench735_after_source_tail59_frontier_ranked_20260601.jsonl`
- summary:
  `data/processed/order5_strategy_registry/candidates/proofbench735_after_source_tail59_frontier_ranked_summary_20260601.json`
- evidence rows: `791`
- frontier pairs scanned: `14,704`
- attempted-pair exclusions: `1,010`
- ranked frontier pairs: `1,351`
- selected top problems: `40`
- local candidates: `9/40`
- remote smoke accepted: `9/9`
- graph preview/import: read `9`, newly set `9`, conflict `0`
- import sha256:
  `4efa48378f41f59a338eb5e39338b6d824454e87a4faa68f956aa56107900e9b`
- accepted pairs:
  `(57804,4341)`, `(57804,4270)`, `(8866,17942)`,
  `(16977,1427)`, `(30280,17965)`, `(37313,33755)`,
  `(13995,2127)`, `(7856,1525)`, `(8866,17850)`

Graph state after this rerank import:

- zero-unknown source rows: `24,190`
- tiny-frontier source rows: `3,258`
- tiny-frontier unknown pairs: `14,695`
- one-unknown source rows: `539`
- graph bit counts: true `1,394,642,074`, false `2,387,094,055`,
  conflict `0`

Interpretation update: the newly closed row can feed useful reverse or adjacent
edges: `(37313,33755)` and `(30280,17965)` were both accepted in this pass.
This suggests a second deterministic continuation strategy after row closure:
feed closed-row endpoints back into the global pair-shape reranker, then mine
their reverse/nearby tails.

## 2026-06-01 after-source-tail59 top40 source-tail pass

Using the graph frontier after the `after_source_tail59_frontier_top40` import, I
expanded the newly accepted sources
`57804, 8866, 16977, 30280, 37313, 13995, 7856`.  The generator selected all
currently unattempted tiny-tail unknowns for those rows, while excluding prior
`proofbench_z3_guided` problem pair indexes:

- problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_after_source_tail59_top40_new_sources_tail_unattempted45_problems_20260601.jsonl`
- generation summary:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_after_source_tail59_top40_new_sources_tail_unattempted45_summary_20260601.json`
- selected problems: `42`
- prior attempted pair indexes excluded: `1,050`

The local Z3 proof-guided run emitted `13` candidates before I interrupted a
stalled hard tail pair after `37/42` status rows.  All emitted candidates were
remote-smoked before import:

- candidates:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_after_source_tail59_top40_new_sources_tail_unattempted45_candidates_20260601.jsonl`
- status:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_after_source_tail59_top40_new_sources_tail_unattempted45_status_20260601.jsonl`
- smoke input:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_after_source_tail59_top40_new_sources_tail_unattempted45_smoke_input_20260601.jsonl`
- smoke results:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_after_source_tail59_top40_new_sources_tail_unattempted45_smoke_results_20260601.jsonl`
- smoke summary:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_after_source_tail59_top40_new_sources_tail_unattempted45_smoke_results_20260601_summary.json`
- accepted pair indexes:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_after_source_tail59_top40_new_sources_tail_unattempted45_accepted_pair_indexes_20260601.txt`
- run summary:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_after_source_tail59_top40_new_sources_tail_unattempted45_run_summary_20260601.json`

Remote smoke accepted `13/13`; the graph preview saw `13` newly set true bits and
`0` conflicts.  Import summary:

```json
{
  "layer": "true",
  "read_count": 13,
  "newly_set_count": 13,
  "already_set_count": 0,
  "conflict_count": 0,
  "sha256": "ef6736caa2d860c82ea0b6876d37966b04e717623a4573fcfcc055f624f8e3d5"
}
```

Accepted edges:

```text
16977 -> 1426
30280 -> 17856, 17942, 17953
37313 -> 23112, 23137, 23215, 23277, 33636, 33645, 33725
13995 -> 2035
7856  -> 1426
```

After import, graph bit counts are true `1,394,642,087`, false
`2,387,094,055`, conflict `0`.  The tiny frontier scan changed:

- zero-unknown source rows: `24,190`
- tiny-frontier source rows: `3,258`
- tiny-frontier unknown pairs: `14,682`
- one-unknown source rows: `539`

Representative graph status after import:

```bash
./.venv/bin/python scripts/data/build_order5_columnar_graph_store.py status \
  --store-dir data/processed/order5_columnar_graph_store \
  --eq-pair 37313 23112
```

returns `verdict: true`, while `37313 -> 23168` remains `unknown`.

Row-tail boundary after this pass:

```text
37313 -> {23168, 33739}
30280 -> {17850, 57315, 57378, 57521, 57683, 57860}
16977 -> {3456, 51176}
13995 -> {2134, 13493, 22235, 22441, 22475}
7856  -> {7569, 50299, 50327, 50503, 50553, 50619}
57804 -> {57317, 57323, 57326, 57682, 57697}
8866  -> {817, 3862, 3915, 23112, 52930, 53134}
```

Interpretation update: source-tail expansion remains productive after the global
pair-shape reranker opens a row, but yield is strongly row-dependent.  `37313`
is now a near-closed row (`2` unknowns left) and is the best next focused
retry.  `57804`/`8866` are current hard-boundary rows for the default auto
pattern mode.

## 2026-06-01 source-pattern near-closed chain

The row `37313` had two residual unknowns after the previous source-tail pass:

```text
37313 -> {23168, 33739}
```

Both residuals timed out under the earlier default `auto` pattern mode, but a
focused `source` pattern retry solved both:

```bash
/Users/zetyun2026/bing/projects/math-distill-stage2-proofbench/math-distill-stage2-proofbench/.venv/bin/python \
  /Users/zetyun2026/bing/projects/math-distill-stage2-proofbench/math-distill-stage2-proofbench/.codex/skills/stage2-proofbench-solver/scripts/z3_proof_guided_letshared.py \
  --problems data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_after_tail13_source37313_residual2_focused_problems_20260601.jsonl \
  --output data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_after_tail13_source37313_residual2_sourcepat_candidates_20260601.jsonl \
  --status data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_after_tail13_source37313_residual2_sourcepat_status_20260601.jsonl \
  --timeout-ms 10000 --seed-count 8 --max-lets 160 --max-code-len 80000 \
  --pattern-mode source --max-patterns 8
```

This started a short near-closed chain.  After each graph import, I followed
accepted target endpoints that were themselves tiny-frontier sources:

```text
37313 -> 23168, 33739
33739 -> 23112, 23215, 37144, 37247
37247 -> 23112, 23215, 33636, 33739
23215 -> 33636, 33739, 37144, 37247
```

All four focused passes were remote-smoked before import:

- chain summary:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_sourcepat_near_closed_chain_after_source37313_summary_20260601.json`
- final tiny frontier:
  `data/processed/order5_strategy_registry/candidates/true_mining_graph_tiny_frontiers_after_source23215_chain_sourcepat_import_20260601.json`
- final frontier pairs:
  `data/processed/order5_strategy_registry/candidates/true_mining_graph_tiny_frontier_after_source23215_chain_sourcepat_import_pairs_20260601.jsonl`

Graph import totals for the chain:

```json
{
  "remote_accepted": 14,
  "newly_set_true": 14,
  "conflict": 0,
  "closed_sources": [37313, 33739, 37247, 23215]
}
```

After the chain, graph bit counts are true `1,394,642,101`, false
`2,387,094,055`, conflict `0`.  Tiny frontier changed from the previous
post-tail13 state:

```text
zero-unknown source rows: 24,191 -> 24,194
tiny-frontier source rows: 3,257 -> 3,254
tiny-frontier unknown pairs: 14,680 -> 14,668
one-unknown source rows: 539 -> 539
```

Representative row checks:

```bash
./.venv/bin/python scripts/data/build_order5_columnar_graph_store.py row-summary \
  --store-dir data/processed/order5_columnar_graph_store \
  --source-id 37313

./.venv/bin/python scripts/data/build_order5_columnar_graph_store.py row-summary \
  --store-dir data/processed/order5_columnar_graph_store \
  --source-id 33739

./.venv/bin/python scripts/data/build_order5_columnar_graph_store.py row-summary \
  --store-dir data/processed/order5_columnar_graph_store \
  --source-id 37247

./.venv/bin/python scripts/data/build_order5_columnar_graph_store.py row-summary \
  --store-dir data/processed/order5_columnar_graph_store \
  --source-id 23215
```

Each returns `unknown_count: 0`.

Strategy update: when an `auto` Z3 pass times out on a near-closed row, retry
the residual row with `--pattern-mode source --max-patterns 8`, then follow
accepted target endpoints that are also tiny-frontier sources.  This turned one
2-unknown hard row into a four-row closure chain with no conflicts.

## 2026-06-01 source-pattern boundary tests after the chain

After closing `37313, 33739, 37247, 23215`, I ranked the remaining tiny frontier
for rows that might generalize the source-pattern chain:

- ranking:
  `data/processed/order5_strategy_registry/candidates/sourcepat_near_closed_candidate_ranking_after_source23215_chain_20260601.json`
- scanned tiny sources: `3,254`
- ranked rows with `unknown_count <= 4`: `1,824`

Two broad generalizations did not work:

```text
33726 -> {23112, 37144, 45037, 45291}
37200 -> {23112, 33636, 45037, 45291}
```

Both rows had success-chain source shape and all residual target endpoints were
already closed, but source-pattern Z3 emitted `0` candidates:

- problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_sourcepat_top2_closed_endpoint_rows_after_chain_problems_20260601.jsonl`
- status:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_sourcepat_top2_closed_endpoint_rows_after_chain_status_20260601.jsonl`

The `1`-unknown cluster-anchor rows also failed under source-pattern:

```text
5598  -> 33636
37197 -> 23112
```

- problems:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_sourcepat_cluster_one_unknown_after_chain_problems_20260601.jsonl`
- status:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_sourcepat_cluster_one_unknown_after_chain_status_20260601.jsonl`

This shows that neither `closed endpoint target` nor low unknown count is a
sufficient condition.

I then tested a smaller mutual tiny-frontier component:

```text
1658 -> {1832, 1861, 2441, 2470}
2470 -> {1629, 1658, 1832, 1861}
```

This produced partial positive evidence:

```text
accepted:
1658 -> 2441
1658 -> 2470
2470 -> 1629

still hard:
1658 -> 1832
1658 -> 1861
2470 -> 1658
2470 -> 1832
2470 -> 1861
```

The current verifier in this worktree expects judge-v2 control and rejects
`problem.pair_index`, so the remote-smoke input for judge-v2 must strip
`pair_index` from the nested `problem` object while preserving top-level graph
metadata.  The accepted smoke used:

- clean smoke input:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_sourcepat_mutual_component_1658_2470_judgev2_smoke_input_20260601.jsonl`
- smoke results:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_sourcepat_mutual_component_1658_2470_judgev2_smoke_results_20260601.jsonl`
- smoke summary:
  `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_sourcepat_mutual_component_1658_2470_judgev2_smoke_results_20260601_summary.json`

Remote judge-v2 accepted `3/3`; graph preview reported newly set `3` and
conflict `0`, then import used sha:

```text
c58b26eb82a6360d682b3df743bf1f10269b6e16c5f1dd344d5e34d5263cca62
```

After import:

```text
true bits: 1,394,642,104
false bits: 2,387,094,055
conflict bits: 0
tiny-frontier unknown pairs: 14,668 -> 14,665
1658 frontier: {1832, 1861}
2470 frontier: {1658, 1832, 1861}
```

Refined strategy boundary: the source-pattern chain is productive inside
specific local components, but broad closed-endpoint rows and single-anchor rows
can remain hard.  The next useful search should rank mutual/tightly connected
tiny components and include target-shape constraints, not just closed endpoint
counts.

## SCC 2064 Closed Anchors

After ranking the post-mutual-component tiny frontier by SCC structure, the
small component `[2064, 2673, 2876]` exposed six closed-anchor candidate edges:

```text
2064 -> 2644
2064 -> 2847
2673 -> 2035
2673 -> 2847
2876 -> 2035
2876 -> 2644
```

Source-pattern Z3 proof-guided generation produced Lean candidates for five of
the six rows; judge-v2 accepted all five generated candidates.  The hard anchor
was `2876 -> 2644`.

Imported graph evidence:

```text
accepted pairs:
2064 -> 2644
2064 -> 2847
2673 -> 2035
2673 -> 2847
2876 -> 2035

import sha:
33f81ab3deca720af06ad57781e746371485844b8d458506dc909c2b33d51315
```

After import, the remaining local frontiers were:

```text
2064 -> {2673, 2876}
2673 -> {2064, 2876}
2876 -> {2064, 2644, 2673}
```

This supports a useful refinement: closed-anchor edges inside a small SCC are
good source-pattern targets, while internal SCC edges and the anchor
`2876 -> 2644` need either target-shape-guided seeds or a different proof
surface.

Artifacts:

- `data/processed/order5_strategy_registry/candidates/sourcepat_tiny_component_scc_ranking_after_mutual1658_20260601.json`
- `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_sourcepat_scc2064_closed_anchors_candidates_20260601.jsonl`
- `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_sourcepat_scc2064_closed_anchors_judgev2_smoke_results_20260601.jsonl`
- `data/processed/order5_strategy_registry/candidates/proofbench_z3_guided_sourcepat_scc2064_closed_anchors_accepted_pair_indexes_20260601.txt`

## Proofbench Residual-1000-v2 Refresh

The external proofbench run for `residual-1000-v2` had advanced to `765 / 1000`
accepted rows when inspected, not the earlier `658` count.  Joined with
`data/residual-1000-v2/problems.jsonl`, these accepted rows split as:

```text
true accepted: 688
false accepted: 77
remaining: 235
```

Graph preview before import showed every accepted proofbench label was still new
to the local exact graph:

```text
true preview:  read 688, newly set 688, conflict 0
false preview: read 77,  newly set 77,  conflict 0
```

They were imported as exact Lean-certificate evidence:

```text
true import sha:  58abe3eafcb5b61e02a6e734d7b018c0eebdb9974978af4ae1d09e5ffd8b4213
false import sha: b20cfce8a8add8cffcc28291839a58e3e9def9ce05d2bb72b4474ef81a6eda9f

true bits:     1,394,642,797
false bits:    2,387,094,132
conflict bits: 0
```

The accepted set is broad rather than row-dense: `688` true certificates cover
many shapes, but the top exact source row contributes only three true labels.
That makes the proofbench harvest more valuable as a template bank and
frontier-ranking signal than as a single rectangular true strategy.

Useful mining consequences:

- `515` accepted shape buckets now have solved examples.
- `109` of the `235` remaining proofbench rows share an exact shape bucket with
  at least one accepted row; these are prime template-replay targets.
- `126` remaining rows have no same-shape accepted neighbor and should be
  treated as tail candidates for graph/SCC search or finite-model search.
- The dominant true route is `z3_proof_guided_v2_perrow_seed0_3` with `486`
  accepts; the next strongest true route families are seed/source-pattern
  variants.

Artifacts:

- `data/processed/order5_strategy_registry/candidates/proofbench_residual1000v2_accepted_graph_analysis_20260601.json`
- `data/processed/order5_strategy_registry/candidates/proofbench_residual1000v2_graph_import_summary_20260601.json`
- `data/processed/order5_strategy_registry/candidates/proofbench_residual1000v2_remaining_template_replay_priorities_20260601.json`
- `data/processed/order5_strategy_registry/candidates/true_mining_graph_tiny_frontiers_after_proofbench_residual1000v2_accepted_import_20260601.json`

### June 2 proofbench-to-graph follow-up

The accepted proofbench bank is useful in three distinct ways:

- exact evidence import: accepted Lean certificates can be copied into the
  graph true/false layers as pair-index evidence after a zero-conflict preview.
- seed-bank mining: accepted rows provide proof surfaces and shape buckets for
  focused Z3/template replay.
- frontier accounting: every accepted pair can shrink a source row's unknown
  count; row-closing effects should be attributed to the exact imported source,
  not to a broad shape rule.

The `residual1000-v2` source-pattern snapshot `s16-23` produced four candidate
Lean certificates. Under the default judge-v2 budget all four were rejected, but
adding deterministic `set_option maxHeartbeats 1000000` accepted one:

- accepted id: `residual1000_v2_0005`
- pair: `51943 -> 54575`, pair index `3250325223`
- graph import: read `1`, newly set `1`, conflict `0`
- true bits after import: `1,394,642,798`

Summary artifact:

- `data/processed/order5_strategy_registry/candidates/proofbench_residual1000v2_z3_source_s16_23_highhb_graph_import_summary_20260602.json`

A focused replay over the top same-shape true buckets selected eight remaining
`residual1000-v2` rows with `same_shape_true >= 3` and `same_shape_false == 0`.
Z3 closed two Lean candidates, and high-heartbeat judge-v2 accepted one:

- selected rows: `8`
- Z3 closed candidates: `2`
- high-heartbeat accepted: `1`
- accepted id: `residual1000_v2_0638`
- pair: `49956 -> 59785`, pair index `3125993908`
- graph import: read `1`, newly set `1`, conflict `0`
- true bits after import: `1,394,642,799`

This validates the shape-prior route as a ranking heuristic, not yet as a
deterministic strategy: `8 -> 2 -> 1` is good enough for mining priority, but
too selective for a broad registry rule.

Summary artifact:

- `data/processed/order5_strategy_registry/candidates/proofbench_residual1000v2_template_replay_top_true_shape8_graph_import_summary_20260602.json`

The latest inspected `residual-1000-v3` directory was
`artifacts/proofbench_runs/20260602-residual1000v3-goal-z3-seed0-3-v1`. Its
direct-true judge-v2 subrun had `34/37` accepted certificates, all true. Those
34 accepted rows were converted to a pair-index cache and imported into the
graph:

- graph preview: read `34`, newly set `34`, conflict `0`
- graph import sha256:
  `e1ec8a79503733776f896a5584c5f9a933b57ae6af438f3ca125d1fb34666b5e`
- true bits after import and concurrent graph updates: `1,394,642,834`
- false bits: `2,387,094,132`
- conflict bits: `0`

The accepted v3 rows are heavily same-shape concentrated. Top buckets:

- `roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0 -> same`: `8`
- `roots=var>mul|d=0>4|vc=4|lm=0|rm=1|vs=0 -> same`: `5`
- `roots=var>mul|d=0>4|vc=4|lm=1|rm=0|vs=0 -> same`: `4`
- `roots=mul>mul|d=2>3|vc=4|lm=0|rm=0|vs=0 -> same`: `4`

Summary artifact:

- `data/processed/order5_strategy_registry/candidates/proofbench_residual1000v3_direct_true_seed0_3_graph_import_summary_20260602.json`

One tiny-frontier row closed during the same graph window:

- source `8900`, target `23137`, pair index `556878060`
- source evidence:
  `order5_frontier_8900_23137_kb_chain_true_20260602`
- source kind:
  `proofbench.accepted_lean_certificate.true.kb_chain_frontier_closure`
- effect: source `8900` moved from one unknown to zero unknown.

This closure is intentionally not attributed to the v3 direct-true cache; it is
a separate KB-chain accepted certificate. The current frontier scan after all
current graph changes is:

- zero-unknown source rows: `24,195`
- tiny-frontier source rows: `3,253`
- tiny-frontier unknown pairs: `14,659`
- one-unknown source rows: `538`

## Graph Evidence

Store status queries before import showed representative pairs unknown:

```bash
./.venv/bin/python scripts/data/build_order5_columnar_graph_store.py status \
  --store-dir data/processed/order5_columnar_graph_store \
  --eq-pair 94 1

./.venv/bin/python scripts/data/build_order5_columnar_graph_store.py status \
  --store-dir data/processed/order5_columnar_graph_store \
  --eq-pair 458 411
```

Graph previews:

- `data/processed/order5_strategy_registry/candidates/true_template_target_instance_order4_to_order4_excluded_graph_preview_current_store_20260529.json`
  - read: `93,871`
  - newly set: `17,202`
  - conflict: `0`
- `data/processed/order5_strategy_registry/candidates/true_template_reflexive_target_xeqx_all_sources_graph_preview_current_store_20260529.json`
  - read: `62,575`
  - newly set: `21,623`
  - conflict: `0`
- `data/processed/order5_strategy_registry/candidates/true_template_joint_target_instance_o4o4_plus_reflexive_graph_preview_current_store_20260529.json`
  - read: `156,445`
  - newly set: `38,825`
  - conflict: `0`

## Proof Surface

Target-instance O4O4 uses the existing `target_instance_of_source` Lean certificate surface: introduce target variables and instantiate the source hypothesis; use `.symm` for reversed target matches.

Reflexive target closes by:

```lean
intro G _ h
intro x
rfl
```

Remote smoke:

- input: `data/processed/order5_strategy_registry/candidates/true_template_joint_target_instance_o4o4_plus_reflexive_smoke_input_20260529.jsonl`
- results: `data/processed/order5_strategy_registry/candidates/true_template_joint_target_instance_o4o4_plus_reflexive_smoke_results_20260529.jsonl`
- summary: `data/processed/order5_strategy_registry/candidates/true_template_joint_target_instance_o4o4_plus_reflexive_smoke_results_20260529_summary.json`
- accepted: `16/16`

## Artifacts

- `data/processed/order5_strategy_registry/candidates/true_template_target_instance_order4_to_order4_excluded_pair_indexes_20260529.txt`
- `data/processed/order5_strategy_registry/candidates/true_template_target_instance_order4_to_order4_excluded_current_profile_audit_20260529.json`
- `data/processed/order5_strategy_registry/candidates/true_template_reflexive_target_xeqx_all_sources_current_profile_audit_20260529.json`
- `data/processed/order5_strategy_registry/candidates/true_template_joint_target_instance_o4o4_plus_reflexive_pair_indexes_20260529.txt`
- `data/processed/order5_strategy_registry/candidates/true_template_joint_target_instance_o4o4_plus_reflexive_current_profile_audit_20260529.json`
- `data/processed/order5_strategy_registry/candidates/true_template_hinst_varroot_positive_components_residual_current_profile_after_targetinst_reflexive_audit_20260529.json`
- `data/processed/order5_strategy_registry/candidates/true_template_congr_context_source_instance_all_order5_pair_indexes_20260529.txt`
- `data/processed/order5_strategy_registry/candidates/true_template_congr_context_source_instance_all_order5_current_profile_audit_20260529.json`
- `data/processed/order5_strategy_registry/candidates/true_template_congr_context_source_instance_current_ready_packet_20260529_summary.json`
- `data/processed/order5_strategy_registry/candidates/true_template_joint_targetinst_reflexive_plus_congr_context_current_ready_packet_20260529_summary.json`
- `data/processed/order5_strategy_registry/candidates/true_template_recursive_congruence_symmetric_source_instance_all_order5_pair_indexes_20260529.txt`
- `data/processed/order5_strategy_registry/candidates/true_template_recursive_congruence_symmetric_source_instance_all_order5_current_profile_audit_20260529.json`
- `data/processed/order5_strategy_registry/candidates/true_template_recursive_congruence_symmetric_source_instance_current_ready_packet_20260529_summary.json`
- `data/processed/order5_strategy_registry/candidates/true_template_egraph_rewrite_search_after_recursive_tiny_frontier_pair_indexes_20260529.txt`
- `data/processed/order5_strategy_registry/candidates/true_template_hinst_grind_highfreq_tiny_frontier_accepted_pair_indexes_20260529.txt`
- `data/processed/order5_strategy_registry/candidates/true_template_hinst_grind_accepted_sources_frontier_expansion_accepted_pair_indexes_20260529.txt`
- `data/processed/order5_strategy_registry/candidates/true_template_graph_tiny_frontier_egraph_hinst_packet_20260529_summary.json`
