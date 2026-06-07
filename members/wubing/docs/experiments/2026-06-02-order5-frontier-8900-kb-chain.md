# Order5 Frontier 8900 KB-Chain Closure

Date: 2026-06-02

## Target

- Source `8900`: `x = y * (z * (((z * z) * y) * x))`
- Target `23137`: `x = ((x * x) * y) * (y * (x * x))`
- Pair index: `556878060`

Before this run, graph `row-summary --source 8900` reported:

- true: `14`
- false: `62560`
- conflict: `0`
- unknown: `1`

The only frontier target was `23137`.

## Attempts

Small-budget probes that did not solve the pair:

- `z3_proof_guided_letshared`, source/all patterns, seeds `0..3`, `5000ms`: all timed out with no candidate.
- `pysat_finite_witness`, orders `4 5 6`, `cadical195`, `200000` conflict budget: no finite countermodel.
- `equational_rewrite_chain`, depth `5`: no candidate.

Successful route:

```bash
uv run python .codex/skills/stage2-proofbench-solver/scripts/kb_rule_chain_probe.py \
  --problems /tmp/order5_frontier_8900_23137_problem.jsonl \
  --output /tmp/order5_frontier_8900_23137_kb_chain_candidates.jsonl \
  --status /tmp/order5_frontier_8900_23137_kb_chain_status.jsonl \
  --max-rules 80 --max-size 16 --rounds 4 \
  --max-depth 5 --max-nodes 30000 --max-term-size 20 \
  --max-neighbors 80 --max-free-choices 2 \
  --method order5_graph_frontier_kb_chain_probe
```

Remote judge-v2 accepted all three emitted true candidates:

- `rule_count=10`, `step_count=1`, `code_len=3249`
- `rule_count=20`, `step_count=1`, `code_len=8074`
- `rule_count=40`, `step_count=1`, `code_len=22186`

Summary:

- accepted: `3/3`
- error codes: `ACCEPTED=3`
- backend: `http://10.220.69.172:8890`

## Graph Import

Accepted pair cache:

- `data/processed/order5_strategy_registry/candidates/order5_frontier_8900_23137_kb_chain_accepted_pair_indexes_20260602.jsonl`

This is exact true evidence for one pair. It closes source row `8900`, but it is not a registry-wide deterministic strategy.

Preview before import:

- read: `1`
- newly set: `1`
- already set: `0`
- conflict: `0`

Import result:

- layer: `true`
- source id: `order5_frontier_8900_23137_kb_chain_true_20260602`
- source kind: `proofbench.accepted_lean_certificate.true.kb_chain_frontier_closure`
- newly set: `1`
- conflict: `0`
- sha256: `5b59be326545f2704cbe3a5c8593c279491939d08ab3036234ffa10224e17cf9`

After import, graph `row-summary --source 8900` reports:

- true: `15`
- false: `62560`
- conflict: `0`
- unknown: `0`
