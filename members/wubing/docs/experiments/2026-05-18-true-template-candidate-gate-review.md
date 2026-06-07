# 2026-05-18 true template candidates 总控复核

## 边界

- 使用技能边界：`stage2-strategy-start` 分流，`stage2-strategy-explore` 做 registry gate；候选 1 的 source-level singleton certificate 生成/验证按 `stage2-proofbank-*` 边界处理。
- 本轮没有修改 `solver.py`，没有修改 false registry，没有做 paircheck/setcheck，没有把未 official judge accepted 的 seed 或样例写成 accepted。
- 本轮没有静默合并 `strategies.json` / `order5_strategy_registry.py`。如需合并，只能作为后续单独变更提出。

## 输入与基线

读取并复核：

- `data/processed/order5_strategy_registry/candidates/true_template_candidates_20260518_topshape_true_templates.jsonl`
- `data/processed/order5_strategy_registry/candidates/true_template_candidates_20260518_topshape_true_templates_summary.json`
- `data/processed/order5_strategy_registry/strategies.json`
- `data/processed/order5_strategy_registry/coverage_summary.json`
- `src/math_distill_stage2/order5_strategy_registry.py`
- `data/processed/proof_banks/gpt_true_certificates/`
- `data/processed/order5_strategy_registry/top3_source_nontrivial_model_probe_120_seed20260521.json`
- `data/processed/proof_banks/gpt_true_certificates/candidate_pools/order5_top3_shape_singleton_like_sources_seed20260521.jsonl`

当前 `coverage_summary.json` 基线：

| 指标 | 数值 |
| --- | ---: |
| deterministic true covered | 624,436,821 |
| deterministic false covered | 2,334,245,819 |
| conflict_count | 0 |
| unresolved_estimate | 957,010,560 |

Schema / duplicate 检查结果已写入：

- `data/processed/order5_strategy_registry/candidates/true_template_gate_schema_duplicate_check_20260518.json`

检查结论：

- candidate JSONL: 2 行，candidate_key 无重复，必需字段未缺失。
- `strategies.json`: 73 个 strategy id，无重复，无缺失。
- phase-1 seed gate input: 29 个 seed，已排除 10653，无重复。
- law-instance smoke input: 20 个 pair，无重复，均含 `problem` 和 `answer`。

## 候选 1：singleton seedbank specialization top3 seed pool

Candidate:

`true.proof.templatecheck.singleton_seedbank_specialization.top3_nontrivial_seedpool.v1`

候选文件估算：

| 指标 | 数值 |
| --- | ---: |
| source_seed_count | 120 |
| estimated raw coverage | 74,600,392 |
| estimated raw after singleton collapse upper bound | 40,287,368 |
| estimated union increment | 23,243,813 |
| phase-1 projected union increment from 50k | 6,375,774 |

### Source-level singleton seed gate

从 phase-1 30 个 seed 开始，排除已经在当前 registry/seedbank 里的 10653，本轮 remote judge 29 个 source -> `Equation2 x = y`。

生成/验证 artifact：

- run dir: `artifacts/proof_bank_runs/2026-05-18/topshape-seedgate-phase1-20260518/`
- import summary: `artifacts/proof_bank_runs/2026-05-18/topshape-seedgate-phase1-20260518/summary.json`
- exact gate summary: `artifacts/proof_bank_runs/2026-05-18/topshape-seedgate-phase1-20260518/exact_registry_gate_summary.json`

Remote judge:

- backend pool: `http://10.220.69.153:8888,http://10.220.69.172:8888`
- selected backend: `http://10.220.69.153:8888`
- command family: `scripts/lean_certificates/proof_bank_import_responses.py --judge-backend remote-http --remote-judge-base-urls ... --remote-judge-no-cache`
- result: 11 accepted / 18 incorrect / 29 total, 0 skipped, 0 error, 0 timeout

Accepted seed ids:

`589, 6838, 7160, 9425, 10486, 11175, 11277, 14935, 21116, 27828, 38579`

Rejected / incorrect seed ids:

`6737, 6757, 6784, 6794, 6968, 7672, 9318, 9404, 9643, 11064, 11105, 11156, 11234, 12191, 16664, 25243, 36630, 39642`

Accepted remote run ids:

| seed | run id |
| ---: | --- |
| 589 | `stage2-pb-import-top3_shape_singleton_source_589_to_eq2-1779084393-e612fc94-11` |
| 6838 | `stage2-pb-import-top3_shape_singleton_source_6838_to_eq2-1779084414-4922f1bc-16` |
| 7160 | `stage2-pb-import-top3_shape_singleton_source_7160_to_eq2-1779084425-a5e0dd07-18` |
| 9425 | `stage2-pb-import-top3_shape_singleton_source_9425_to_eq2-1779084336-9c1790a8-00` |
| 10486 | `stage2-pb-import-top3_shape_singleton_source_10486_to_eq2-1779084336-1517e804-01` |
| 11175 | `stage2-pb-import-top3_shape_singleton_source_11175_to_eq2-1779084455-576fad81-26` |
| 11277 | `stage2-pb-import-top3_shape_singleton_source_11277_to_eq2-1779084462-a54a3027-28` |
| 14935 | `stage2-pb-import-top3_shape_singleton_source_14935_to_eq2-1779084347-d330d62f-03` |
| 21116 | `stage2-pb-import-top3_shape_singleton_source_21116_to_eq2-1779084358-9faba656-05` |
| 27828 | `stage2-pb-import-top3_shape_singleton_source_27828_to_eq2-1779084369-64550fbe-07` |
| 38579 | `stage2-pb-import-top3_shape_singleton_source_38579_to_eq2-1779084376-475f59f2-09` |

完整 accepted/rejected run URL 已保存在 `exact_registry_gate_summary.json` 的 `attempt_rows`。

### Exact coverage gate for accepted subset

只使用 official_judge_status=`accepted` 的 11 个 seed，重算 source closure 和 registry gate。

| 指标 | 数值 |
| --- | ---: |
| accepted seed count | 11 |
| exact source closure source_count | 149 |
| target_count | 62,576 |
| order4 excluded source_count | 65 |
| order4 excluded target_count | 4,694 |
| exact raw coverage | 9,018,630 |
| exact current union increment | 2,931,639 |
| current true overlap | 6,086,991 |
| conflict_count | 0 |

主要 current true overlap：

| overlap strategy | overlap_count |
| --- | ---: |
| `true.proof.templatecheck.singleton_seedbank_specialization.any_target.v1` | 6,086,991 |
| `true.proof.templatecheck.singleton_collapse.any_target.v1` | 4,755,705 |
| `true.proof.explicitbank.singleton_seedbank.any_target.v1` | 4,433,444 |

Gate 状态：

- phase-1 broad seed pool 不通过整体合并：29 个 seed 里 18 个 incorrect，必须继续排除。
- accepted 子集通过 exact gate：11 个 seed 的 source closure exact union increment 为 2,931,639，conflict_count=0。
- 但本轮不合并 registry。下一阶段可以提出一个单独变更：把这 11 个 accepted source-level singleton proof body 作为 seed-level singleton certificate 引入正式 seedbank，再由现有 singleton seedbank / specialization 策略自然扩展覆盖。

Canonical priority / supersedes 判断：

- 不建议新增一个独立 `top3_nontrivial_seedpool` strategy。
- canonical 注册方式应是扩充 `true.proof.explicitbank.singleton_seedbank.any_target.v1` 的 seed proof source，并重算 `true.proof.templatecheck.singleton_seedbank_specialization.any_target.v1`。
- priority 沿用现有 seedbank / specialization：seedbank priority 305，specialization priority 306。
- 不设置新的 `supersedes`；这是现有 seedbank family 的 seed 扩容，不是新的覆盖语义。

需要注意：

- `strategies.json` 当前 manifest 顶层 source_count 为 seedbank 3,734、specialization 8,296；可执行 registry 重算时 seedbank/source specialization 相关集合更大。由于 `coverage_summary.json` 的 deterministic true covered 与本轮 executable registry union baseline 一致，本轮 exact increment 使用 executable registry semantics。后续正式合并前建议顺手重建 manifest，避免 source_count 元数据滞后。

## 候选 2：target instance of source law-instance

Candidate:

`true.proof.templatecheck.law_instance.target_instance_of_source.v1`

候选文件估算：

| 指标 | 数值 |
| --- | ---: |
| estimated raw coverage | 1,550,864 |
| estimated union increment | 880,738 |
| sample hits all | 81 / 50,000 |
| sample candidate increment hits after collapse/seed | 46 |

### Dry-run certificate generator

本轮只做 dry-run，不改 `solver.py`，不改 registry。

生成逻辑：

- 若 target 是 source 的直接实例：`intro` target variables 后，调用 `h` 加 source variable 的 substitution terms。
- 若 target 的反向是 source 的实例：同样调用 `h`，最后加 `.symm`。
- 这是一条 pair-dependent predicate：能否覆盖取决于 `(source, target)` 这一对，不能用 `source_target_sets` 表达。

Smoke input / output：

- selection: `data/processed/order5_strategy_registry/candidates/true_template_law_instance_target_instance_smoke_20260518_selection.json`
- input: `data/processed/order5_strategy_registry/candidates/true_template_law_instance_target_instance_smoke_20260518_input.jsonl`
- results: `data/processed/order5_strategy_registry/candidates/true_template_law_instance_target_instance_smoke_20260518_results.jsonl`
- summary: `data/processed/order5_strategy_registry/candidates/true_template_law_instance_target_instance_smoke_20260518_summary.json`

Selection:

| 指标 | 数值 |
| --- | ---: |
| total smoke pairs | 20 |
| representative pairs | 2 |
| 50k sample hit pairs | 18 |
| direct orientation | 19 |
| symmetric orientation | 1 |
| sample rows scanned until 20 selected | 17,571 |

Remote judge:

- backend pool: `http://10.220.69.153:8888,http://10.220.69.172:8888`
- selected backend: `http://10.220.69.153:8888`
- run id prefix: `stage2-true-template-law-instance-smoke`
- cache: false
- result: 20 accepted / 0 incorrect / 20 total

Representative run ids:

| pair | orientation | run id |
| --- | --- | --- |
| 7671 -> 7580 | direct | `stage2-true-template-law-instance-smoke-law_instance_target_instance_7671_7580-1779086005-77639dfc-00` |
| 4556 -> 60613 | symmetric | `stage2-true-template-law-instance-smoke-law_instance_target_instance_4556_60613-1779086005-a1e49d70-01` |

完整 20 个 run URL 已保存在 `true_template_law_instance_target_instance_smoke_20260518_results.jsonl`。

Gate 状态：

- dry-run generator smoke 通过：20/20 accepted。
- 但还没有进入 formal registry exact gate：global exact pair-predicate raw coverage、current union increment、conflict_count 尚未物化计算。
- 因此本轮不能合并 registry，也不能宣布 global conflict_count=0。候选当前状态是 `smoke_passed; needs_pair_predicate_exact_gate`。

Canonical priority / supersedes 判断：

- 需要新增 pair-predicate coverage 表达，不能用 `source_target_sets` 近似，否则会把同一 source 的所有 target 都错误覆盖。
- 当前 `CoverageRule` 只有 `SourceTargetSetsRule` 和 `ExplicitPairsRule`。下一阶段可选两条路：
  - 物化 exact pair indexes，使用现有 `ExplicitPairsRule` 表达。
  - 或在 `order5_strategy_registry.py` 新增真正的 pair-predicate rule，再补 union/intersection/conflict 支持。
- 只有在 exact pair gate 证明它严格覆盖现有四条固定 law-instance strategy 且 conflict_count=0 后，才考虑设置 `supersedes`。当前不建议设置 supersedes。
- priority 暂不定稿。若 exact 后作为通用 law-instance family 合并，建议放在现有 law-instance family 附近，并以是否 supersede 现有 320-323 四条策略决定 priority。

## 总控结论

| Candidate | 当前 gate 状态 | 是否建议本轮合并 |
| --- | --- | --- |
| `singleton_seedbank_specialization.top3_nontrivial_seedpool.v1` | accepted 子集 exact gate 通过：11 accepted seeds，raw 9,018,630，union +2,931,639，conflict_count=0 | 否。本轮只建议进入单独的 seedbank 合并提案 |
| `law_instance.target_instance_of_source.v1` | dry-run generator smoke 通过：20/20 accepted；global exact pair gate 未完成 | 否。下一步先做 pair-predicate exact coverage/conflict gate |

下一步建议：

1. 对候选 1 单独提出 registry/proofbank 合并变更：只导入 11 个 accepted seed；不导入 18 个 incorrect seed；重建正式 seedbank/specialization manifest 与 coverage summary。
2. 对候选 2 先实现或物化 pair-predicate exact gate，计算 exact raw coverage、current union increment、conflict_count，再决定是否新增 registry rule。

## 追加执行：候选 1 accepted 子集合并

执行时间：2026-05-18。

本次只合并候选 1 的 11 个 accepted phase-1 seed；18 个 incorrect seed 没有进入 filtered merge run，也没有进入 harvest。

Filtered run：

- `artifacts/proof_bank_runs/2026-05-18/topshape-seedgate-phase1-accepted-20260518/`
- filtered_from_run: `artifacts/proof_bank_runs/2026-05-18/topshape-seedgate-phase1-20260518`
- accepted_seed_ids: `589, 6838, 7160, 9425, 10486, 11175, 11277, 14935, 21116, 27828, 38579`

Proof bank merge：

| 步骤 | 结果 |
| --- | --- |
| dry-run `proof_bank_merge_run.py` | new_attempts 11, new_problems 9, copied_blobs 11 |
| write merge | new_attempts 11, new_problems 9, copied_blobs 11 |
| bank accepted_count | 70,337 |
| bank attempt_count | 73,119 |
| bank problem_count | 72,291 |
| `proof_bank_check.py` | ok=true, errors=[] |

Registry/code 变更：

- `SINGLETON_SEEDBANK_HARVEST_SOURCE_RUN_IDS` 增加 `topshape-seedgate-phase1-20260518`。
- `SINGLETON_SEEDBANK_BARE_PROOF_SOURCE_RUN_IDS` 增加 `topshape-seedgate-phase1-20260518`。
- `singleton_seedbank_specialization_true_judge_code` 增加 harvested source-level proof body fallback，保证新 seed 不只影响 coverage，也能生成 specialization certificate。

Registry rebuild 后：

| 指标 | 数值 |
| --- | ---: |
| strategy_count | 73 |
| seedbank source_count | 5,984 |
| seedbank coverage_count | 370,347,118 |
| specialization source_count | 8,996 |
| specialization coverage_count | 557,091,301 |
| raw_true_union_covered | 627,368,460 |
| deterministic_true_covered | 627,368,460 |
| raw_false_union_covered | 2,334,245,819 |
| deterministic_false_covered | 2,334,245,819 |
| conflict_count | 0 |
| unresolved_estimate | 954,078,921 |

与合并前 deterministic true 624,436,821 相比，正式 registry 增量为 2,931,639，和 accepted 子集 exact gate 完全一致。

Harvest containment check：

| 检查 | 结果 |
| --- | --- |
| accepted_missing | `[]` |
| rejected_present | `[]` |
| seedbank signature mismatches | 0 |

验证：

- `uv run pytest -q tests/order5_strategy_registry/test_explicit_pairs_rule.py` -> 11 passed
- `uv run python scripts/lean_certificates/proof_bank_check.py --bank data/processed/proof_banks/gpt_true_certificates` -> ok=true
- harvested proof specialization generator remote smoke:
  - input: `data/processed/order5_strategy_registry/candidates/true_template_phase1_seedbank_specialization_smoke_20260518_input.jsonl`
  - summary: `data/processed/order5_strategy_registry/candidates/true_template_phase1_seedbank_specialization_smoke_20260518_summary.json`
  - result: 3/3 accepted
- `strategies.json` / `coverage_summary.json` / proofbank `bank_summary.json` JSON 解析通过

最终状态：

- 候选 1 accepted 子集已经完成正式 seedbank/specialization registry 合并。
- `solver.py` 未修改。
- 候选 2 仍保持 smoke-only 状态，下一步仍需 pair-predicate exact gate。

## 追加执行：候选 2 exact pair-predicate gate

执行时间：2026-05-18。

Candidate:

`true.proof.templatecheck.law_instance.target_instance_of_source.v1`

Exact gate artifact：

- `data/processed/order5_strategy_registry/candidates/true_template_law_instance_target_instance_exact_20260518_summary.json`

枚举方法：

- 对每个 target 和 reversed target 生成所有一阶 generalization canonical signature。
- 与 order<=5 equation signature 表回查 source id。
- 输出关系为 explicit ordered pairs `(source_id, target_id)`，并排除 `source_id == target_id`。
- 没有使用 `source_target_sets` 近似。

Exact coverage：

| 指标 | 数值 |
| --- | ---: |
| coverage_kind | explicit_pairs |
| exact raw coverage | 2,420,703 |
| source_count | 62,454 |
| target_count | 62,575 |
| exact current union increment | 1,171,358 |
| current true overlap | 1,249,345 |
| conflict_count | 0 |
| pair index SHA256 | `616ceb386f2d5aa5dbbfe2317e6984212c4a5de9bd25d8f2860bd886b1878a45` |

Orientation split：

| orientation | pair_count |
| --- | ---: |
| direct only | 2,235,149 |
| symmetric only | 51,336 |
| both orientations | 134,218 |

Overlap with current true registry：

| strategy | overlap_count |
| --- | ---: |
| `true.proof.templatecheck.singleton_seedbank_specialization.any_target.v1` | 1,051,220 |
| `true.proof.templatecheck.singleton_collapse.any_target.v1` | 963,744 |
| `true.proof.explicitbank.singleton_seedbank.any_target.v1` | 789,939 |
| `true.proof.templatecheck.term_shape_anchor.product.any_product_target.v1` | 203,232 |
| `true.proof.templatecheck.projection_normalizer.left.any_left_normal_target.v1` | 2,976 |
| `true.proof.templatecheck.projection_normalizer.right.any_right_normal_target.v1` | 2,976 |
| each existing fixed law-instance strategy | 2,120 |

现有四条 fixed law-instance strategy 的 coverage_count 均为 2,120，且候选 2 与每条 overlap_count 均为 2,120。因此候选 2 精确覆盖现有四条：

- `true.proof.templatecheck.law_instance.left_self_absorption.any_instance.v1`
- `true.proof.templatecheck.law_instance.right_self_absorption.any_instance.v1`
- `true.proof.templatecheck.law_instance.left_sandwich_absorption.any_instance.v1`
- `true.proof.templatecheck.law_instance.right_sandwich_absorption.any_instance.v1`

验证：

- dry-run generator remote smoke: 20/20 accepted。
- exact artifact JSON 解析通过。
- exact summary 的前 100 个 sample pairs 使用 `_match_equation_instance` 回查：0 error。

Gate 状态：

- exact pair-predicate gate 通过。
- conflict_count=0。
- 比候选阶段 50k projection 的 estimated raw 1,550,864 和 estimated union increment 880,738 都更高；exact raw 为 2,420,703，exact union increment 为 1,171,358。

Canonical priority / supersedes 建议：

- 建议后续单独合并为一个新的 explicit-pairs true strategy，而不是改写成 `source_target_sets`。
- 建议新 strategy key 仍使用 `true.proof.templatecheck.law_instance.target_instance_of_source`。
- 建议 priority 放在现有 fixed law-instance family 前，例如 319；现有四条 fixed law-instance strategy priority 为 320-323。
- 可以设置 `supersedes_strategy_ids` 覆盖上述四条 fixed law-instance strategies，或先保留它们 active 但让新 strategy 通过更低 priority 成为 canonical。
- 本轮未静默修改 `strategies.json` / `order5_strategy_registry.py` 来合并候选 2。

## 追加执行：候选 2 正式 registry 合并

执行时间：2026-05-18。

本次将 exact gate 通过的 candidate 2 合并为正式 true strategy：

- strategy_id: `true.proof.templatecheck.law_instance.target_instance_of_source.v1`
- coverage_kind: `explicit_pairs`
- priority: 319
- certificate_generator: `target_instance_of_source`
- `supersedes_strategy_ids`:
  - `true.proof.templatecheck.law_instance.left_self_absorption.any_instance.v1`
  - `true.proof.templatecheck.law_instance.right_self_absorption.any_instance.v1`
  - `true.proof.templatecheck.law_instance.left_sandwich_absorption.any_instance.v1`
  - `true.proof.templatecheck.law_instance.right_sandwich_absorption.any_instance.v1`

实现边界：

- 2026-05-26 更新：下面这节是当时的历史 gate 口径，已被全 order5 canonical summary 取代；当前 `coverage_summary.json` 必须包含 `order4_source_to_order4_target`。
- 新增 exact pair-predicate 枚举器，枚举 target / reversed target 的一阶 generalization signature，再回查 order<=5 source signature。
- 历史 gate 当时按 true source-target 模板约定排除 order4->order4 pair；这一节的旧 coverage 与当前 canonical 全域统计不同，不能作为正式 registry 口径继续引用。
- 新增 `target_instance_of_source_true_judge_code`，certificate 直接用 substitution terms 调用 source hypothesis；symmetric orientation 使用 `.symm`。
- `solver.py` 未修改。

正式 registry coverage：

| 指标 | 数值 |
| --- | ---: |
| strategy_count | 74 |
| target-instance coverage_count / pair_count | 2,326,832 |
| source_count | 61,625 |
| target_count | 57,882 |
| order4->order4 excluded pair_count | 93,871 |
| pair index SHA256 | `d57ac182448a099e33f9941733df5990799febe82ce28e699d169b54489f0d92` |
| raw_true_union_covered | 628,445,947 |
| deterministic_true_covered | 628,445,947 |
| raw_false_union_covered | 2,334,245,819 |
| deterministic_false_covered | 2,334,245,819 |
| conflict_count | 0 |
| unresolved_estimate | 953,001,434 |

相对候选 1 合并后的基线 deterministic true 627,368,460，候选 2 的正式 registry union increment 为 1,077,487。

验证：

- `uv run pytest -q tests/order5_strategy_registry/test_explicit_pairs_rule.py` -> 13 passed
- 正式 generator remote smoke:
  - input: `data/processed/order5_strategy_registry/candidates/true_template_law_instance_target_instance_registry_smoke_20260518_input.jsonl`
  - summary: `data/processed/order5_strategy_registry/candidates/true_template_law_instance_target_instance_registry_smoke_20260518_summary.json`
  - result: 3/3 accepted
- `strategies.json` / `coverage_summary.json` / registry smoke summary JSON 解析通过

最终状态：

- 候选 1 accepted seedbank 子集已合并。
- 候选 2 target-instance-of-source explicit-pairs strategy 已合并。
- `solver.py` 仍未修改。
