# 2026-05-21 opnorm top16 true template mining

日期：2026-05-21

## 目标

基于 `2026-05-21-opnorm-current-residual-stratified-diagnostic.md` 的 top residual shape bucket 诊断，继续挖掘 true deterministic strategy（真命题确定性策略），优先复核命中率最高的 `top_16` bucket。

本实验只做 candidate/seed 层探索，不修改 `solver.py`，不写正式 registry。

## 输入

- 诊断文档：`docs/experiments/2026-05-21-opnorm-current-residual-stratified-diagnostic.md`
- top bucket run：`artifacts/runs/2026-05-21/opnorm-current-residual-shape-stratified-20260521/`
- frozen opnorm solver：`solvers/solo_official/versions/2026-05-07/v1/solver.py`
- 当前 registry summary：`data/processed/order5_strategy_registry/coverage_summary.json`
- 当前 unresolved estimate：`228019453`
- remote judge：`http://10.220.69.172:8888`

## 方法

1. 从 `remote_tail_1000.json` 恢复 `top_16` 样本的 SOLVED/FAILED 标签。
2. 对 `top_16` 中 opnorm SOLVED 的 13 条样本重放 frozen solver。
3. replay 过程中只响应 `judge` call，不接 LLM；每个 deterministic certificate 走 remote judge。
4. 将 accepted certificate code 落盘，再按 proof body 形态聚类。

## 结果

`top_16` 原始分层统计是 `13/15` accepted，但 replay 后必须拆开看：

| 类别 | 数量 |
| --- | ---: |
| true certificate accepted | 11 |
| false countermodel accepted | 2 |
| rejected / unproved | 2 |

因此，`top_16` 的 shape bucket 本身不能直接作为 true strategy 条件；同一 bucket 内已经出现 accepted false countermodel。

true proof seed 聚类：

| proof cluster | seed count | 说明 |
| --- | ---: | --- |
| `hconst_match_collapse` | 5 | 先由 source 推出局部 constancy lemma，再用 match-collapse 证明 target |
| `nested_congrArg_match_collapse` | 3 | 通过嵌套 `congrArg` 改写内部子项，再反向使用 source hypothesis 收尾 |
| `plain_calc_match_collapse` | 3 | 纯 `calc` 链，若干次 source hypothesis 正反向实例化 |

两条 false accepted 已明确排除：

- `44361 -> 42479`
- `49622 -> 52989`

## 产物

- replay 全量记录：`data/processed/order5_strategy_registry/candidates/true_opnorm_top16_replay_20260521.jsonl`
- replay summary：`data/processed/order5_strategy_registry/candidates/true_opnorm_top16_replay_20260521_summary.json`
- true seed proof：`data/processed/order5_strategy_registry/candidates/true_opnorm_top16_true_seed_proofs_20260521.jsonl`
- seed candidate family summary：`data/processed/order5_strategy_registry/candidates/true_template_candidates_20260521_opnorm_top16_match_collapse_seed_summary.json`

## 2026-05-21 编译器推进

已把 `hconst_match_collapse` 的核心生成逻辑提取为 repo-native proof compiler：

- 模块：`src/math_distill_stage2/order5_opnorm_match_collapse.py`
- focused test：`tests/order5_strategy_registry/test_opnorm_match_collapse.py`
- top16 seed smoke：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_compiler_top16_seed_smoke_20260521_summary.json`
- shape-stratified probe：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_compiler_shape_stratified_probe_20260521_summary.json`
- 命中记录：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_compiler_shape_stratified_probe_20260521_hits.jsonl`
- current residual filtered probe：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_compiler_current_residual_mulmul_sample_seed20260526_summary.json`
- current residual smoke：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_compiler_current_residual_mulmul_smoke_20260521_summary.json`
- 可复现扫描入口：`scripts/data/scan_order5_opnorm_hconst_compiler.py`
- 带 coverage profile 的 sample delta：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_compiler_current_residual_mulmul_sample_seed20260526_summary_v4.json`
- 重构后 existing-hits smoke：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_compiler_current_residual_mulmul_sample_seed20260526_summary_v5.json`

验证结果：

| 检查 | 结果 |
| --- | ---: |
| top16 `hconst_match_collapse` seed compiler hits | 5/5 |
| top16 seed remote smoke | 5/5 accepted |
| shape-stratified sample compiler hits | 89/394 |
| shape-stratified representative remote smoke | 25/25 accepted |
| current residual `roots=mul>mul` filtered sample hits | 662/2518 |
| current residual representative remote smoke | 15/15 accepted |
| current coverage profile sample overlap | same true 0 / opposite false 0 |
| current coverage profile sample union increment lower bound | 662 |

该 compiler 同时对两条 top16 false countermodel 做了负例 focused test，当前不会误匹配：

- `44361 -> 42479`
- `49622 -> 52989`

这一步将 `hconst_match_collapse` 从 seed-only 证据推进到可扫描 compiler candidate；但还不是 register-ready candidate，因为尚未在 current residual 全局/大样本 universe 上去重、套 current registry mask，并计算 `exact_union_increment`。

一次无剪枝扫描 4179 条 current residual sample 超过两分钟，说明后续 coverage job 不能直接 full-pair/全样本硬扫；需要先按 source/target shape 和 source constancy prefilter 缩小候选空间，再做 exact union increment。

`summary_v4` 使用 `current_coverage_profile_v4_20260521.json` 对 662 个 sample hit 做了显式 pair overlap 检查，结果是 `same_verdict_overlap=0`、`opposite_verdict_overlap=0`、`union_increment=662`。这只是 sample lower bound（样本下界），不能替代全局 exact union increment。

## 2026-05-21 shape-bucket exact scan

为把 sample evidence 推进到可复核的 candidate 层，新增 source/target shape-pruned exact residual scanner：

- 扫描入口：`scripts/data/scan_order5_opnorm_hconst_shape_bucket.py`
- fast matcher：`src/math_distill_stage2/order5_opnorm_match_collapse.py`
- focused test：`tests/order5_strategy_registry/test_opnorm_match_collapse.py`
- coverage profile：`data/processed/order5_strategy_registry/candidates/current_coverage_profile_v5_20260521.json`

该 scanner 先按 source/target shape 全量取方程集合，再用 current coverage profile 精确排除已被 true/false registry 覆盖的 pair，只在 current residual pair 上运行 `hconst_match_collapse` proof compiler。输出仍是 candidate 层 explicit hit set（显式命中集），不直接修改正式 registry。

exact scan 结果：

| bucket | full shape pairs | current residual pairs | compiler hits | hit rate | exact true union increment | conflict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| top16 `d=1>4 vc=5 -> d=1>4 vc=3` | 1,037,184 | 681,520 | 282,836 | 41.5% | 282,836 | 0 |
| top13 `d=1>3 vc=5 -> d=1>4 vc=3` | 838,624 | 539,317 | 179,768 | 33.3% | 179,768 | 0 |
| top12 `d=1>3 vc=4 -> d=1>3 vc=3` | 1,657,840 | 1,233,214 | 452,540 | 36.7% | 452,540 | 0 |
| top08 `d=1>3 vc=4 -> d=1>4 vc=3` | 1,826,752 | 1,333,624 | 336,648 | 25.2% | 336,648 | 0 |
| combined top16+top13+top12+top08 | 5,360,400 | 3,787,675 | 1,251,792 | 33.0% | 1,251,792 | 0 |

低 ROI smoke：

| bucket | smoke residual pairs | compiler hits | hit rate | decision |
| --- | ---: | ---: | ---: | --- |
| top04 `d=1>4 vc=4 -> d=1>3 vc=4` | 20,000 | 14 | 0.07% | 不全扫 |
| top03 `d=1>4 vc=4 -> d=1>4 vc=3` | 20,000 | 651 | 3.3% | 暂不全扫 |
| top09 `d=1>4 vc=4 -> d=1>3 vc=3 lm=1` | 20,000 | 14 | 0.07% | 不全扫 |
| top15 `d=1>4 vc=4 -> d=1>3 vc=3` | 20,000 | 55 | 0.3% | 不全扫 |

合并复核：

- combined hit file：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_shape_top16_top13_top12_top08_exact_combined_20260521_hits.jsonl`
- combined summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_shape_top16_top13_top12_top08_exact_combined_20260521_summary.json`
- duplicate pair count：`0`
- after-merge projection：`deterministic_true_covered=1320494503`，`unresolved_estimate=225875234`
- registry status：`main_batch_candidate_ge1m_needs_remote_smoke_and_registry_rule`

remote official smoke：

- input：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_shape_top16_top13_top12_top08_smoke_20260521_input.jsonl`
- results：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_shape_top16_top13_top12_top08_smoke_20260521_results.jsonl`
- summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_shape_top16_top13_top12_top08_smoke_20260521_summary.json`
- backend：`http://10.220.69.172:8888`
- result：`20/20 accepted`

结论：`hconst_match_collapse` 已从 sample lower bound 推进到 exact current-residual main batch candidate。后续已由总控合入正式 register 层，见下节。

## 2026-05-21 hconst register merge

合入方式：

- 新增 coverage rule：`CompilerPairIndexesRule`
- strategy id：`true.proof.templatecheck.opnorm.hconst_match_collapse.top16_top13_top12_top08.v1`
- certificate generator：`opnorm_hconst_match_collapse`
- coverage kind：`compiler_pair_indexes`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_match_collapse_top16_top13_top12_top08_pair_indexes_20260521.txt`
- register cache summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_shape_top16_top13_top12_top08_register_pair_index_cache_20260521_summary.json`
- pair-index digest：`bc8de8f2a4077db4d550ec1dfb88760ffa3e737c62ec52ec0965bfea163d3eea`

register 复算结果：

- strategy count：`269`
- hconst strategy coverage count：`1,251,792`
- deterministic true covered：`1,320,494,503`
- deterministic false covered：`2,369,350,082`
- unresolved estimate：`225,848,615`
- conflict count：`0`

验证：

- focused tests：`tests/order5_strategy_registry/test_opnorm_match_collapse.py`、`tests/order5_strategy_registry/test_explicit_pairs_rule.py`
- test result：`31 passed`
- register summary command：`.venv/bin/python scripts/data/summarize_order5_strategy_coverage.py --source-target-cache data/processed/order5_strategy_registry/setcheck_source_target_cache.jsonl --output-dir data/processed/order5_strategy_registry`

该 register rule 不写入 125 万条 proof body，也不把它们当 proofbank known table；pair-index cache 是 compiler exact hit 的轻量索引，manifest 中保留 compiler、shape bucket、digest、current delta 和 remote smoke evidence。

## 2026-05-21 register gate 复核

按总控 register gate 重新审计 candidate 层：

- true 侧：`product_anchor_seed_lift` 已经进入 register；ETP Eq2 相关 accepted source 已通过 `singleton_seedbank` / specialization 覆盖，`missing32` delta preview 当前 `union_increment=0`。`opnorm.hconst_match_collapse` 已完成 exact current-residual scan、remote smoke 和 pair-index cache 复核，本轮正式合入 register 层。
- false 侧：当前 `discovered_predicatecheck_bank.jsonl` 已有 11 个 active predicatecheck bank row，并在正式 registry 展开为 97 个 predicatecheck shard。
- 剩余两个看似满足旧 candidate 门槛的 predicatecheck 行，按当前 register 临时重算后真实增量很小：

| candidate | 旧 candidate increment | 当前 register increment |
| --- | ---: | ---: |
| `all370.batch02` | 184469 | 7076 |
| `structured_le5.batch01` | 126828 | 7379 |
| 两者合并 | 311297 | 13990 |

因此除已合入的 hconst 主批外，本轮没有其它合适 candidate 提交到正式 register 层；上述两个 false predicate 候选按 ROI Gate 进入 parking lot。当前正式 `coverage_summary.json` 仍保持 `conflict_count=0`。

## 2026-05-21 hconst sandwich candidate 复核

在 hconst 主批合并后，继续把 `nested_congrArg_match_collapse` 和 `plain_calc_match_collapse` 的一部分 seed 抽象成 `hconst_sandwich_match_collapse` compiler。该 compiler 证明形态是：

1. target lhs 先由 source hypothesis 改写为中间项；
2. 中间项之间使用 hconst lemma 和 `congrArg` 改写；
3. 最后再由 source hypothesis 反向收尾到 target rhs。

已完成的 candidate 证据：

- compiler/module：`src/math_distill_stage2/order5_opnorm_match_collapse.py`
- exact scanner 支持：`scripts/data/scan_order5_opnorm_hconst_shape_bucket.py --compiler hconst-sandwich`
- topbucket sample probe：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_sandwich_topbucket_probe_20260521_summary.json`
- representative remote smoke：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_sandwich_topbucket_probe_smoke_fixed_20260521_summary.json`
- smoke result：`8/8 accepted`
- focused test：`tests/order5_strategy_registry/test_opnorm_match_collapse.py`

register gate 判断：

- 该 candidate 已有 Lean certificate smoke 证据，但仍缺可接受成本下的 exact current union increment。
- 使用 v6 coverage profile 对 top03 前 2000 个 current residual pair 做 prefix scan，结果为 `0` hit，不能作为新增覆盖下界。
- 对 sample 命中 source 附近做 source×target 小批 exact sweep 时，`hconst_sandwich` compiler 成本明显高于 hconst 主批，直接全扫不适合作为 register path。

因此 `hconst_sandwich_match_collapse` 当前保持 candidate 层，不提交 register。下一步应先增加 source-level prefilter 或把 proof family 拆成更窄的可索引子模板，再计算 exact union increment。

### top03 y-left core source-family exact candidate

为避免全桶扫描，已将 `hconst_sandwich_match_collapse` 改为 indexed matcher（索引化匹配器）：先用 source lhs/rhs unify target lhs/rhs，只枚举未绑定 source 变量，再检查中间项之间的 hconst/congrArg 改写。该改动保持原 seed 命中，同时把 20 条 sample hit 检查降到约 `0.02s`。

随后从 top03 代表 target 反推一组 `x * y = y * (y * T)` core source，分三种 source shape 做 exact current-residual scan：

| source shape | source ids | exact union increment |
| --- | --- | ---: |
| `d=1>4 vc=3 -> d=1>4 vc=3` | `41938,41946,41950` | `3,501` |
| `d=1>4 vc=4 -> d=1>4 vc=3` | `41939,41947,41951,41954,41955` | `5,820` |
| `d=1>4 vc=5 -> d=1>4 vc=3` | `41956` | `1,154` |
| combined | 9 source ids | `10,475` |

combined candidate 产物：

- hits：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_sandwich_top03_yyleft_core_sources_exact_combined_20260521_hits.jsonl`
- summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_sandwich_top03_yyleft_core_sources_exact_combined_20260521_summary.json`
- remote smoke input：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_sandwich_top03_yyleft_core_sources_smoke_20260521_input.jsonl`
- remote smoke summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_sandwich_top03_yyleft_core_sources_smoke_20260521_summary.json`

复核结果：

- exact current union increment：`10,475`
- conflict increment：`0`
- representative remote smoke：`18/18 accepted`
- after-merge projection：`deterministic_true_covered=1,320,504,978`，`unresolved_estimate=225,838,140`
- registry status：`parking_lot_below_100k_remote_smoke_passed`

该 candidate 证明 `hconst_sandwich` 已从 smoke-only 进入 exact candidate 层，但覆盖规模仍低于 register ROI gate。下一步应扩大 source prefilter，而不是把这 10k 直接合入 register。

### y-left repfilter targetbatch exact candidate 与 register merge

在 10k parking-lot candidate 基础上，继续扩大 source prefilter：保留 source text 以 `x * y = y * (y * T)` 开头、且能通过代表 target 复核的 23 个 source id，并对 10 个 target shape bucket 做 exact current-residual scan。

source ids：

`337, 3357, 3360, 3361, 41938, 41939, 41946, 41947, 41950, 41951, 41954, 41955, 41956, 42812, 42815, 42816, 42823, 42824, 42827, 42828, 42831, 42832, 42833`

candidate 产物：

- hits：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_sandwich_yyleft_repfilter_targetbatch_exact_combined_20260521_hits.jsonl`
- summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_sandwich_yyleft_repfilter_targetbatch_exact_combined_20260521_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_sandwich_yyleft_repfilter_targetbatch_pair_indexes_20260521.txt`
- register cache summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_sandwich_yyleft_repfilter_targetbatch_register_pair_index_cache_20260521_summary.json`
- pair-index digest：`73d95fcf11bc23740340b9b2aa462e9c1b257274eed810fd5f056c03fefc5a1a`

exact/register gate 复核：

| 指标 | 数值 |
| --- | ---: |
| source count | 23 |
| target shape count | 10 |
| exact pair count | 263,371 |
| exact union increment | 263,371 |
| conflict increment | 0 |
| duplicate rows | 0 |
| remote smoke | 80/80 accepted |

remote smoke 首轮为 `79/80 accepted`，唯一失败是 transient `HTTP 502`，重试该样例后 `1/1 accepted`，合并口径为 `80/80 accepted`。

已合入正式 register 层：

- strategy id：`true.proof.templatecheck.opnorm.hconst_sandwich_match_collapse.yyleft_repfilter_targetbatch.v1`
- coverage kind：`compiler_pair_indexes`
- certificate generator：`opnorm_hconst_sandwich_match_collapse`
- priority：`318`

正式 `coverage_summary.json` 复算结果：

- strategy count：`271`
- sandwich strategy coverage count：`263,371`
- deterministic false covered：`2,369,376,273`
- deterministic true covered：`1,320,756,862`
- unresolved estimate：`225,560,065`
- conflict count：`0`

说明：candidate register summary 中的 projection 是 against `current_coverage_profile_v6_20260521.json`，投影为 `deterministic_false_covered=2,369,350,082`、`deterministic_true_covered=1,320,757,874`、`unresolved_estimate=225,585,244`。正式复算时当前 register 还包含其它本地未在 v6 profile 中体现的策略变化，因此以最新 `coverage_summary.json` 为当前工作区口径，仍保持 `conflict_count=0`。

验证：

- focused tests：`.venv/bin/python -m pytest tests/order5_strategy_registry/test_opnorm_match_collapse.py tests/order5_strategy_registry/test_explicit_pairs_rule.py tests/order5_strategy_registry/test_coverage_profile.py -q`
- result：`35 passed`
- register summary command：`.venv/bin/python scripts/data/summarize_order5_strategy_coverage.py --source-target-cache data/processed/order5_strategy_registry/setcheck_source_target_cache.jsonl --output-dir data/processed/order5_strategy_registry`

### hconst lm/rm mainline v7 register merge

继续复核旧的 `hconst_match_collapse.lmrm_v1_20260521_mainline_batch` candidate。该 batch 最初使用 `current_coverage_profile_v5_20260521.json`，旧 summary 给出 exact union increment `1,111,200`；由于当前 register 已合入 hconst 主批和 hconst-sandwich targetbatch，不能直接沿用旧数字。

本轮先构建当前 register 的 v7 coverage profile：

- profile：`data/processed/order5_strategy_registry/candidates/current_coverage_profile_v7_20260521.json`
- timings：registry build `114.3s`，profile build `137.3s`，total `251.6s`
- true explicit pair count：`3,840,983`

用 v7 profile 重新审计 12 个 lm/rm/d23 component hit files：

- v7 delta summary：`data/processed/order5_strategy_registry/candidates/true_template_candidates_20260521_opnorm_hconst_mainline_batch_v7_delta_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_lmrm_mainline_pair_indexes_20260521.txt`
- register cache summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_lmrm_mainline_register_pair_index_cache_20260521_summary.json`
- pair-index digest：`ec2ee2a64b3916652995abaf72714c2c4e0140c810c9a791cf815fdd9b1a6b76`

v7/register gate 复核：

| 指标 | 数值 |
| --- | ---: |
| component count | 12 |
| source count | 800 |
| raw pair count | 1,112,800 |
| same-true overlap | 2,345 |
| exact union increment | 1,110,455 |
| conflict increment | 0 |
| remote smoke | 30/30 accepted |

已合入正式 register 层：

- strategy id：`true.proof.templatecheck.opnorm.hconst_match_collapse.lmrm_mainline.v1`
- coverage kind：`compiler_pair_indexes`
- certificate generator：`opnorm_hconst_match_collapse`
- priority：`319`

正式 `coverage_summary.json` 复算结果：

- strategy count：`272`
- lm/rm mainline strategy coverage count：`1,112,800`
- deterministic false covered：`2,369,376,273`
- deterministic true covered：`1,321,867,317`
- unresolved estimate：`224,449,610`
- conflict count：`0`

验证：

- focused tests：`.venv/bin/python -m pytest tests/order5_strategy_registry/test_opnorm_match_collapse.py tests/order5_strategy_registry/test_explicit_pairs_rule.py tests/order5_strategy_registry/test_coverage_profile.py -q`
- result：`37 passed`
- register summary command：`.venv/bin/python scripts/data/summarize_order5_strategy_coverage.py --source-target-cache data/processed/order5_strategy_registry/setcheck_source_target_cache.jsonl --output-dir data/processed/order5_strategy_registry`

### v8 residual follow-up：现有 hit set 审计与 top01 var→mul parking lot

在 `hconst_match_collapse.lmrm_mainline` 合入后，重新构建当前 register 的 v8 coverage profile：

- profile：`data/processed/order5_strategy_registry/candidates/current_coverage_profile_v8_20260521.json`
- timings：registry build `110.1s`，profile build `138.6s`，total `248.6s`
- true explicit pair count：`4,951,438`

随后批量审计已有 opnorm hconst / hconst-sandwich hit files：

- audit summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_existing_hits_v8_audit_20260521_summary.json`
- audit results：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_existing_hits_v8_audit_20260521_results.jsonl`
- audited hit file count：`59`
- positive hit file count：`12`
- 最大剩余 hit set：`true_template_opnorm_hconst_current_top01_source0000_0100_exact_20260521_hits.jsonl`，v8 union increment `18,350`

审计结论：已落盘的大块 hconst/hconst-sandwich hit sets 基本已被当前三条 opnorm register strategy 覆盖；剩余正增量主要集中在 `roots=var>mul|d=0>4|vc=4 -> roots=var>mul|d=0>4|vc=4` 的 top01 source slice。

对该 top01 var→mul 子族继续做 v8 exact residual scan：

| source offset | source count | union increment | conflict |
| ---: | ---: | ---: | ---: |
| 0-100 | 100 | 18,350 | 0 |
| 100-200 | 100 | 20,552 | 0 |
| 200-500 | 300 | 34,498 | 0 |
| 500-1000 | 500 | 0 | 0 |
| combined 0-500 | 500 | 73,400 | 0 |

combined candidate 产物：

- hits：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_current_top01_source0000_0500_exact_combined_v8_20260521_hits.jsonl`
- summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_current_top01_source0000_0500_exact_combined_v8_20260521_summary.json`
- candidate key：`true.proof.templatecheck.opnorm.hconst_match_collapse.varmul_top01_source0000_0500.v1`
- 初始 registry status：`parking_lot_below_100k_after_v8_audit`

该候选低于默认 100k tail gate，但属于当前 top residual bucket 的可解释
order4→order4 true 子族。用户确认后作为小 tail 合入 register 层：

- register strategy id：`true.proof.templatecheck.opnorm.hconst_match_collapse.varmul_top01_source0000_0500.v1`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_varmul_top01_source0000_0500_pair_indexes_20260521.txt`
- register summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_varmul_top01_source0000_0500_register_pair_index_cache_20260521_summary.json`
- remote smoke：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_current_top01_source0000_0500_smoke_20260521_summary.json`
- smoke result：`30/30 accepted`
- exact current union increment：`73,400`
- conflict increment：`0`
- pair-index SHA256：`004e08c239b4147a777eb31e871abd87c86985e047e68502b20003f6f5408e5a`

正式 `coverage_summary.json` 复算结果：

- strategy count：`273`
- deterministic false covered：`2,369,376,273`
- deterministic true covered：`1,321,940,717`
- unresolved estimate：`224,376,210`
- conflict count：`0`

负向探针：

| bucket | compiler | sample/residual scan | hits | timing |
| --- | --- | ---: | ---: | ---: |
| `roots=var>mul|d=0>5|vc=3 -> roots=var>mul|d=0>4|vc=3` | hconst | 20,000 | 0 | `6.9s` |
| `roots=mul>mul|d=1>4|vc=4 -> roots=mul>mul|d=2>3|vc=4` | hconst | 20,000 | 0 | `5.3s` |
| `roots=mul>mul|d=1>4|vc=4 -> roots=mul>mul|d=2>3|vc=4` | hconst-sandwich | 5,000 | 0 | `215.4s` |

结论：当前剩余 top residual 中，简单 hconst/hconst-sandwich 在上述高残差 bucket 没有可扩信号；下一步要么继续抽象 `plain_calc_match_collapse` / `nested_congrArg_match_collapse` compiler，要么寻找新的 source-level predicate，而不是继续用 hconst brute-force 扩扫这些 bucket。

## 结论

`top_16` 是高 ROI 的 true-template mining 区域，但不能按 bucket shape 直接注册。`hconst_match_collapse` 已经有项目内 proof compiler（证明编译器）和 25 条跨 bucket remote-accepted smoke 证据；下一步需要用 compiler 命中集计算 coverage union increment。

当前 `hconst_match_collapse` compiler 已有 top16+top13+top12+top08 的 current registry mask exact union increment：`1,251,792`，且 remote smoke `20/20 accepted`。该批已正式合入 register 层。`hconst_sandwich_match_collapse` 也已从 `10,475` parking-lot seed 扩展为 y-left repfilter targetbatch：exact union increment `263,371`、conflict `0`、remote smoke `80/80 accepted`，并已正式合入 register 层。随后 `hconst_match_collapse.lmrm_mainline` 经 v7 profile 复核仍有 exact union increment `1,110,455`、conflict `0`、remote smoke `30/30 accepted`，也已正式合入 register 层。`hconst_match_collapse.varmul_top01_source0000_0500` 作为小 tail，经 v8 profile 复核 exact union increment `73,400`、conflict `0`、remote smoke `30/30 accepted`，已正式合入 register 层。`hconst-default-sandwich` 已继续扩到 post-lowvc topbucket extension、frontier extension、edge extension、post-edge top40 extension、postedge2 top60 extension、postedge3 top80 extension 和 postedge4 top100 extension，分别新增 exact union increment `1,775,820`、`2,994,830`、`1,069,408`、`5,503,838`、`6,295,929`、`3,740,105` 与 `3,117,295`，conflict 均为 `0`，remote smoke 分别为 `80/80 accepted`、`90/90 accepted`、retry `80/80 accepted`、`120/120 accepted`、`120/120 accepted`、`120/120 accepted` 与 `120/120 accepted`，并正式合入 register 层。

### default-sandwich：plain/nested seed 抽象并合入

`plain_calc_match_collapse` 与 `nested_congrArg_match_collapse` 最初是 seed-only cluster。复核后发现：

- 现有 `hconst_sandwich` 慢 compiler 可覆盖 6 条 seed，但对 top16 bucket 无差别扫描过慢。
- 新增快路径 compiler：
  - `hconst-default-sandwich`：source 未约束变量统一用 target 首变量填充，用 hconst sandwich 闭合。
  - `hstep-default-sandwich`：补一类中间普通 `h` 子项重写，覆盖 `50837 -> 45406` 这类 seed。
- seed remote smoke：`6/6 accepted`。
- 6 个 seed source exact scan：combined union `2,788`，parking lot。
- 6 个 RHS role signature 扩成 `48` source：combined union `22,658`，remote smoke `24/24 accepted`，仍为 parking lot。
- 将 `hconst-default-sandwich` 扩到完整 top16 source shape：
  - source shape：`roots=mul>mul|d=1>4|vc=5|lm=0|rm=0|vs=0`
  - target shape：`roots=mul>mul|d=1>4|vc=3|lm=0|rm=0|vs=0`
  - source count：`888`
  - exact current union increment：`269,662`
  - conflict increment：`0`
  - remote smoke：`71/71 accepted`

候选产物：

- hits：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_top16_fullshape_v8_20260521_hits.jsonl`
- summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_top16_fullshape_v8_20260521_summary.json`
- smoke summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_top16_fullshape_smoke_20260521_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_top16_fullshape_pair_indexes_20260521.txt`
- register summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_top16_fullshape_register_pair_index_cache_20260521_summary.json`
- pair-index SHA256：`c2a582a3af265c76b6271d1af8c0d83ec811b44ad1c5b0d37d2229e2cdd26f20`

正式合入 register 层：

- strategy id：`true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.top16_fullshape.v1`
- strategy count：`274`
- deterministic false covered：`2,369,376,273`
- deterministic true covered：`1,322,210,379`
- unresolved estimate：`224,106,548`
- conflict count：`0`

### default-sandwich：d14vc4 multitarget 扩展并合入

top16 default-sandwich 合入后，v9 residual shape sample 显示 `d1>4/vc4` source 仍有百万级残差；沿用同一个 `hconst-default-sandwich` compiler 对两个 target shape 做 exact scan：

- source shape：`roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0`
- target shapes：
  - `roots=mul>mul|d=2>3|vc=4|lm=0|rm=0|vs=0`
  - `roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0`
- source count：`1,840`
- shape count：`1,453,600` + `1,452,810`
- combined exact current union increment：`2,906,410`
- conflict increment：`0`
- remote smoke：`86/86 accepted`

候选产物：

- hits：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d14vc4_multitarget_full_v9_20260521_hits.jsonl`
- summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d14vc4_multitarget_full_v9_20260521_summary.json`
- smoke summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d14vc4_multitarget_smoke_20260521_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_d14vc4_multitarget_pair_indexes_20260521.txt`
- register summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d14vc4_multitarget_register_pair_index_cache_20260521_summary.json`
- pair-index SHA256：`37972488274a6e1d7a6a62584cdfb45d660266859162ccb13e0f07e53260aa03`

正式合入 register 层：

- strategy id：`true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.d14vc4_multitarget.v1`
- strategy count：`275`
- deterministic false covered：`2,369,376,273`
- deterministic true covered：`1,325,116,789`
- unresolved estimate：`221,200,138`
- conflict count：`0`

### default-sandwich：d13vc4 multitarget 扩展并合入

d14vc4 合入后，v10 residual shape sample 将 `d1>3/vc4` source shape 推到 top residual；沿用 `hconst-default-sandwich` compiler 对三个 target shape 做 exact scan：

- source shape：`roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0`
- target shapes：
  - `roots=mul>mul|d=2>3|vc=4|lm=0|rm=0|vs=0`
  - `roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0`
  - `roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0`
- source count：`1,564`
- shape count：`1,278,040` + `1,085,757` + `1,278,384`
- combined exact current union increment：`3,642,181`
- conflict increment：`0`
- remote smoke：`90/90 accepted`

候选产物：

- hits：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d13vc4_multitarget_full_v10_20260521_hits.jsonl`
- summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d13vc4_multitarget_full_v10_20260521_summary.json`
- smoke summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d13vc4_multitarget_smoke_20260521_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_d13vc4_multitarget_pair_indexes_20260521.txt`
- register summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d13vc4_multitarget_register_pair_index_cache_20260521_summary.json`
- pair-index SHA256：`21583dd58ba8ccfba6e4e1522cb8cee12ced5c8dac000e072ee861137b72325e`

正式合入 register 层：

- strategy id：`true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.d13vc4_multitarget.v1`
- strategy count：`276`
- deterministic false covered：`2,369,376,273`
- deterministic true covered：`1,328,758,970`
- unresolved estimate：`217,557,957`
- conflict count：`0`

### default-sandwich：d14vc4 target-extension 扩展并合入

d13vc4 合入后，v11 residual shape sample 显示 `d1>4/vc4` source 仍有可解释 target-extension 残差。沿用 `hconst-default-sandwich` compiler 对四个新 target shape 做 exact scan：

- source shape：`roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0`
- target shapes：
  - `roots=mul>mul|d=2>3|vc=3|lm=0|rm=0|vs=0`
  - `roots=mul>mul|d=1>4|vc=3|lm=0|rm=0|vs=0`
  - `roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0`
  - `roots=mul>mul|d=1>3|vc=3|lm=1|rm=0|vs=0`
- source count：`1,840`
- shape count：`815,280` + `919,560` + `1,235,560` + `133,985`
- combined exact current union increment：`3,104,385`
- conflict increment：`0`
- remote smoke：`100/100 accepted`

候选产物：

- hits：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d14vc4_targetext_full_v11_20260521_hits.jsonl`
- summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d14vc4_targetext_full_v11_20260521_summary.json`
- smoke summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d14vc4_targetext_smoke_20260521_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_d14vc4_targetext_pair_indexes_20260521.txt`
- register summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d14vc4_targetext_register_pair_index_cache_20260521_summary.json`
- pair-index SHA256：`5672b1773fd340e0a03b3276f200a01ba5f62aefc1581d8f833fa4a7c3430340`

正式合入 register 层：

- strategy id：`true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.d14vc4_targetext.v1`
- strategy count：`277`
- deterministic false covered：`2,369,376,273`
- deterministic true covered：`1,331,863,355`
- unresolved estimate：`214,453,572`
- conflict count：`0`

### default-sandwich：low-vc extension 扩展并合入

d14vc4 target-extension 合入后，v12 residual shape sample 中仍有一批相邻低变量数（low-vc）形状可由 `hconst-default-sandwich` compiler 覆盖：

- source/target shape pairs：
  - `roots=mul>mul|d=1>4|vc=3|lm=0|rm=0|vs=0 -> roots=mul>mul|d=2>3|vc=4|lm=0|rm=0|vs=0`
  - `roots=mul>mul|d=1>4|vc=3|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0`
  - `roots=mul>mul|d=1>3|vc=3|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0`
  - `roots=mul>mul|d=1>3|vc=5|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>4|vc=3|lm=0|rm=0|vs=0`
- shape count：`428,720` + `428,720` + `361,831` + `267,180`
- combined exact current union increment：`1,486,451`
- conflict increment：`0`
- remote smoke：`80/80 accepted`

候选产物：

- hits：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_lowvc_extension_full_v12_20260521_hits.jsonl`
- summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_lowvc_extension_full_v12_20260521_summary.json`
- smoke summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_lowvc_extension_smoke_20260521_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_lowvc_extension_pair_indexes_20260521.txt`
- register summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_lowvc_extension_register_pair_index_cache_20260521_summary.json`
- pair-index SHA256：`8869fb145be04031067049c85f62af7c40ab0ccce9c34b2954701b2da535accb`

正式合入 register 层：

- strategy id：`true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.lowvc_extension.v1`
- strategy count：`278`
- deterministic false covered：`2,369,376,273`
- deterministic true covered：`1,333,349,806`
- unresolved estimate：`212,967,121`
- conflict count：`0`

### default-sandwich：topbucket extension 扩展并合入

low-vc extension 合入后，v13 residual shape sample 显示仍有三个同族 top bucket 可由 `hconst-default-sandwich` compiler 覆盖。按 current profile v13 做 exact scan 后，将三条 candidate 合并成同一 register batch：

- source/target shape pairs：
  - `roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>4|vc=3|lm=0|rm=0|vs=0`
  - `roots=mul>mul|d=1>3|vc=3|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0`
  - `roots=mul>mul|d=1>4|vc=5|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0`
- shape count：`475,084` + `425,040` + `875,696`
- combined exact current union increment：`1,775,820`
- conflict increment：`0`
- remote smoke：`80/80 accepted`

候选产物：

- v13 profile：`data/processed/order5_strategy_registry/candidates/current_coverage_profile_v13_20260522.json`
- residual sample：`data/processed/order5_strategy_registry/current_residual_after_lowvc_extension_shape_6000_seed20260522_summary.json`
- hits：
  - `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d13vc4_to_d14vc3_full_v13_20260522_hits.jsonl`
  - `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d13vc3_to_d14vc4_full_v13_20260522_hits.jsonl`
  - `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d14vc5_to_d14vc4_full_v13_20260522_hits.jsonl`
- register summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_topbucket_extension_register_pair_index_cache_20260522_summary.json`
- smoke summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_topbucket_extension_smoke_20260522_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_topbucket_extension_pair_indexes_20260522.txt`
- pair-index SHA256：`7b9f7b15c6fe982f00c53be3bfae2e8a2916efd48ef1fb3159127c3dc79c816a`

正式合入 register 层：

- strategy id：`true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.topbucket_extension.v1`
- strategy count：`279`
- deterministic false covered：`2,369,376,273`
- deterministic true covered：`1,335,125,626`
- unresolved estimate：`211,191,301`
- conflict count：`0`
- full coverage summary runtime：`10:57.11`
- focused tests：`tests/order5_strategy_registry/test_opnorm_match_collapse.py`，`35 passed`
- registry regression：`tests/order5_strategy_registry`，`84 passed`

### default-sandwich：frontier extension 扩展并合入

topbucket extension 合入后，v14 residual shape sample 显示 `hconst-default-sandwich` 仍能覆盖一批 frontier bucket。按 `>=100k` gate 过滤后，合并五个同族 shape pair；另有 `d14/vc4 -> d14/vc3_lm1rm1` 的 `80,076` 小尾巴保留在 parking lot，不进入 register batch。

- source/target shape pairs：
  - `roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=2>3|vc=3|lm=0|rm=0|vs=0`
  - `roots=mul>mul|d=1>4|vc=5|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0`
  - `roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>3|vc=3|lm=0|rm=0|vs=0`
  - `roots=mul>mul|d=1>3|vc=3|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>4|vc=3|lm=0|rm=0|vs=0`
  - `roots=mul>mul|d=1>4|vc=5|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>4|vc=5|lm=0|rm=0|vs=0`
- shape count：`716,044` + `747,592` + `837,400` + `269,808` + `423,986`
- combined exact current union increment：`2,994,830`
- conflict increment：`0`
- remote smoke：`90/90 accepted`

候选产物：

- v14 profile：`data/processed/order5_strategy_registry/candidates/current_coverage_profile_v14_20260522.json`
- residual sample：`data/processed/order5_strategy_registry/current_residual_after_topbucket_extension_shape_6000_seed20260522_summary.json`
- hits：
  - `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d13vc4_to_d23vc3_full_v14_20260522_hits.jsonl`
  - `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d14vc5_to_d13vc4_full_v14_20260522_hits.jsonl`
  - `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d14vc4_to_d13vc3_full_v14_20260522_hits.jsonl`
  - `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d13vc3_to_d14vc3_full_v14_20260522_hits.jsonl`
  - `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d14vc5_to_d14vc5_full_v14_20260522_hits.jsonl`
- register summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_frontier_extension_register_pair_index_cache_20260522_summary.json`
- smoke summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_frontier_extension_smoke_20260522_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_frontier_extension_pair_indexes_20260522.txt`
- pair-index SHA256：`765a27b399dbd79aa35191043ad3c1318edf7a85793cbe1b0e529f6141214c3b`

正式合入 register 层：

- strategy id：`true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.frontier_extension.v1`
- strategy count：`280`
- deterministic false covered：`2,369,376,273`
- deterministic true covered：`1,338,120,456`
- unresolved estimate：`208,196,471`
- conflict count：`0`
- full coverage summary runtime：`12:11.63`
- focused tests：`tests/order5_strategy_registry/test_opnorm_match_collapse.py`，`37 passed`
- registry regression：`tests/order5_strategy_registry`，`86 passed`

### default-sandwich：edge extension 扩展并合入

frontier extension 合入后，v15 residual shape sample 显示 `hconst-default-sandwich` 仍有两个同族 edge bucket 满足 register ROI gate。按 current profile v15 做 exact scan 后，将两个 shape pair 合并为同一 register batch；另有 `80,076` 与 `44,160` 两个小尾巴继续留在 parking lot。

- source/target shape pairs：
  - `roots=mul>mul|d=1>3|vc=5|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0`
  - `roots=mul>mul|d=1>4|vc=3|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0`
- shape count：`704,996` + `364,412`
- combined exact current union increment：`1,069,408`
- conflict increment：`0`
- remote smoke：首轮 `79/80 accepted`，唯一失败是 transient simple-api request failure；retry 后 `80/80 accepted`

候选产物：

- v15 profile：`data/processed/order5_strategy_registry/candidates/current_coverage_profile_v15_20260522.json`
- residual sample：`data/processed/order5_strategy_registry/current_residual_after_frontier_extension_shape_6000_seed20260522_summary.json`
- hits：
  - `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d13vc5_to_d14vc4_full_v15_20260522_hits.jsonl`
  - `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d14vc3_to_d13vc4_full_v15_20260522_hits.jsonl`
- register summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_edge_extension_register_pair_index_cache_20260522_summary.json`
- smoke summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_edge_extension_smoke_20260522_summary_retry.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_edge_extension_pair_indexes_20260522.txt`
- pair-index SHA256：`9b8f0f03a25e121b30b221514ba039d975ed5d5930d2f7e8e719515e80d5f4d1`

正式合入 register 层：

- strategy id：`true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.edge_extension.v1`
- strategy count：`281`
- deterministic false covered：`2,369,376,273`
- deterministic true covered：`1,339,189,864`
- unresolved estimate：`207,127,063`
- conflict count：`0`
- full coverage summary runtime：`13:13.09`
- focused tests：`tests/order5_strategy_registry/test_opnorm_match_collapse.py`，`39 passed`

### default-sandwich：post-edge top40 extension 扩展并合入

edge extension 与 post-frontier false predicate batch 合入后，重新按当前 register 口径采样 residual，并构建 v16 coverage profile。top40 residual shape 中仍有 23 个 positive shape pair 可由 `hconst-default-sandwich` compiler 精确覆盖，合并为一个 register batch：

- current residual sample：`data/processed/order5_strategy_registry/current_residual_after_edge_extension_shape_6000_seed20260522_summary.json`
- v16 profile：`data/processed/order5_strategy_registry/candidates/current_coverage_profile_v16_20260522.json`
- false covered：`2,369,435,311`
- true covered before merge：`1,339,189,864`
- unresolved before merge：`207,068,025`
- retained residual sample：`716/6000`，rate `0.1193`
- positive shape pair count：`23`
- combined exact current union increment：`5,503,838`
- conflict increment：`0`
- remote smoke：`120/120 accepted`

最大几个 shape pair 增量：

| rank | shape pair | exact union increment |
| ---: | --- | ---: |
| 26 | `d13/vc5 -> d23/vc4` | `705,456` |
| 13 | `d14/vc4 -> d23/vc5` | `701,520` |
| 30 | `d13/vc4 -> d14/vc5` | `617,108` |
| 9 | `d14/vc4 -> d13/vc5` | `567,220` |
| 12 | `d13/vc4 -> d23/vc3_lm1` | `282,278` |

候选与 register 产物：

- combined hits：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge_top40_extension_full_v16_20260522_hits.jsonl`
- candidate summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge_top40_extension_full_v16_20260522_summary.json`
- register summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge_top40_extension_register_pair_index_cache_20260522_summary.json`
- smoke summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge_top40_extension_smoke_20260522_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_postedge_top40_extension_pair_indexes_20260522.txt`
- pair-index SHA256：`f3beea2cb85741cb0ce1018d3d37449376f3b42bc7d8efb6b3ef8b2df329f1da`

正式合入 register 层：

- strategy id：`true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.postedge_top40_extension.v1`
- deterministic false covered：`2,369,435,311`
- deterministic true covered：`1,344,693,702`
- unresolved estimate：`201,564,187`
- conflict count：`0`
- full coverage summary runtime：`16:35.67`
- focused tests：`tests/order5_strategy_registry/test_opnorm_match_collapse.py`，`41 passed`
- registry regression：`tests/order5_strategy_registry`，`92 passed`

### default-sandwich：postedge2 top60 extension 扩展并合入

post-edge top40 extension 合入后，继续按当前 register 口径采样 residual，并构建 v17 coverage profile。top60 residual shape 中仍有 23 个 positive shape pair 可由 `hconst-default-sandwich` compiler 精确覆盖，合并为第二个 post-edge register batch：

- current residual sample：`data/processed/order5_strategy_registry/current_residual_after_postedge_top40_extension_shape_8000_seed20260522_summary.json`
- residual buckets：`data/processed/order5_strategy_registry/current_residual_after_postedge_top40_extension_shape_8000_seed20260522_residual_buckets.json`
- v17 profile：`data/processed/order5_strategy_registry/candidates/current_coverage_profile_v17_20260522.json`
- false covered：`2,369,435,311`
- true covered before merge：`1,344,693,702`
- unresolved before merge：`201,564,187`
- retained residual sample：`923/8000`，rate `0.115375`
- positive shape pair count：`23`
- combined exact current union increment：`6,295,929`
- conflict increment：`0`
- remote smoke：`120/120 accepted`

最大几个 shape pair 增量：

| rank | shape pair | exact union increment |
| ---: | --- | ---: |
| 15 | `d14/vc5 -> d23/vc4` | `879,520` |
| 27 | `d14/vc4 -> d14/vc5` | `701,520` |
| 29 | `d14/vc5 -> d13/vc3` | `506,680` |
| 60 | `d13/vc4 -> d13/vc5` | `498,944` |
| 33 | `d14/vc5 -> d23/vc3` | `493,296` |
| 34 | `d13/vc3 -> d23/vc4` | `424,989` |
| 24 | `d13/vc5 -> d13/vc3` | `400,488` |
| 31 | `d13/vc5 -> d23/vc3` | `395,360` |

候选与 register 产物：

- combined hits：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge2_top60_extension_full_v17_20260522_hits.jsonl`
- candidate summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge2_top60_extension_full_v17_20260522_summary.json`
- register summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge2_top60_extension_register_pair_index_cache_20260522_summary.json`
- smoke summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge2_top60_extension_smoke_20260522_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_postedge2_top60_extension_pair_indexes_20260522.txt`
- pair-index SHA256：`67f0a2c68e86d1968b781e1456b61fc756892195a555bd186ea39b0aa8f247ae`

正式合入 register 层：

- strategy id：`true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.postedge2_top60_extension.v1`
- deterministic false covered：`2,369,435,311`
- deterministic true covered：`1,350,989,631`
- unresolved estimate：`195,268,258`
- conflict count：`0`
- strategy count：`287`
- full coverage summary runtime：`18:08.88`
- focused tests：`tests/order5_strategy_registry/test_opnorm_match_collapse.py`，`43 passed`
- registry regression：`tests/order5_strategy_registry`，`95 passed in 501.57s`

### default-sandwich：postedge3 top80 extension 扩展并合入

postedge2 top60 extension 合入后，继续按当前 register 口径采样 residual，并构建 v18 coverage profile。top80 residual shape 中的 `mul>mul -> mul>mul` 子族仍有 19 个 positive shape pair 可由 `hconst-default-sandwich` compiler 精确覆盖，合并为第三个 post-edge register batch：

- current residual sample：`data/processed/order5_strategy_registry/current_residual_after_postedge2_top60_extension_shape_10000_seed20260522_summary.json`
- residual buckets：`data/processed/order5_strategy_registry/current_residual_after_postedge2_top60_extension_shape_10000_seed20260522_residual_buckets.json`
- v18 profile：`data/processed/order5_strategy_registry/candidates/current_coverage_profile_v18_20260522.json`
- false covered：`2,369,435,311`
- true covered before merge：`1,350,989,631`
- unresolved before merge：`195,268,258`
- retained residual sample：`1087/10000`，rate `0.1087`
- positive shape pair count：`19`
- combined exact current union increment：`3,740,105`
- conflict increment：`0`
- remote smoke：`120/120 accepted`

最大几个 shape pair 增量：

| rank | shape pair | exact union increment |
| ---: | --- | ---: |
| 28 | `d13/vc4 -> d23/vc5` | `617,065` |
| 55 | `d14/vc4 -> d23/vc4_lm1` | `308,054` |
| 57 | `d13/vc4 -> d13/vc3` | `288,142` |
| 27 | `d13/vc4 -> d23/vc3_rm1` | `282,324` |
| 66 | `d13/vc5 -> d13/vc5` | `274,834` |
| 21 | `d14/vc3 -> d14/vc3` | `271,911` |
| 77 | `d14/vc5 -> d22/vc4` | `267,840` |
| 73 | `d13/vc4 -> d14/vc4_rm1` | `229,644` |

候选与 register 产物：

- scan index：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_after_postedge2_top80_v18_20260522_scan_index.json`
- combined hits：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge3_top80_extension_full_v18_20260522_hits.jsonl`
- candidate summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge3_top80_extension_full_v18_20260522_summary.json`
- register summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge3_top80_extension_register_pair_index_cache_20260522_summary.json`
- smoke summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge3_top80_extension_smoke_20260522_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_postedge3_top80_extension_pair_indexes_20260522.txt`
- pair-index SHA256：`9ee3b27bcf4e6f6ae4d55d65e3903a6241bb47975abda6b3c534b5db250bd6f2`

正式合入 register 层：

- strategy id：`true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.postedge3_top80_extension.v1`
- deterministic false covered：`2,369,435,311`
- deterministic true covered：`1,354,729,736`
- unresolved estimate：`191,528,153`
- conflict count：`0`
- strategy count：`288`
- full coverage summary runtime：`19:43.21`
- focused tests：`tests/order5_strategy_registry/test_opnorm_match_collapse.py`，`45 passed`
- registry regression：`tests/order5_strategy_registry`，`97 passed in 495.80s`

### default-sandwich：postedge4 top100 extension 扩展并合入

postedge3 top80 extension 合入后，继续按当前 register 口径采样 residual，并构建 v19 coverage profile。top100 residual shape 中 `hconst-default-sandwich` 的前排 bucket 多数已清空，但后排仍有 18 个 positive shape pair，合并后仍超过 main register gate：

- current residual sample：`data/processed/order5_strategy_registry/current_residual_after_postedge3_top80_extension_shape_12000_seed20260522_summary.json`
- residual buckets：`data/processed/order5_strategy_registry/current_residual_after_postedge3_top80_extension_shape_12000_seed20260522_residual_buckets.json`
- v19 profile：`data/processed/order5_strategy_registry/candidates/current_coverage_profile_v19_20260522.json`
- false covered：`2,369,435,311`
- true covered before merge：`1,354,729,736`
- unresolved before merge：`191,528,153`
- retained residual sample：`1262/12000`，rate `0.1051666667`
- positive shape pair count：`18`
- combined exact current union increment：`3,117,295`
- conflict increment：`0`
- remote smoke：`120/120 accepted`

最大几个 shape pair 增量：

| rank | shape pair | exact union increment |
| ---: | --- | ---: |
| 51 | `d13/vc5 -> d13/vc4` | `596,116` |
| 85 | `d14/vc4 -> d22/vc4` | `446,400` |
| 69 | `d14/vc5 -> d23/vc5` | `424,464` |
| 95 | `d13/vc4 -> d23/vc4_rm1` | `267,920` |
| 54 | `d14/vc4 -> d14/vc4_lm1` | `264,000` |
| 77 | `d14/vc3 -> d23/vc3` | `240,456` |
| 49 | `d14/vc4 -> d23/vc3_lm1` | `220,502` |
| 82 | `d14/vc5 -> d23/vc3_rm1` | `194,931` |

候选与 register 产物：

- scan index：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_after_postedge3_top100_v19_20260522_scan_index.json`
- combined hits：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge4_top100_extension_full_v19_20260522_hits.jsonl`
- candidate summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge4_top100_extension_full_v19_20260522_summary.json`
- register summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge4_top100_extension_register_pair_index_cache_20260522_summary.json`
- smoke summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge4_top100_extension_smoke_20260522_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_postedge4_top100_extension_pair_indexes_20260522.txt`
- pair-index SHA256：`eca638eeb2bcb2a8f514baf21704e1649d4e7fb0f9b273dac6a60da84a15e77e`

正式合入 register 层：

- strategy id：`true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.postedge4_top100_extension.v1`
- deterministic false covered：`2,369,435,311`
- deterministic true covered：`1,357,847,031`
- unresolved estimate：`188,410,858`
- conflict count：`0`
- strategy count：`289`
- full coverage summary runtime：`20:56.58`
- focused tests：`tests/order5_strategy_registry/test_opnorm_match_collapse.py`，`47 passed`
- registry regression：`tests/order5_strategy_registry`，`99 passed in 511.62s`

### default-sandwich：postedge5 top120 extension 扩展并合入

postedge4 top100 extension 合入、false round2 fresh setcheck top100 注册后，
继续按当前 register 口径采样 residual，并使用 v20 coverage profile 扫描
top120 residual shape。`hconst-default-sandwich` 的前排 bucket 已基本枯竭，
但后排和少量 `var>mul -> mul>mul` tail bucket 仍能 batch 出百万级增量。

- current residual sample：`data/processed/order5_strategy_registry/current_residual_after_postedge4_top100_extension_shape_15000_seed20260522_summary.json`
- residual buckets：`data/processed/order5_strategy_registry/current_residual_after_postedge4_top100_extension_shape_15000_seed20260522_residual_buckets.json`
- v20 profile：`data/processed/order5_strategy_registry/candidates/current_coverage_profile_v20_after_postedge4_top100_20260522.json`
- false covered before merge：`2,369,622,194`
- true covered before merge：`1,357,847,031`
- unresolved before merge：`188,223,975`
- retained residual sample：`1560/15000`，rate `0.104`
- positive shape pair count：`19`
- combined exact current union increment：`1,913,716`
- conflict increment：`0`
- remote smoke：`120/120 accepted`，其中 1 条 simple-api request failure 重试后 accepted

最大几个 shape pair 增量：

| rank | shape pair | exact union increment |
| ---: | --- | ---: |
| 74 | `d14/vc5 -> d13/vc5` | `343,204` |
| 46 | `d14/vc4 -> d22/vc3` | `276,004` |
| 117 | `d13/vc4 -> d14/vc3_lm1` | `271,230` |
| 65 | `d13/vc3 -> d14/vc5` | `205,128` |
| 69 | `d14/vc4 -> d14/vc3_rm1` | `149,500` |
| 53 | `d13/vc5 -> d13/vc4_lm1` | `125,922` |

候选与 register 产物：

- scan index：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_after_postedge4_top120_v20_20260522_scan_index.json`
- combined hits：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge5_top120_extension_full_v20_20260522_hits.jsonl`
- candidate summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge5_top120_extension_full_v20_20260522_summary.json`
- register summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge5_top120_extension_register_pair_index_cache_20260522_summary.json`
- smoke summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge5_top120_extension_smoke_20260522_summary.json`
- smoke retry summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge5_top120_extension_smoke_20260522_retry_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_postedge5_top120_extension_pair_indexes_20260522.txt`
- pair-index SHA256：`8c4a1283bf1363d76a0238021dc01e08c568e5888735aa2f85259ab7bdd9c53b`

正式合入 register 层：

- strategy id：`true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.postedge5_top120_extension.v1`
- deterministic false covered：`2,369,622,194`
- deterministic true covered：`1,359,760,747`
- unresolved estimate：`186,310,259`
- conflict count：`0`
- strategy count：`330`
- full coverage summary runtime：约 `25m`
- focused tests：`tests/order5_strategy_registry/test_opnorm_match_collapse.py`，`49 passed`
- registry regression：`tests/order5_strategy_registry`，`103 passed in 615.77s`

### default-sandwich：postedge6 sample-hit top20 tail 扩展并合入

postedge5 合入后，`hconst-default-sandwich` 的 top residual bucket 已继续碎片化。
本轮不再盲扫 top-N residual shape，而是先在 current residual sample 上运行
fast matcher probe，然后只扩展 sample 命中的 top20 shape pair。该策略
仍保持零冲突，并新增百万级 true 覆盖。

- current residual sample：`data/processed/order5_strategy_registry/current_residual_after_postedge5_top120_extension_shape_18000_seed20260522_summary.json`
- residual buckets：`data/processed/order5_strategy_registry/current_residual_after_postedge5_top120_extension_shape_18000_seed20260522_residual_buckets.json`
- fast matcher probe：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_fast_hconst_default_after_postedge5_residual_sample_20260522_summary.json`
- v22 profile：`data/processed/order5_strategy_registry/candidates/current_coverage_profile_v22_after_postedge5_top120_20260522.json`
- false covered before merge：`2,369,622,194`
- true covered before merge：`1,359,760,747`
- unresolved before merge：`186,310,259`
- retained residual sample：`1861/18000`，rate `0.1033888889`
- fast probe hits：`hconst=180`，`hconst_default_sandwich=239`
- positive shape pair count：`20`
- combined exact current union increment：`2,008,676`
- conflict increment：`0`
- remote smoke：`120/120 accepted`

最大几个 shape pair 增量：

| rank | shape pair | exact union increment |
| ---: | --- | ---: |
| 12 | `d13/vc4 -> d13/vc3_lm1` | `287,228` |
| 19 | `d14/vc3 -> d14/vc5` | `206,904` |
| 2 | `d13/vc3 -> d23/vc5` | `205,128` |
| 5 | `d14/vc5 -> d13/vc4_rm1` | `158,160` |
| 17 | `d13/vc5 -> d14/vc3_lm1` | `149,266` |
| 16 | `d13/vc5 -> d23/vc4_rm1` | `147,710` |
| 4 | `d13/vc5 -> d13/vc4_rm1` | `125,965` |
| 11 | `d14/vc4 -> d23/vc6` | `121,600` |

候选与 register 产物：

- scan index：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_after_postedge5_samplehit_top20_v22_20260522_scan_index.json`
- combined hits：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge6_samplehit_top20_tail_full_v22_20260522_hits.jsonl`
- candidate summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge6_samplehit_top20_tail_full_v22_20260522_summary.json`
- candidate JSONL：`data/processed/order5_strategy_registry/candidates/true_template_candidates_20260522_opnorm_hconst_default_sandwich_postedge6_samplehit_top20_tail.jsonl`
- smoke summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge6_samplehit_top20_tail_smoke_20260522_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_postedge6_samplehit_top20_tail_pair_indexes_20260522.txt`
- pair-index SHA256：`ebd47b400aac1e2ab990cbee781447cd3ad13936bfe7ee4d70f1dbd4589611ec`

正式合入 register 层：

- strategy id：`true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.postedge6_samplehit_top20_tail.v1`
- deterministic false covered：`2,369,622,194`
- deterministic true covered：`1,361,769,423`
- unresolved estimate：`184,301,583`
- conflict count：`0`
- strategy count：`331`
- full coverage summary runtime：约 `30m`
- focused tests：`tests/order5_strategy_registry/test_opnorm_match_collapse.py`，`51 passed in 24.99s`
- registry regression：`tests/order5_strategy_registry`，`105 passed in 654.23s`

### default-sandwich：postedge7 sample-hit top20 tail 扩展并合入

postedge6 合入后，继续使用最新 register 口径采样 residual。top residual
bucket 里 `var>mul -> var>mul` 开始靠前，但 fast matcher probe 证明
`hconst-default-sandwich` 仍有一个可 batch 的 `mul>mul -> mul>mul` tail
批次；因此本轮继续合并同 family，而把 `var>mul` 新模板留给下一条主线。

- current residual sample：`data/processed/order5_strategy_registry/current_residual_after_postedge6_samplehit_top20_tail_shape_20000_seed20260522_summary.json`
- residual buckets：`data/processed/order5_strategy_registry/current_residual_after_postedge6_samplehit_top20_tail_shape_20000_seed20260522_residual_buckets.json`
- fast matcher probe：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_fast_hconst_default_after_postedge6_residual_sample_20260522_summary.json`
- v23 profile：`data/processed/order5_strategy_registry/candidates/current_coverage_profile_v23_after_postedge6_samplehit_top20_tail_20260522.json`
- false covered before merge：`2,369,622,194`
- true covered before merge：`1,361,769,423`
- unresolved before merge：`184,301,583`
- retained residual sample：`2041/20000`，rate `0.10205`
- fast probe hits：`hconst=173`，`hconst_default_sandwich=230`
- positive shape pair count：`20`
- combined exact current union increment：`2,769,157`
- conflict increment：`0`
- remote smoke：`120/120 accepted`

最大几个 shape pair 增量：

| rank | shape pair | exact union increment |
| ---: | --- | ---: |
| 18 | `d13/vc5 -> d23/vc5` | `340,680` |
| 2 | `d13/vc5 -> d14/vc5` | `340,550` |
| 4 | `d13/vc3 -> d23/vc3` | `238,188` |
| 12 | `d13/vc4 -> d14/vc4_lm1` | `229,638` |
| 16 | `d14/vc4 -> d22/vc5` | `199,200` |
| 3 | `d14/vc5 -> d23/vc3_lm1` | `194,931` |
| 15 | `d14/vc5 -> d14/vc3_rm1` | `185,748` |
| 7 | `d14/vc5 -> d13/vc4_lm1` | `158,160` |

候选与 register 产物：

- scan index：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_after_postedge6_samplehit_top20_v23_20260522_scan_index.json`
- combined hits：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge7_samplehit_top20_tail_full_v23_20260522_hits.jsonl`
- candidate summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge7_samplehit_top20_tail_full_v23_20260522_summary.json`
- candidate JSONL：`data/processed/order5_strategy_registry/candidates/true_template_candidates_20260522_opnorm_hconst_default_sandwich_postedge7_samplehit_top20_tail.jsonl`
- smoke summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge7_samplehit_top20_tail_smoke_20260522_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_postedge7_samplehit_top20_tail_pair_indexes_20260522.txt`
- pair-index SHA256：`fd0e15124305ea9b9d19a9b28ef8b05c7781181cdb1c5df62bb0343d6a91975e`

正式合入 register 层：

- strategy id：`true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.postedge7_samplehit_top20_tail.v1`
- deterministic false covered：`2,369,622,194`
- deterministic true covered：`1,364,538,580`
- unresolved estimate：`181,532,426`
- conflict count：`0`
- strategy count：`332`
- full coverage summary runtime：约 `30m`
- focused tests：`tests/order5_strategy_registry/test_opnorm_match_collapse.py`，`53 passed in 29.11s`
- registry regression：`tests/order5_strategy_registry`，`107 passed in 670.05s`

## 下一步

1. postedge7 后同 family 仍可能有 tail，但每轮都需要 sample-hit gate；不要盲扫 top-N。
2. 将 full `coverage_summary()` 从主循环中拆成长跑 gate，主循环先用 v23 profile delta、remote smoke 和 focused discoverability test 做快速判定。
3. 开始专门分析 `var>mul -> var>mul` residual top bucket，寻找新的 true template，而不是只继续扩同一个 hconst-default-sandwich compiler。
