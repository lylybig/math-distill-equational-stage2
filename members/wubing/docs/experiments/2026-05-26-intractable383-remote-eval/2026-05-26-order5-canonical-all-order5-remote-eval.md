# Order5 canonical all-order5 coverage remote eval

## 结论

`members/wubing/data/processed/order5_strategy_registry/coverage_summary.json` 现在是唯一 canonical coverage summary，语义为 full order5 directed non-self pair space，包含 `order4_source_to_order4_target`。

在 `datasets/intractable_class_samples/*.jsonl` 的 383 题上，canonical registry 静态命中 275 题；这 275 题全部送 remote simple-api judge 后均为 `accepted`。剩余 108 题没有 registry 策略命中，本轮不计 accepted。

## Canonical registry snapshot

- `coverage_scope`: `all_order5_directed_nonself`
- `includes_order4_source_to_order4_target`: `true`
- `source_target_excluded_block_count`: `0`
- `total_pairs`: `3915693200`
- `deterministic_false_covered`: `2383452378`
- `deterministic_true_covered`: `1376984345`
- `unresolved_estimate`: `155256477`
- `conflict_count`: `0`

`strategies.json` 当前有 335 条 active strategy row；生成后的策略行没有 `source_target` excluded block。

## 383 remote judge eval

- dataset: `datasets/intractable_class_samples/*.jsonl`
- total: `383`
- static covered: `275`
- static uncovered: `108`
- static verdict mismatch: `0`
- remote judged: `275`
- remote accepted: `275`
- effective accepted on 383: `275`
- remaining uncovered/unaccepted on 383: `108`

Accepted breakdown:

- by oracle: `True=231`, `False=44`
- by class: `B-brute=11`, `C-cex=44`, `D-implicit=144`, `E-search=10`, `R-rewrite=60`, `V-vampire=6`

First remote pass returned `274/275 accepted`; the only failure was a transient `HTTP 502` on `mine_le4_646_2858` from `http://10.220.69.172:8888`. Retrying that one row on `http://10.220.69.153:8888` returned `accepted`.

No LLM was used in this eval. The answer code was generated from the canonical registry strategies and verified by remote judge.

## Local artifacts

- static eval: `/tmp/intractable383_canonical_all_order5_eval.json`
- remote input: `/tmp/intractable383_remote_judge_input.jsonl`
- first pass results: `/tmp/intractable383_remote_judge_results.jsonl`
- retry results: `/tmp/intractable383_remote_judge_failed_retry_results.jsonl`
- combined results: `/tmp/intractable383_remote_judge_combined_results.jsonl`
- combined summary: `docs/experiments/2026-05-26-intractable383-remote-eval/2026-05-26-intractable383-remote-judge-combined-summary.json`
- tmp combined summary: `/tmp/intractable383_remote_judge_combined_summary.json`
