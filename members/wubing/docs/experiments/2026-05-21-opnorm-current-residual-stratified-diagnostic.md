# 2026-05-21 opnorm current residual stratified diagnostic

日期：2026-05-21

## 目标

评估官方提供的 opnorm `solver.py` 在 current unresolved residual（当前未解决残差）上的真实增量效果，并用 top residual shape bucket（残差形状桶）分层诊断后续确定性策略挖掘方向。

本实验不修改 `solver.py`，只跑 frozen solver snapshot（冻结求解器快照）和 run-local problem set。

## 输入

- opnorm solver snapshot：`solvers/solo_official/versions/2026-05-07/v1/solver.py`
- solver sha256：`77d56a5cb6178bf9a6a1d8149e187cc800c3be90ecb017e15e423b6ce50602b1`
- current coverage summary：`data/processed/order5_strategy_registry/coverage_summary.json`
- current unresolved estimate：`228143690`
- remote simple-api backend：`http://10.220.69.172:8888`
- max workers：`16`

## 随机 residual 估计

先从 current false-uncovered 候选采样，再用 current true strategies 过滤，得到 current residual pool（当前残差池），然后抽样跑 opnorm。

### cv100

- run id：`opnorm-current-residual-cv100-20260521`
- 本地目录：`artifacts/runs/2026-05-21/opnorm-current-residual-cv100-20260521/`
- 抽样：`1000` 个 false-uncovered 中留下 `149` 个 current residual，固定 seed 抽 `100`
- 结果：`30A / 70R / 0E`
- accepted verdict：`true=28`，`false=2`
- judge calls：`800`
- LLM calls：`70`
- cache exact hits：`0`

### cv500

在 cv100 基础上，额外抽不重叠 `400` 题。

- additional run id：`opnorm-current-residual-cv500-add400-20260521`
- combined summary：`artifacts/runs/2026-05-21/opnorm-current-residual-cv500-20260521/combined_cv500_summary.json`
- 结果：`168A / 332R / 0E`
- accepted rate：`33.6%`
- Wilson 95% 区间：`29.6% - 37.9%`
- accepted verdict：`true=159`，`false=9`
- judge calls：`3789`
- LLM calls：`332`
- cache exact hits：`0`
- projected residual accepted（按 `228143690` 外推）：约 `76656280`
- projected Wilson 95%：约 `67527635 - 86355484`

日志解析确认：随机 residual 的 accepted 都是 `llm:0`，rejected 都是 `llm:1`。也就是说，在这些样本上 LLM fallback（大模型兜底）没有贡献 accepted；opnorm 的有效增量来自 deterministic path（确定性路径）。

## Top Bucket 分层诊断

随机 residual 估计回答整体效果；top bucket 分层诊断用于找后续确定性策略挖掘的高 ROI 区域。该分层样本不是无偏整体估计。

### 样本口径

- run id：`opnorm-residual-shape-stratified-20260521`
- 本地目录：`artifacts/runs/2026-05-21/opnorm-current-residual-shape-stratified-20260521/`
- analysis：`artifacts/runs/2026-05-21/opnorm-current-residual-shape-stratified-20260521/shape_bucket_analysis.json`
- source reservoir：`data/processed/order5_strategy_registry/current_residual_after_k40_shape_20000_seed20260521_residual_sample.jsonl`
- top bucket ranking：同 reservoir 的 `current_residual_after_k40_shape_20000_seed20260521_residual_buckets.json`
- 排除：已跑过的 cv500 pair
- 样本：top20 buckets 每桶最多 `15` 题，tail 对照 `100` 题
- 实际样本数：`394`
  - top20：`294`
  - tail：`100`
  - top11/top14/top18/top19 因排除 cv500 后可用样本不足，分别为 `12/14/14/14`

### 总体结果

| 分组 | total | accepted | rejected | accepted rate |
| --- | ---: | ---: | ---: | ---: |
| top20 buckets | 294 | 148 | 146 | 50.3% |
| tail | 100 | 32 | 68 | 32.0% |
| all stratified | 394 | 180 | 214 | 45.7% |

全局 accepted verdict：`true=176`，`false=4`。

日志解析同样确认：`llm_on_accepted=0`，`llm_on_rejected=214`。

## Bucket 结果

| group | n | accepted | rate | bucket |
| --- | ---: | ---: | ---: | --- |
| top_01 | 15 | 5 | 33.3% | `roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0` |
| top_02 | 15 | 7 | 46.7% | `roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=2>3|vc=4|lm=0|rm=0|vs=0` |
| top_03 | 15 | 10 | 66.7% | `roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>4|vc=3|lm=0|rm=0|vs=0` |
| top_04 | 15 | 11 | 73.3% | `roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0` |
| top_05 | 15 | 8 | 53.3% | `roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0` |
| top_06 | 15 | 10 | 66.7% | `roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=2>3|vc=4|lm=0|rm=0|vs=0` |
| top_07 | 15 | 6 | 40.0% | `roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0` |
| top_08 | 15 | 7 | 46.7% | `roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>4|vc=3|lm=0|rm=0|vs=0` |
| top_09 | 15 | 10 | 66.7% | `roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>3|vc=3|lm=1|rm=0|vs=0` |
| top_10 | 15 | 5 | 33.3% | `roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=2>3|vc=5|lm=0|rm=0|vs=0` |
| top_11 | 12 | 0 | 0.0% | `roots=var>mul|d=0>5|vc=3|lm=0|rm=0|vs=0 -> roots=var>mul|d=0>4|vc=3|lm=0|rm=0|vs=0` |
| top_12 | 15 | 11 | 73.3% | `roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>3|vc=3|lm=0|rm=0|vs=0` |
| top_13 | 15 | 12 | 80.0% | `roots=mul>mul|d=1>3|vc=5|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>4|vc=3|lm=0|rm=0|vs=0` |
| top_14 | 14 | 0 | 0.0% | `roots=var>mul|d=0>5|vc=3|lm=0|rm=0|vs=0 -> roots=var>mul|d=0>4|vc=4|lm=0|rm=0|vs=0` |
| top_15 | 15 | 6 | 40.0% | `roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>3|vc=3|lm=0|rm=0|vs=0` |
| top_16 | 15 | 13 | 86.7% | `roots=mul>mul|d=1>4|vc=5|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>4|vc=3|lm=0|rm=0|vs=0` |
| top_17 | 15 | 8 | 53.3% | `roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=2>3|vc=3|lm=0|rm=0|vs=0` |
| top_18 | 14 | 7 | 50.0% | `roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>4|vc=5|lm=0|rm=0|vs=0` |
| top_19 | 14 | 4 | 28.6% | `roots=mul>mul|d=1>4|vc=3|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0` |
| top_20 | 15 | 8 | 53.3% | `roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>3|vc=5|lm=0|rm=0|vs=0` |
| tail | 100 | 32 | 32.0% | not top20 |

## 结论

1. `sample200` 的 `87.5%` accepted rate 不能代表 current residual。
2. current residual 随机样本显示 opnorm 可吃掉约三成多 residual，点估计 `33.6%`。
3. top20 residual shape buckets 明显更适合 opnorm deterministic path，分层 accepted rate 达到 `50.3%`。
4. tail 对照 `32.0%` 与随机 residual `33.6%` 接近，说明 top bucket 的高命中不是整体偏差，而是真正的形状集中信号。
5. 所有 accepted 都是 `llm:0`，所有 rejected 都是 `llm:1`；后续应优先挖 deterministic templates（确定性模板）或 finite-model predicates（有限模型谓词），不是继续扩大 LLM fallback。

## 下一步

优先挖高命中 bucket：

- `top_16`：`13/15`，最高 ROI。
- `top_13`：`12/15`。
- `top_04`、`top_12`：各 `11/15`。
- `top_03`、`top_06`、`top_09`：各 `10/15`。

建议工作流：

1. 从 `shape_bucket_analysis.json` 找出高命中 bucket 的 accepted problem ids。
2. 对这些 ids 运行 opnorm 结果解析，抽取 accepted certificate 或 solver branch 命中路径。
3. 按 bucket 归纳 source/target term pattern，判断是 true proof template 还是 false finite-model predicate。
4. 先在 `data/processed/order5_strategy_registry/candidates/` 落候选，不直接改正式 registry。
5. 对候选做 union increment、conflict count、remote official smoke，再决定是否合并。

## 后续进展：hconst exact candidate

已按上述工作流推进 `hconst_match_collapse` true proof compiler：

- top16 exact current-residual scan：`282,836` true union increment，conflict `0`。
- top13 exact current-residual scan：`179,768` true union increment，conflict `0`。
- top12 exact current-residual scan：`452,540` true union increment，conflict `0`。
- top08 exact current-residual scan：`336,648` true union increment，conflict `0`。
- top16+top13+top12+top08 combined：`1,251,792` true union increment，duplicate pair `0`，conflict `0`。
- representative remote smoke：`20/20 accepted`。

候选产物：

- `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_shape_top16_exact_20260521_summary.json`
- `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_shape_top13_exact_20260521_summary.json`
- `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_shape_top12_exact_20260521_summary.json`
- `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_shape_top08_exact_20260521_summary.json`
- `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_shape_top16_top13_top12_top08_exact_combined_20260521_summary.json`
- `data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_shape_top16_top13_top12_top08_smoke_20260521_summary.json`

该结果已经满足 main batch candidate（主线批量候选）规模。后续已进入正式 register 层，见下节。

## register 层合入：hconst compiler pair rule

已把 top16+top13+top12+top08 的 `hconst_match_collapse` exact hit set 合入正式 strategy registry（策略注册表）：

- strategy id：`true.proof.templatecheck.opnorm.hconst_match_collapse.top16_top13_top12_top08.v1`
- coverage kind：`compiler_pair_indexes`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_match_collapse_top16_top13_top12_top08_pair_indexes_20260521.txt`
- register cache summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_shape_top16_top13_top12_top08_register_pair_index_cache_20260521_summary.json`
- pair count / true union increment：`1,251,792`
- pair-index digest：`bc8de8f2a4077db4d550ec1dfb88760ffa3e737c62ec52ec0965bfea163d3eea`
- remote smoke：`20/20 accepted`
- focused tests：`tests/order5_strategy_registry/test_opnorm_match_collapse.py`、`tests/order5_strategy_registry/test_explicit_pairs_rule.py`、`tests/order5_strategy_registry/test_coverage_profile.py`，共 `31 passed`

正式 `coverage_summary.json` 复算结果：

- deterministic false covered：`2,369,350,082`
- deterministic true covered：`1,320,494,503`
- unresolved estimate：`225,848,615`
- conflict count：`0`

实现上新增 `CompilerPairIndexesRule`（编译器 pair-index 规则），manifest 记录 compiler family、shape bucket、pair-index cache digest 和 smoke evidence；certificate 仍由 `render_first_hconst_match_collapse_certificate` 按 pair 现场生成，不把 Lean proof body 或 proofbank known table 写入 registry。

## register 层合入：hconst-sandwich y-left targetbatch

在 `hconst_match_collapse` 主批之后，继续把 `hconst_sandwich_match_collapse` 从 top03 y-left core source family 扩展到 y-left repfilter targetbatch，并已合入正式 strategy registry：

- strategy id：`true.proof.templatecheck.opnorm.hconst_sandwich_match_collapse.yyleft_repfilter_targetbatch.v1`
- coverage kind：`compiler_pair_indexes`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_sandwich_yyleft_repfilter_targetbatch_pair_indexes_20260521.txt`
- register cache summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_sandwich_yyleft_repfilter_targetbatch_register_pair_index_cache_20260521_summary.json`
- pair count / candidate union increment：`263,371`
- pair-index digest：`73d95fcf11bc23740340b9b2aa462e9c1b257274eed810fd5f056c03fefc5a1a`
- source count：`23`
- target shape count：`10`
- remote smoke：`80/80 accepted`，其中首轮一个 transient `HTTP 502` 重试后 accepted
- focused tests：`tests/order5_strategy_registry/test_opnorm_match_collapse.py`、`tests/order5_strategy_registry/test_explicit_pairs_rule.py`、`tests/order5_strategy_registry/test_coverage_profile.py`，共 `35 passed`

正式 `coverage_summary.json` 最新复算结果：

- deterministic false covered：`2,369,376,273`
- deterministic true covered：`1,320,756,862`
- unresolved estimate：`225,560,065`
- conflict count：`0`

candidate summary 的 projection 是 against `current_coverage_profile_v6_20260521.json`，而当前工作区正式 register 同时包含其它本地策略变化；因此对外报告当前状态时以最新 `coverage_summary.json` 为准。

## register 层合入：hconst lm/rm mainline

继续复核同一 `hconst_match_collapse` compiler 在 lm1/rm1/d23 target 子族上的旧 mainline batch。由于旧 batch 使用 v5 coverage profile，本轮先构建当前 register 的 v7 coverage profile，再重算 union/conflict：

- v7 coverage profile：`data/processed/order5_strategy_registry/candidates/current_coverage_profile_v7_20260521.json`
- v7 delta summary：`data/processed/order5_strategy_registry/candidates/true_template_candidates_20260521_opnorm_hconst_mainline_batch_v7_delta_summary.json`
- strategy id：`true.proof.templatecheck.opnorm.hconst_match_collapse.lmrm_mainline.v1`
- coverage kind：`compiler_pair_indexes`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_lmrm_mainline_pair_indexes_20260521.txt`
- register cache summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_lmrm_mainline_register_pair_index_cache_20260521_summary.json`
- pair count：`1,112,800`
- same-true overlap：`2,345`
- current true union increment：`1,110,455`
- conflict increment：`0`
- remote smoke：`30/30 accepted`
- pair-index digest：`ec2ee2a64b3916652995abaf72714c2c4e0140c810c9a791cf815fdd9b1a6b76`

正式 `coverage_summary.json` 最新复算结果：

- deterministic false covered：`2,369,376,273`
- deterministic true covered：`1,321,867,317`
- unresolved estimate：`224,449,610`
- conflict count：`0`

focused tests：`tests/order5_strategy_registry/test_opnorm_match_collapse.py`、`tests/order5_strategy_registry/test_explicit_pairs_rule.py`、`tests/order5_strategy_registry/test_coverage_profile.py`，共 `37 passed`。

## v8 follow-up：hconst 剩余增量审计

`hconst_match_collapse.lmrm_mainline` 合入后，已构建 v8 coverage profile 并复核剩余 opnorm hconst/hconst-sandwich hit sets：

- v8 profile：`data/processed/order5_strategy_registry/candidates/current_coverage_profile_v8_20260521.json`
- audit summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_existing_hits_v8_audit_20260521_summary.json`
- audited hit file count：`59`
- positive hit file count：`12`
- 最大未合并正增量：`18,350`

继续扩扫 top01 var→mul 子族：

- combined hits：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_current_top01_source0000_0500_exact_combined_v8_20260521_hits.jsonl`
- combined summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_current_top01_source0000_0500_exact_combined_v8_20260521_summary.json`
- source offset：`0-500`
- current union increment：`73,400`
- conflict increment：`0`
- registry status：`parking_lot_below_100k_after_v8_audit`

两个高 residual bucket 的探针结果：

- `roots=var>mul|d=0>5|vc=3 -> roots=var>mul|d=0>4|vc=3`：hconst `0/20000`。
- `roots=mul>mul|d=1>4|vc=4 -> roots=mul>mul|d=2>3|vc=4`：hconst `0/20000`，hconst-sandwich `0/5000` 且耗时 `215.4s`。

因此当前剩余 top residual 不应继续无差别扩跑 hconst/hconst-sandwich；下一步应抽象 `plain_calc_match_collapse` / `nested_congrArg_match_collapse`，或寻找新的 source-level predicate。

低命中 bucket 暂不优先：

- `top_11`、`top_14` 均为 `0%`，且都是 `var>mul` 到 `var>mul` 形状。
- `top_19` 只有 `28.6%`，低于 tail，对 opnorm 迁移价值暂时有限。

## true follow-up：top01 var→mul 小 tail 合入 register

`roots=var>mul|d=0>4|vc=4|lm=0|rm=0|vs=0 -> roots=var>mul|d=0>4|vc=4|lm=0|rm=0|vs=0`
的 source offset `0..500` exact scan 在 v8 current profile 下得到：

- hits：`73,400`
- union increment：`73,400`
- conflict increment：`0`
- stratum：全部为 `order4_source_to_order4_target`
- hits：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_current_top01_source0000_0500_exact_combined_v8_20260521_hits.jsonl`
- candidate summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_current_top01_source0000_0500_exact_combined_v8_20260521_summary.json`

该候选低于默认 `100k` tail gate，但属于当前 top residual bucket 的可解释
true 子族。经用户确认后补做远程 judge smoke：

- smoke input：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_current_top01_source0000_0500_smoke_20260521_input.jsonl`
- smoke summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_current_top01_source0000_0500_smoke_20260521_summary.json`
- result：`30/30 accepted`
- backend：`http://10.220.69.172:8888`

正式 register 合入：

- strategy id：`true.proof.templatecheck.opnorm.hconst_match_collapse.varmul_top01_source0000_0500.v1`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_varmul_top01_source0000_0500_pair_indexes_20260521.txt`
- register summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_varmul_top01_source0000_0500_register_pair_index_cache_20260521_summary.json`
- pair-index SHA256：`004e08c239b4147a777eb31e871abd87c86985e047e68502b20003f6f5408e5a`

正式 `coverage_summary.json` 复算结果：

- strategy count：`273`
- deterministic false covered：`2,369,376,273`
- deterministic true covered：`1,321,940,717`
- unresolved estimate：`224,376,210`
- conflict count：`0`

## true follow-up：plain/nested seed 抽象为 hconst-default-sandwich

基于 top16 true seed cluster 的 `plain_calc_match_collapse` / `nested_congrArg_match_collapse`，
先验证现有慢 `hconst_sandwich` compiler 能覆盖 6 条 seed，但直接扫 seed source 时耗时过高。
随后新增两个快路径 compiler：

- `hconst-default-sandwich`：source 未约束变量使用 target 首变量默认填充，使用 hconst sandwich 闭合。
- `hstep-default-sandwich`：允许中间一步普通 `h` 子项重写，覆盖 `50837 -> 45406` 这类 seed。

验证链：

- focused tests：`tests/order5_strategy_registry/test_opnorm_match_collapse.py`
- seed smoke：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_default_sandwich_plain_nested_seed_smoke_20260521_summary.json`
- seed smoke result：`6/6 accepted`

分层扫描：

| 范围 | compiler | union increment | conflict | smoke |
| --- | --- | ---: | ---: | --- |
| 6 seed source | hconst-default + hstep-default combined | `2,788` | `0` | seed `6/6` |
| 48 RHS role-signature source | hconst-default + hstep-default combined | `22,658` | `0` | `24/24` |
| full top16 source shape | hconst-default | `269,662` | `0` | `71/71` |

full top16 candidate：

- source shape：`roots=mul>mul|d=1>4|vc=5|lm=0|rm=0|vs=0`
- target shape：`roots=mul>mul|d=1>4|vc=3|lm=0|rm=0|vs=0`
- source count：`888`
- hits：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_top16_fullshape_v8_20260521_hits.jsonl`
- summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_top16_fullshape_v8_20260521_summary.json`
- smoke summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_top16_fullshape_smoke_20260521_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_top16_fullshape_pair_indexes_20260521.txt`
- register summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_top16_fullshape_register_pair_index_cache_20260521_summary.json`
- pair-index SHA256：`c2a582a3af265c76b6271d1af8c0d83ec811b44ad1c5b0d37d2229e2cdd26f20`

正式 register 合入：

- strategy id：`true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.top16_fullshape.v1`
- strategy count：`274`
- deterministic false covered：`2,369,376,273`
- deterministic true covered：`1,322,210,379`
- unresolved estimate：`224,106,548`
- conflict count：`0`

## true follow-up：d14vc4 default-sandwich multitarget 合入 register

在 top16 default-sandwich 合入后，重新构建 current register 的 v9 coverage profile，并对最新 residual 做 shape sample：

- profile：`data/processed/order5_strategy_registry/candidates/current_coverage_profile_v9_20260521.json`
- profile timings：registry build `244.45s`，profile build `225.02s`，total `469.47s`
- true explicit pair count：`5,294,500`
- residual sample summary：`data/processed/order5_strategy_registry/current_residual_after_default_sandwich_shape_6000_seed20260521_summary.json`
- false-uncovered sample：`6,000`
- current residual sample：`804`
- true filter 后保留率：`13.4%`

top residual bucket 指向 `d1>4/vc4` source 到两个 `vc4` target shape，因此对 `hconst-default-sandwich` 做 v9 exact scan：

| source -> target shape | union increment | conflict |
| --- | ---: | ---: |
| `roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=2>3|vc=4|lm=0|rm=0|vs=0` | `1,453,600` | `0` |
| `roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0` | `1,452,810` | `0` |
| combined multitarget | `2,906,410` | `0` |

候选产物：

- combined hits：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d14vc4_multitarget_full_v9_20260521_hits.jsonl`
- combined summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d14vc4_multitarget_full_v9_20260521_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_d14vc4_multitarget_pair_indexes_20260521.txt`
- register summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d14vc4_multitarget_register_pair_index_cache_20260521_summary.json`
- pair-index SHA256：`37972488274a6e1d7a6a62584cdfb45d660266859162ccb13e0f07e53260aa03`
- remote smoke：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d14vc4_multitarget_smoke_20260521_summary.json`
- smoke result：`86/86 accepted`

正式 register 合入：

- strategy id：`true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.d14vc4_multitarget.v1`
- strategy count：`275`
- deterministic false covered：`2,369,376,273`
- deterministic true covered：`1,325,116,789`
- unresolved estimate：`221,200,138`
- conflict count：`0`
- coverage summary recompute：`.venv/bin/python scripts/data/summarize_order5_strategy_coverage.py`，用时 `7:13.84`
- regression tests：`.venv/bin/python -m pytest tests/order5_strategy_registry/test_opnorm_match_collapse.py tests/order5_strategy_registry/test_explicit_pairs_rule.py tests/order5_strategy_registry/test_coverage_profile.py -q`
- result：`47 passed`

## true follow-up：d13vc4 default-sandwich multitarget 合入 register

在 d14vc4 multitarget 合入后，重建 current register 的 v10 coverage profile，并重新抽样 residual shape：

- profile：`data/processed/order5_strategy_registry/candidates/current_coverage_profile_v10_20260521.json`
- profile timings：registry build `113.10s`，profile build `142.79s`，total `255.89s`
- true explicit pair count：`8,200,910`
- residual sample summary：`data/processed/order5_strategy_registry/current_residual_after_d14vc4_shape_6000_seed20260521_summary.json`
- false-uncovered sample：`6,000`
- current residual sample：`792`
- true filter 后保留率：`13.2%`

top residual bucket 中 `d1>3/vc4` source shape 与 default-sandwich compiler 高度匹配，因此对三个 target shape 做 v10 exact scan：

| source -> target shape | union increment | conflict |
| --- | ---: | ---: |
| `roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=2>3|vc=4|lm=0|rm=0|vs=0` | `1,278,040` | `0` |
| `roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0` | `1,085,757` | `0` |
| `roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0` | `1,278,384` | `0` |
| combined multitarget | `3,642,181` | `0` |

候选产物：

- combined hits：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d13vc4_multitarget_full_v10_20260521_hits.jsonl`
- combined summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d13vc4_multitarget_full_v10_20260521_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_d13vc4_multitarget_pair_indexes_20260521.txt`
- register summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d13vc4_multitarget_register_pair_index_cache_20260521_summary.json`
- pair-index SHA256：`21583dd58ba8ccfba6e4e1522cb8cee12ced5c8dac000e072ee861137b72325e`
- remote smoke：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d13vc4_multitarget_smoke_20260521_summary.json`
- smoke result：`90/90 accepted`

正式 register 合入：

- strategy id：`true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.d13vc4_multitarget.v1`
- strategy count：`276`
- deterministic false covered：`2,369,376,273`
- deterministic true covered：`1,328,758,970`
- unresolved estimate：`217,557,957`
- conflict count：`0`
- coverage summary recompute：`.venv/bin/python scripts/data/summarize_order5_strategy_coverage.py`，用时 `8:26.18`
- regression tests：`.venv/bin/python -m pytest tests/order5_strategy_registry/test_opnorm_match_collapse.py tests/order5_strategy_registry/test_explicit_pairs_rule.py tests/order5_strategy_registry/test_coverage_profile.py -q`
- result：`49 passed`

## true follow-up：d14vc4 target-extension 合入 register

在 d13vc4 multitarget 合入后，重建 current register 的 v11 coverage profile，并再次抽样 residual shape：

- profile：`data/processed/order5_strategy_registry/candidates/current_coverage_profile_v11_20260521.json`
- profile timings：registry build `112.42s`，profile build `137.33s`，total `249.74s`
- true explicit pair count：`11,843,091`
- residual sample summary：`data/processed/order5_strategy_registry/current_residual_after_d13vc4_shape_6000_seed20260521_summary.json`
- false-uncovered sample：`6,000`
- current residual sample：`778`
- true filter 后保留率：`12.97%`

top residual bucket 回到 `d1>4/vc4` source，但 target 转向 `vc3` 或 `d1>3/vc4`。沿用 `hconst-default-sandwich` compiler 做 v11 exact scan：

| source -> target shape | union increment | conflict |
| --- | ---: | ---: |
| `roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=2>3|vc=3|lm=0|rm=0|vs=0` | `815,280` | `0` |
| `roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>4|vc=3|lm=0|rm=0|vs=0` | `919,560` | `0` |
| `roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0` | `1,235,560` | `0` |
| `roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>3|vc=3|lm=1|rm=0|vs=0` | `133,985` | `0` |
| combined target-extension | `3,104,385` | `0` |

候选产物：

- combined hits：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d14vc4_targetext_full_v11_20260521_hits.jsonl`
- combined summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d14vc4_targetext_full_v11_20260521_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_d14vc4_targetext_pair_indexes_20260521.txt`
- register summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d14vc4_targetext_register_pair_index_cache_20260521_summary.json`
- pair-index SHA256：`5672b1773fd340e0a03b3276f200a01ba5f62aefc1581d8f833fa4a7c3430340`
- remote smoke：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_d14vc4_targetext_smoke_20260521_summary.json`
- smoke result：`100/100 accepted`

正式 register 合入：

- strategy id：`true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.d14vc4_targetext.v1`
- strategy count：`277`
- deterministic false covered：`2,369,376,273`
- deterministic true covered：`1,331,863,355`
- unresolved estimate：`214,453,572`
- conflict count：`0`
- coverage summary recompute：`.venv/bin/python scripts/data/summarize_order5_strategy_coverage.py`，用时 `9:42.41`
- regression tests：`.venv/bin/python -m pytest tests/order5_strategy_registry/test_opnorm_match_collapse.py tests/order5_strategy_registry/test_explicit_pairs_rule.py tests/order5_strategy_registry/test_coverage_profile.py -q`
- result：`51 passed`

## true follow-up：low-vc default-sandwich extension 合入 register

在 d14vc4 target-extension 合入后，重建 current register 的 v12 coverage profile，并再次抽样 residual shape：

- profile：`data/processed/order5_strategy_registry/candidates/current_coverage_profile_v12_20260521.json`
- profile timings：registry build `114.58s`，profile build `139.27s`，total `253.86s`
- true explicit pair count：`14,947,476`
- residual sample summary：`data/processed/order5_strategy_registry/current_residual_after_d14vc4_targetext_shape_6000_seed20260521_summary.json`
- false-uncovered sample：`6,000`
- current residual sample：`761`
- true filter 后保留率：`12.68%`

top residual bucket 中仍有 default-sandwich 可解释的相邻低变量数（low-vc）形状；对四个 source/target shape pair 做 v12 exact scan：

| source -> target shape | union increment | conflict |
| --- | ---: | ---: |
| `roots=mul>mul|d=1>4|vc=3|lm=0|rm=0|vs=0 -> roots=mul>mul|d=2>3|vc=4|lm=0|rm=0|vs=0` | `428,720` | `0` |
| `roots=mul>mul|d=1>4|vc=3|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0` | `428,720` | `0` |
| `roots=mul>mul|d=1>3|vc=3|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0` | `361,831` | `0` |
| `roots=mul>mul|d=1>3|vc=5|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>4|vc=3|lm=0|rm=0|vs=0` | `267,180` | `0` |
| combined low-vc extension | `1,486,451` | `0` |

候选产物：

- combined hits：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_lowvc_extension_full_v12_20260521_hits.jsonl`
- combined summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_lowvc_extension_full_v12_20260521_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_lowvc_extension_pair_indexes_20260521.txt`
- register summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_lowvc_extension_register_pair_index_cache_20260521_summary.json`
- pair-index SHA256：`8869fb145be04031067049c85f62af7c40ab0ccce9c34b2954701b2da535accb`
- remote smoke：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_lowvc_extension_smoke_20260521_summary.json`
- smoke result：`80/80 accepted`

正式 register 合入：

- strategy id：`true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.lowvc_extension.v1`
- strategy count：`278`
- deterministic false covered：`2,369,376,273`
- deterministic true covered：`1,333,349,806`
- unresolved estimate：`212,967,121`
- conflict count：`0`
- coverage summary recompute：`.venv/bin/python scripts/data/summarize_order5_strategy_coverage.py`，用时 `10:48.24`
- regression tests：`.venv/bin/python -m pytest tests/order5_strategy_registry/test_opnorm_match_collapse.py tests/order5_strategy_registry/test_explicit_pairs_rule.py tests/order5_strategy_registry/test_coverage_profile.py -q`
- result：`53 passed`

## false controller merge：all-smoked 包合入 register

总控复核 candidate 层已通过 smoke 的 false 确定性策略后，只保留一个在当前 union 口径仍有正增量且零 true overlap 的候选：

- strategy id：`false.finmodel.setcheck.current_residual_top20.order3_selector.enum_order3_766.all_equations.v1`
- source count：`1,545`
- target count：`61,031`
- raw coverage：`93,748,470`
- current union increment：`26,191`
- current true overlap：`0`
- priority：`604`
- remote smoke：`4/4 accepted`
- smoke summary：`data/processed/order5_strategy_registry/candidates/false_controller_current_all_smoked_selector_enum_order3_766_smoke_20260521_summary.json`
- merge artifact：`data/processed/order5_strategy_registry/candidates/false_controller_current_all_smoked_merge_selection_20260521.jsonl`
- register merge summary：`data/processed/order5_strategy_registry/candidates/false_controller_register_merge_current_all_smoked_20260521_summary.json`
- final audit：`data/processed/order5_strategy_registry/candidates/false_controller_current_all_smoked_merge_selection_final_audit_20260521_summary.json`

正式 `coverage_summary.json` 复算结果：

- strategy count：`274`
- deterministic false covered：`2,369,376,273`
- deterministic true covered：`1,322,210,379`
- unresolved estimate：`224,106,548`
- conflict count：`0`

后续 all-smoked final audit 在 `25k` controller gate 下 `selected_count=0`；candidate 层其余 false smoke/predicate 候选当前均为 parking lot，不继续合入 register。

## false follow-up：current residual finite-model broad probe

在 `hconst_match_collapse.lmrm_mainline` 合入后，按最新正式 coverage 重新采样 current residual，并把现有 false finite-model/table mutation 候选池做了一轮 broad selector probe（宽模型选择器探针）。

最新 coverage 口径：

- deterministic false covered：`2,369,376,273`
- deterministic true covered：`1,321,867,317`
- unresolved estimate：`224,449,610`
- conflict count：`0`

采样产物：

- summary：`data/processed/order5_strategy_registry/current_residual_after_lmrm_shape_15000_seed20260521_summary.json`
- residual sample：`data/processed/order5_strategy_registry/current_residual_after_lmrm_shape_15000_seed20260521_residual_sample.jsonl`
- false-uncovered sample：`15,000`
- current residual sample：`2,000`
- true filter 后保留率：`13.33%`

top current residual bucket 仍集中在 `mul>mul`：

- `roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0`：sample `29`，均匀外推约 `3,254,519`
- `roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=2>3|vc=4|lm=0|rm=0|vs=0`：sample `28`，均匀外推约 `3,142,295`
- `roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0`：sample `24`，均匀外推约 `2,693,395`

broad selector probe：

- summary：`data/processed/order5_strategy_registry/candidates/false_current_after_lmrm_sample2000_broad_selector_probe_20260521.json`
- hits：`data/processed/order5_strategy_registry/candidates/false_current_after_lmrm_sample2000_broad_selector_probe_20260521_hits.jsonl`
- residual pairs：`2,000`
- scanned finite models：`20,008`
- hit count：`4`
- hit rate：`0.20%`
- true-check sample：`4/4` checked，true conflict `0`

model-family compression（模型族压缩）：

- summary：`data/processed/order5_strategy_registry/candidates/false_current_after_lmrm_sample2000_broad_selector_family_20260521_summary.json`
- candidates：`15`
- best exact current false union increment：`21,616`
- best raw coverage：`279,363,650`
- best model family size：`3`
- `>=100k` candidate count：`0`
- `>=1m` candidate count：`0`
- status：`parking_lot_below_100k`

shape+model predicate ranking（形状加模型谓词排序）：

- summary：`data/processed/order5_strategy_registry/candidates/false_current_after_lmrm_sample2000_broad_shape_predicate_20260521_summary.json`
- candidates：`80`
- best exact union increment：`841`
- best raw coverage：`359,196`
- `>=100k` candidate count：`0`
- `>=1m` candidate count：`0`
- status：`parking_lot_below_100k`

结论：本轮 false finite-model broad probe 没有产生满足 tail gate（尾部门槛）`100k` 的候选，因此不进入 smoke，也不合入 register。opnorm false tables、order-3 mutation pool 和现有 structured finite-model pool 在最新 current residual 上呈现稀疏长尾，继续横向扩大同类模型池的 ROI 较低。下一步 false 侧优先转向新的 source-level predicate 或新的 compiler branch，而不是继续对同一 finite-model pool 做无差别扩扫。

## false follow-up：varmul top01 合入后的最新 residual probe

`true.proof.templatecheck.opnorm.hconst_match_collapse.varmul_top01_source0000_0500.v1` 进入 register 后，正式 coverage 又减少 `73,400` residual。本轮按最新 `coverage_summary.json` 重新采样并验证 false 侧候选：

最新 coverage 口径：

- deterministic false covered：`2,369,376,273`
- deterministic true covered：`1,321,940,717`
- unresolved estimate：`224,376,210`
- conflict count：`0`

刷新采样：

- summary：`data/processed/order5_strategy_registry/current_residual_after_varmul_top01_shape_30000_seed20260521_summary.json`
- residual sample：`data/processed/order5_strategy_registry/current_residual_after_varmul_top01_shape_30000_seed20260521_residual_sample.jsonl`
- false-uncovered sample：`30,000`
- current residual sample：`3,936`
- true filter 后保留率：`13.12%`

top residual bucket 仍然集中在 `mul>mul`，top1 为：

- `roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0`
- sample：`64`
- 均匀外推约：`3,648,394`

manifest + structured + residual-hit broad selector probe：

- summary：`data/processed/order5_strategy_registry/candidates/false_current_after_varmul_top01_sample3936_manifest_broad_selector_probe_20260521.json`
- hits：`data/processed/order5_strategy_registry/candidates/false_current_after_varmul_top01_sample3936_manifest_broad_selector_probe_20260521_hits.jsonl`
- residual pairs：`3,936`
- scanned finite models：`20,149`
- hit count：`14`
- hit rate：`0.3557%`
- true-check sample：`14/14` checked，true conflict `0`

model-family compression：

- summary：`data/processed/order5_strategy_registry/candidates/false_current_after_varmul_top01_sample3936_manifest_broad_selector_family_20260521_summary.json`
- candidates：`100`
- best exact current false union increment：`54,056`
- best raw coverage：`355,443,195`
- best model family size：`6`
- best sample hit count：`5`
- `>=100k` candidate count：`0`
- `>=1m` candidate count：`0`
- status：`parking_lot_below_100k`

shape+model predicate ranking：

- summary：`data/processed/order5_strategy_registry/candidates/false_current_after_varmul_top01_sample3936_manifest_shape_predicate_20260521_summary.json`
- candidates：`100`
- best exact union increment：`1,690`
- `>=100k` candidate count：`0`
- `>=1m` candidate count：`0`
- status：`parking_lot_below_100k`

bounded hit mutation probe：

- pool summary：`data/processed/order5_strategy_registry/candidates/false_current_after_varmul_top01_sample3936_hit_mutation_pool_20260521_summary.json`
- family summary：`data/processed/order5_strategy_registry/candidates/false_current_after_varmul_top01_sample3936_hit_mutation_family_20260521_summary.json`
- seed model count：`10`
- mutated model count：`1,098`
- output hit model count：`10`
- best full residual hit count：`3`
- best mutated-family exact current false union increment：`36,637`
- `>=100k` candidate count：`0`
- `>=1m` candidate count：`0`
- status：`parking_lot_below_100k`

结论：在 varmul top01 最新 register 口径下，false finite-model / predicatecheck 路线仍未产生可 smoke 的 tail candidate。`20,149` 个模型只命中 `14/3,936` residual，family best 仍低于 `100k`；mutation 没有突破 identity seed。该方向本轮不合并 register。下一步 false 侧若继续，应优先找非“固定有限模型池横向扩扫”的新结构，例如从 residual top `mul>mul` bucket 的 term skeleton（项骨架）反推可编译 countermodel family，或先抽取这些 bucket 中 rejected-by-opnorm 的 source/target term fragments，寻找新的 per-pair countermodel constructor。

## false follow-up：term skeleton countermodel probe

按上一节结论，本轮不再扩大固定 finite-model pool，而是从 latest current residual 的 term skeleton（项骨架）出发，寻找可能的 source/target skeleton predicate（源/目标项骨架谓词）和 countermodel constructor（反模型构造器）。

exact role-tree skeleton（精确变量角色树）过细：

- diagnostic：`data/processed/order5_strategy_registry/candidates/false_current_varmul_top01_term_skeleton_diagnostic_20260521_summary.json`
- residual sample：`3,936`
- `sample_count >= 3` 的 exact role-tree combo：`0`

因此改用 coarse skeleton（粗项骨架）：

- summary：`data/processed/order5_strategy_registry/candidates/false_current_varmul_top01_term_skeleton_coarse_diagnostic_20260521_summary.json`
- rows：`data/processed/order5_strategy_registry/candidates/false_current_varmul_top01_term_skeleton_coarse_diagnostic_20260521.jsonl`
- scored combo count：`300`
- candidate rows：`200`
- `current_false_union_increment_upper_bound >= 100k`：`199`
- zero current true overlap：`30`
- zero true overlap 且 upper bound `>=100k`：`29`

这些 rows 只是 diagnostic upper bound（诊断上界），不是 sound false candidate；没有 countermodel model table 或 constructor 前不能 smoke 或合并。

最强 zero-true-overlap skeleton upper bound：

- candidate key：`false.skeleton.countermodel_probe.coarse.shape_key.0085`
- source skeleton：`roots=var>mul|d=0>5|vc=4|lm=0|rm=1|vs=0`
- target skeleton：`roots=var>mul|d=0>4|vc=3|lm=0|rm=1|vs=0`
- sample hit count：`14/3,936`
- source count：`880`
- target count：`1,452`
- raw coverage upper bound：`1,277,760`
- current false union increment upper bound：`570,510`
- current true overlap：`0`
- status：`skeleton_candidate_needs_countermodel_constructor`

随后对 constructor 做 bounded Z3 试探：

- top `mul>mul` bucket order6 pair-specific probe：`data/processed/order5_strategy_registry/candidates/false_current_varmul_top01_top5_z3_order6_models_20260521_summary.json`
  - selected pair count：`10`
  - result：`unsat=4`、`unknown=6`、`sat=0`
- skeleton0085 sample：`data/processed/order5_strategy_registry/candidates/false_current_varmul_top01_skeleton0085_sample_pairs_20260521.jsonl`
  - sample count：`14`
- skeleton0085 order4 probe：`data/processed/order5_strategy_registry/candidates/false_current_varmul_top01_skeleton0085_z3_order4_models_20260521_summary.json`
  - selected pair count：`8`
  - result：`unsat=8`、`sat=0`
- skeleton0085 order5 probe：`data/processed/order5_strategy_registry/candidates/false_current_varmul_top01_skeleton0085_z3_order5_models_20260521_summary.json`
  - selected pair count：`6`
  - result：`unsat=5`、`unknown=1`、`sat=0`

结论：coarse skeleton 层确实存在 `100k-570k` 的 zero-true-overlap false 上界，说明“source/target skeleton predicate”值得保留为下一类方向；但低阶 order4/order5/order6 Z3 per-pair synthesis 没有找到可用 finite magma，因此当前还没有 sound countermodel constructor。本轮不 smoke、不合并 register。下一步若继续 false 侧，应尝试非低阶表枚举的 constructor，例如按 RHS endpoint role 设计专门代数、允许 exclusions 的 narrowed skeleton predicate，或从 opnorm false accepted tables 反推可参数化 family，而不是继续对低阶 Z3 做同样搜索。

补充验证两个 next-best RHS endpoint skeleton family：

- summary：`data/processed/order5_strategy_registry/candidates/false_current_varmul_top01_skeleton_constructor_followup_20260521_summary.json`
- `rhs_first_last_key.0099`：`lhs=LR|rhs_first_last=R:A -> lhs=LR|rhs_first_last=A:R`，old upper `517,824`；order4 `unsat=7, unknown=1`，order5 `unsat=3, unknown=2`，`sat=0`。
- `rhs_first_last_key.0045`：`lhs=LR|rhs_first_last=R:A -> lhs=LR|rhs_first_last=A:A`，old upper `517,807`；order4 `unsat=8`，order5 `unsat=2, unknown=3`，`sat=0`。
- controller decision：`do_not_smoke_do_not_merge`

## false follow-up：default-sandwich/d14 后 residual finite-model refresh

并行 true session 合入 `true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.d14vc4_multitarget.v1` 后，当前正式 registry 口径变为：

- strategy count：`275`
- deterministic false covered：`2,369,376,273`
- deterministic true covered：`1,325,116,789`
- unresolved estimate：`221,200,138`
- conflict count：`0`

刷新 current residual sample：

- summary：`data/processed/order5_strategy_registry/current_residual_after_default_sandwich_shape_30000_seed20260521_summary.json`
- false-uncovered sample：`30,000`
- current residual sample：`3,865`
- retained after true filter：`12.88%`
- note：这份样本使用当前 worktree true filter，包含 `d14vc4_multitarget`；summary 中的 sample projection 只作采样引导。

top current residual bucket 仍是 `mul>mul`：

- `roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0 -> roots=mul>mul|d=1>4|vc=3|lm=0|rm=0|vs=0`
- sample：`43/3,865`
- current unresolved 均匀外推约：`2,493,294`

finite-model broad selector refresh：

- small probe：`data/processed/order5_strategy_registry/candidates/false_current_after_default_sandwich_sample804_broad_selector_probe_20260521.json`
  - residual pairs：`804`
  - scanned models：`19,816`
  - hit count：`0`
- main probe：`data/processed/order5_strategy_registry/candidates/false_current_after_default_sandwich_sample3865_broad_selector_probe_20260521.json`
  - residual pairs：`3,865`
  - scanned models：`19,816`
  - hit count：`8`
  - hit rate：`0.207%`
  - hit strata：order4 source -> order5 target `1`，order5 source -> order5 target `7`
  - true-check sample：`0/8` conflict

model-family compression：

- summary：`data/processed/order5_strategy_registry/candidates/false_current_after_default_sandwich_sample3865_broad_selector_family_20260521_summary.json`
- model count：`8`
- candidate count：`40`
- best exact current false union increment：`36,325`
- best raw coverage：`193,787,823`
- best sample hit count：`3`
- `>=100k` candidate count：`0`
- `>=1m` candidate count：`0`
- status：`parking_lot_below_100k`

shape predicate ranking：

- model table file：`data/processed/order5_strategy_registry/candidates/false_current_after_default_sandwich_sample3865_hit_models_20260521_tables.txt`
- summary：`data/processed/order5_strategy_registry/candidates/false_current_after_default_sandwich_sample3865_shape_predicate_20260521_summary.json`
- candidate count：`80`
- best exact union increment：`829`
- `>=100k` candidate count：`0`
- `>=1m` candidate count：`0`
- status：`parking_lot_below_100k`

结论：在 default-sandwich/d14 最新 register 口径下，finite-model 横扫、model-family compression 和 shape-predicate narrowing 仍没有形成可 smoke 的 false deterministic candidate。该方向本轮不合并 register。下一步 false 侧继续转向 skeleton/constructor，不再扩大同一有限模型池。

## false follow-up：current skeleton upper-bound refresh

基于同一 `3,865` current residual sample，重算 coarse skeleton upper-bound（只作诊断，不是 sound candidate）：

- fast rows：`data/processed/order5_strategy_registry/candidates/false_current_after_default_sandwich_sample3865_skeleton_coarse_fast_20260521.jsonl`
- fast summary：`data/processed/order5_strategy_registry/candidates/false_current_after_default_sandwich_sample3865_skeleton_coarse_fast_20260521_summary.json`
- scored combo count：`200`
- `current_false_union_increment_upper_bound >= 100k`：`200`
- full true-overlap status：`not_checked_fast_skeleton_probe`

全量 true-overlap skeleton rescore 因当前 true registry mask 构建成本过高在本轮中止；因此这些 rows 只能作为 constructor target ranking，不能 smoke 或合并。

top fast upper-bound 是过宽的 RHS endpoint role：

- candidate：`false.skeleton.countermodel_probe.current_after_default_sandwich_fast.rhs_first_last_key.0004`
- source skeleton：`lhs=B|rhs_first_last=A:A`
- target skeleton：`lhs=B|rhs_first_last=A:A`
- sample hit count：`183/3,865`
- raw coverage upper bound：`559,276,326`
- current false union increment upper bound：`501,110,872`
- status：`skeleton_candidate_needs_countermodel_constructor`

较窄、仍有千万级上界的 shape/role-depth candidate：

- `shape_key.0102`：`roots=var>mul|d=0>4|vc=3|lm=0|rm=0|vs=0 -> roots=var>mul|d=0>4|vc=4|lm=0|rm=0|vs=0`
- sample hit count：`14/3,865`
- raw coverage upper bound：`16,199,360`
- current false union increment upper bound：`11,856,136`
- paired role-depth key：`rhs_first_last_depth_vc_key.0103`

结论：fresh skeleton 上界仍很大，说明 false residual 里还有结构性块；但没有 countermodel constructor 或 exact true-overlap 之前，它们不是确定性策略。下一步应优先对 `var>mul d0>4 vc3 -> var>mul d0>4 vc4` 这类较窄 shape 设计专门 constructor，或先做小范围 exact true-overlap/exclusion scan，而不是重复有限模型横扫。

### shape0102 constructor probe

对上节较窄 candidate 做 bounded constructor（有界反模型构造器）探针：

- candidate：`false.skeleton.countermodel_probe.current_after_default_sandwich.shape_key.0102`
- source skeleton：`roots=var>mul|d=0>4|vc=3|lm=0|rm=0|vs=0`
- target skeleton：`roots=var>mul|d=0>4|vc=4|lm=0|rm=0|vs=0`
- sample pairs：`data/processed/order5_strategy_registry/candidates/false_current_default_sandwich_shape0102_sample_pairs_20260521.jsonl`
- sample count：`14`
- raw coverage upper bound：`16,199,360`
- current false union increment upper bound：`11,856,136`
- aggregate summary：`data/processed/order5_strategy_registry/candidates/false_current_default_sandwich_shape0102_constructor_probe_20260521_summary.json`

Z3 finite magma synthesis（有限岩浆合成）结果：

| order | selected pairs | result | output |
| --- | ---: | --- | --- |
| 4 | `14` | `unsat=14` | `data/processed/order5_strategy_registry/candidates/false_current_default_sandwich_shape0102_z3_order4_models_20260521_summary.json` |
| 5 | `10` | `unsat=10` | `data/processed/order5_strategy_registry/candidates/false_current_default_sandwich_shape0102_z3_order5_models_20260521_summary.json` |
| 6 | `4` | `unsat=1, unknown=3` | `data/processed/order5_strategy_registry/candidates/false_current_default_sandwich_shape0102_z3_order6_models_20260521_summary.json` |

结论：该 narrow skeleton 仍只是 diagnostic upper bound；order4/order5 没有任何 finite magma witness，order6 小探针也没有 sat。当前没有可复用 constructor/model table，本轮不 smoke、不合并 register。下一步不要在这个 shape 上重复低阶有限表 Z3，除非先提出新的约束或非小有限代数构造；false 侧应切到另一个 narrow skeleton，或先补 exact true-overlap/exclusion evidence 再选 constructor target。

### shape0071 constructor probe

继续切到 `shape0102` 之后的 next-best narrow candidate：

- candidate：`false.skeleton.countermodel_probe.current_after_default_sandwich.shape_key.0071`
- source skeleton：`roots=var>mul|d=0>5|vc=3|lm=0|rm=0|vs=0`
- target skeleton：`roots=var>mul|d=0>4|vc=4|lm=0|rm=0|vs=0`
- sample pairs：`data/processed/order5_strategy_registry/candidates/false_current_default_sandwich_shape0071_sample_pairs_20260521.jsonl`
- sample count：`18`
- raw coverage upper bound：`11,605,248`
- current false union increment upper bound：`8,872,848`
- aggregate summary：`data/processed/order5_strategy_registry/candidates/false_current_default_sandwich_shape0071_constructor_probe_20260521_summary.json`

Z3 finite magma synthesis 结果：

| order | selected pairs | result | output |
| --- | ---: | --- | --- |
| 4 | `18` | `unsat=18` | `data/processed/order5_strategy_registry/candidates/false_current_default_sandwich_shape0071_z3_order4_models_20260521_summary.json` |
| 5 | `10` | `unsat=10` | `data/processed/order5_strategy_registry/candidates/false_current_default_sandwich_shape0071_z3_order5_models_20260521_summary.json` |
| 6 | `4` | `unsat=2, unknown=2` | `data/processed/order5_strategy_registry/candidates/false_current_default_sandwich_shape0071_z3_order6_models_20260521_summary.json` |

结论：`shape0071` 是 `shape0102` 的 source-depth-5 变体，sample hit 更高，但低阶 finite magma constructor 仍然失败。当前 `sat=0`、unique model `0`，没有可 smoke 的 certificate generator，也不合并 register。下一步不要继续在同一 `var>mul d0>5 vc3 -> var>mul d0>4 vc4` 形状上重复低阶 Z3；false 侧应转到独立的 `shape0089/shape0138`，或者先设计非有限小表的 endpoint-role constructor。

### shape0089 constructor probe

继续验证另一侧 depth-5 target 变体：

- candidate：`false.skeleton.countermodel_probe.current_after_default_sandwich.shape_key.0089`
- source skeleton：`roots=var>mul|d=0>4|vc=3|lm=0|rm=0|vs=0`
- target skeleton：`roots=var>mul|d=0>5|vc=4|lm=0|rm=0|vs=0`
- sample pairs：`data/processed/order5_strategy_registry/candidates/false_current_default_sandwich_shape0089_sample_pairs_20260521.jsonl`
- sample count：`15`
- raw coverage upper bound：`12,099,840`
- current false union increment upper bound：`8,861,440`
- aggregate summary：`data/processed/order5_strategy_registry/candidates/false_current_default_sandwich_shape0089_constructor_probe_20260521_summary.json`

Z3 finite magma synthesis 结果：

| order | selected pairs | result | output |
| --- | ---: | --- | --- |
| 4 | `15` | `unsat=15` | `data/processed/order5_strategy_registry/candidates/false_current_default_sandwich_shape0089_z3_order4_models_20260521_summary.json` |
| 5 | `10` | `unsat=10` | `data/processed/order5_strategy_registry/candidates/false_current_default_sandwich_shape0089_z3_order5_models_20260521_summary.json` |
| 6 | `4` | `unknown=4` | `data/processed/order5_strategy_registry/candidates/false_current_default_sandwich_shape0089_z3_order6_models_20260521_summary.json` |

结论：`shape0102/shape0071/shape0089` 三个 `var>mul vc3 -> var>mul vc4` 深度变体均未产出低阶 finite magma witness。`shape0089` 当前 `sat=0`、unique model `0`，不 smoke、不合并 register。下一步 false 侧不应继续机械重复同类 depth-variant Z3；更合理的是切到结构不同的 `shape0138` self-family，或先设计 endpoint role 的符号构造器。

### shape0138 constructor probe

转向结构不同的 self-family candidate：

- candidate：`false.skeleton.countermodel_probe.current_after_default_sandwich.shape_key.0138`
- source skeleton：`roots=var>mul|d=0>4|vc=3|lm=0|rm=0|vs=0`
- target skeleton：`roots=var>mul|d=0>4|vc=3|lm=0|rm=0|vs=0`
- sample pairs：`data/processed/order5_strategy_registry/candidates/false_current_default_sandwich_shape0138_sample_pairs_20260521.jsonl`
- sample count：`11`
- raw coverage upper bound：`10,672,600`
- current false union increment upper bound：`7,884,332`
- aggregate summary：`data/processed/order5_strategy_registry/candidates/false_current_default_sandwich_shape0138_constructor_probe_20260521_summary.json`

Z3 finite magma synthesis 结果：

| order | selected pairs | result | output |
| --- | ---: | --- | --- |
| 4 | `11` | `unsat=11` | `data/processed/order5_strategy_registry/candidates/false_current_default_sandwich_shape0138_z3_order4_models_20260521_summary.json` |
| 5 | `10` | `unsat=9, unknown=1` | `data/processed/order5_strategy_registry/candidates/false_current_default_sandwich_shape0138_z3_order5_models_20260521_summary.json` |
| 6 | `4` | `unknown=4` | `data/processed/order5_strategy_registry/candidates/false_current_default_sandwich_shape0138_z3_order6_models_20260521_summary.json` |

结论：`shape0138` self-family 也没有低阶 finite magma witness。当前 `sat=0`、unique model `0`，不 smoke、不合并 register。至此 top var/mul skeleton targets 均缺少 order4/order5/order6 小表反模型；false 侧应切到 `mul>mul` current residual top bucket，或先做非小有限代数 / endpoint-role symbolic constructor，而不是继续在 var/mul 上做同类 Z3。

### mulmul topbucket constructor probe

转向 current residual sample 中最高频的 `mul>mul` bucket：

- candidate：`false.skeleton.countermodel_probe.current_after_default_sandwich.mulmul_topbucket.shape_key.0029`
- source skeleton：`roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0`
- target skeleton：`roots=mul>mul|d=1>4|vc=3|lm=0|rm=0|vs=0`
- sample pairs：`data/processed/order5_strategy_registry/candidates/false_current_default_sandwich_mulmul_topbucket_sample_pairs_20260521.jsonl`
- sample count：`43`
- raw coverage upper bound：`2,149,120`
- current false union increment upper bound：`1,742,070`
- residual uniform estimate：`2,460,959`
- aggregate summary：`data/processed/order5_strategy_registry/candidates/false_current_default_sandwich_mulmul_topbucket_constructor_probe_20260521_summary.json`

Z3 finite magma synthesis 结果：

| order | selected pairs | result | output |
| --- | ---: | --- | --- |
| 4 | `20` | `unsat=20` | `data/processed/order5_strategy_registry/candidates/false_current_default_sandwich_mulmul_topbucket_z3_order4_models_20260521_summary.json` |
| 5 | `10` | `unsat=6, unknown=4` | `data/processed/order5_strategy_registry/candidates/false_current_default_sandwich_mulmul_topbucket_z3_order5_models_20260521_summary.json` |
| 6 | `4` | `unknown=4` | `data/processed/order5_strategy_registry/candidates/false_current_default_sandwich_mulmul_topbucket_z3_order6_models_20260521_summary.json` |

结论：`mul>mul` top bucket 虽然是当前 residual sample 的最高频形状，但 bounded order4/order5/order6 finite magma synthesis 仍没有 `sat`。当前无可复用 model table，不 smoke、不合并 register。到这里，低阶 pair-specific 小表 Z3 在 top var/mul skeleton 和 top mul/mul bucket 上都没有产出；下一步 false mining 应停止机械重复小表合成，改为从已 accepted 的 opnorm false tables 反推 shared predicate family，或设计非小有限代数 / endpoint-role symbolic constructor。

### 2026-05-22 true topbucket extension register 合并

low-vc extension 合入后重新采样 current residual：

- v13 profile：`data/processed/order5_strategy_registry/candidates/current_coverage_profile_v13_20260522.json`
- residual sample：`data/processed/order5_strategy_registry/current_residual_after_lowvc_extension_shape_6000_seed20260522_summary.json`
- false-uncovered sample：`6,000`
- retained residual after current true filter：`759`
- retained rate：`0.1265`

对 sample top residual 中同属 `hconst-default-sandwich` 的前三个 bucket 做 exact scan，并按同一 proof family 合并为 register batch：

| shape pair | exact union increment | conflict |
| --- | ---: | ---: |
| `d13/vc4 -> d14/vc3` | `475,084` | `0` |
| `d13/vc3 -> d14/vc4` | `425,040` | `0` |
| `d14/vc5 -> d14/vc4` | `875,696` | `0` |
| **combined** | **`1,775,820`** | **`0`** |

register 产物：

- strategy id：`true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.topbucket_extension.v1`
- register summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_topbucket_extension_register_pair_index_cache_20260522_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_topbucket_extension_pair_indexes_20260522.txt`
- pair-index SHA256：`7b9f7b15c6fe982f00c53be3bfae2e8a2916efd48ef1fb3159127c3dc79c816a`
- remote smoke：`80/80 accepted`
- smoke summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_topbucket_extension_smoke_20260522_summary.json`

full `coverage_summary()` 重算结果：

- strategy count：`279`
- deterministic false covered：`2,369,376,273`
- deterministic true covered：`1,335,125,626`
- unresolved estimate：`211,191,301`
- conflict count：`0`
- runtime：`10:57.11`

验证：

- focused opnorm tests：`35 passed`
- full `tests/order5_strategy_registry` regression：`84 passed`

### 2026-05-22 true frontier extension register 合并

topbucket extension 合入后重新采样 current residual：

- v14 profile：`data/processed/order5_strategy_registry/candidates/current_coverage_profile_v14_20260522.json`
- residual sample：`data/processed/order5_strategy_registry/current_residual_after_topbucket_extension_shape_6000_seed20260522_summary.json`
- false-uncovered sample：`6,000`
- retained residual after current true filter：`746`
- retained rate：`0.1243`

对 sample top residual 中同属 `hconst-default-sandwich` 的 frontier bucket 做 exact scan。按 register gate 只合并 `>=100k` 的五个 shape pair；`d14/vc4 -> d14/vc3_lm1rm1` 的 `80,076` 仍作为 parking lot。

| shape pair | exact union increment | conflict |
| --- | ---: | ---: |
| `d13/vc4 -> d23/vc3` | `716,044` | `0` |
| `d14/vc5 -> d13/vc4` | `747,592` | `0` |
| `d14/vc4 -> d13/vc3` | `837,400` | `0` |
| `d13/vc3 -> d14/vc3` | `269,808` | `0` |
| `d14/vc5 -> d14/vc5` | `423,986` | `0` |
| **combined** | **`2,994,830`** | **`0`** |

register 产物：

- strategy id：`true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.frontier_extension.v1`
- register summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_frontier_extension_register_pair_index_cache_20260522_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_frontier_extension_pair_indexes_20260522.txt`
- pair-index SHA256：`765a27b399dbd79aa35191043ad3c1318edf7a85793cbe1b0e529f6141214c3b`
- remote smoke：`90/90 accepted`
- smoke summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_frontier_extension_smoke_20260522_summary.json`

full `coverage_summary()` 重算结果：

- strategy count：`280`
- deterministic false covered：`2,369,376,273`
- deterministic true covered：`1,338,120,456`
- unresolved estimate：`208,196,471`
- conflict count：`0`
- runtime：`12:11.63`

验证：

- focused opnorm tests：`37 passed`
- full `tests/order5_strategy_registry` regression：`86 passed`

### 2026-05-22 true edge extension register 合并

frontier extension 合入后重新采样 current residual：

- v15 profile：`data/processed/order5_strategy_registry/candidates/current_coverage_profile_v15_20260522.json`
- residual sample：`data/processed/order5_strategy_registry/current_residual_after_frontier_extension_shape_6000_seed20260522_summary.json`
- false-uncovered sample：`6,000`
- retained residual after current true filter：`726`
- retained rate：`0.1210`

对 sample top residual 中仍可由 `hconst-default-sandwich` 解释的 edge bucket 做 exact scan。按 register gate 合并两个 shape pair；`d14/vc4 -> d14/vc3_lm1rm1` 和 `var/mul d04/vc3 -> d04/vc4` 两个小尾巴继续作为 parking lot。

| shape pair | exact union increment | conflict | decision |
| --- | ---: | ---: | --- |
| `d13/vc5 -> d14/vc4` | `704,996` | `0` | register |
| `d14/vc3 -> d13/vc4` | `364,412` | `0` | register |
| **combined register batch** | **`1,069,408`** | **`0`** | register |
| `d14/vc4 -> d14/vc3_lm1rm1` | `80,076` | `0` | parking lot below `100k` |
| `var/mul d04/vc3 -> d04/vc4` | `44,160` | `0` | parking lot below `100k` |

register 产物：

- strategy id：`true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.edge_extension.v1`
- register summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_edge_extension_register_pair_index_cache_20260522_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_edge_extension_pair_indexes_20260522.txt`
- pair-index SHA256：`9b8f0f03a25e121b30b221514ba039d975ed5d5930d2f7e8e719515e80d5f4d1`
- smoke summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_edge_extension_smoke_20260522_summary_retry.json`
- remote smoke：首轮 `79/80 accepted`，唯一失败为 transient `REMOTE_SIMPLE_API_REQUEST_FAILED`；retry 后 `80/80 accepted`

full `coverage_summary()` 重算结果：

- strategy count：`281`
- deterministic false covered：`2,369,376,273`
- deterministic true covered：`1,339,189,864`
- unresolved estimate：`207,127,063`
- conflict count：`0`
- runtime：`13:13.09`

验证：

- focused opnorm tests：`39 passed`

### 2026-05-22 总控 smoke 包合并复核

总控按最新 register 层重新复核至今 accepted 的 false predicate smoke pool：

- 输入 pool：`data/processed/order5_strategy_registry/candidates/false_controller_accepted_predicate_pool_from_smoke_20260521.jsonl`
- latest current rescore：`data/processed/order5_strategy_registry/candidates/false_controller_smoke_package_latest_current_rescore_20260522_summary.json`
- latest merge selection：`data/processed/order5_strategy_registry/candidates/false_controller_smoke_package_latest_current_merge_selection_20260522_summary.json`
- post-frontier current rescore：`data/processed/order5_strategy_registry/candidates/false_controller_smoke_package_post_frontier_current_rescore_20260522_summary.json`
- post-frontier merge selection：`data/processed/order5_strategy_registry/candidates/false_controller_smoke_package_post_frontier_current_merge_selection_20260522_summary.json`
- register merge audit：`data/processed/order5_strategy_registry/candidates/false_controller_register_merge_smoke_package_post_frontier_current_20260522_summary.json`
- current register 覆盖快照：false `2,369,376,273`，true `1,338,120,456`，unresolved `208,196,471`，conflict `0`

rescore 结果：

| 指标 | 数值 |
| --- | ---: |
| accepted smoke candidate | `15` |
| positive current increment | `4` |
| best current increment | `9,975` |
| `>=100k` | `0` |
| `>=1M` | `0` |

带 current true-overlap 的 greedy selection 结果：

| 指标 | 数值 |
| --- | ---: |
| input candidate | `15` |
| zero true-overlap candidate | `15` |
| min marginal increment | `25,000` |
| selected for register merge | `0` |
| cumulative increment | `0` |

结论：这个 smoke 包里此前合适的 false 策略已经被 register 层吸收；在最新 post-frontier true/false register 下剩余 accepted smoke candidates 的 exact union increment 全部低于 `25k`，不再合并到 `discovered_predicatecheck_bank.jsonl`。本次只生成复核产物并重算 `coverage_summary.json`，正式 register 覆盖保持 false `2,369,376,273`、true `1,338,120,456`、unresolved `208,196,471`、conflict `0`。

验证：

- registry summary：`PYTHONPATH=src .venv/bin/python scripts/data/summarize_order5_strategy_coverage.py --reuse-true-from-output --update-source-target-cache` 通过，conflict `0`
- focused false registry tests：`31 passed in 204.69s`

同时复核 latest residual false model-family mining：

- residual resample：`data/processed/order5_strategy_registry/current_residual_latest_false_mining_shape_20000_seed20260522_summary.json`
- model-family search：`data/processed/order5_strategy_registry/candidates/false_predicate_model_family_latest_residual_20260522_summary.json`
- truecheck selection：`data/processed/order5_strategy_registry/candidates/false_predicate_model_family_latest_residual_min25k_truecheck_20260522_summary.json`
- 20k false-uncovered sample 经 current true filter 后保留 `2,500` residual，保留率 `0.125`
- 搜索 `199` 个模型、`1,217` 个 beam families，best exact current false union increment `39,618`，`>=100k`/`>=1M` 均为 `0`
- truecheck selection 在最新 true register 下仍选出 `1` 个 `39,618` tail seed，true overlap `0`

结论：`39,618` 仍低于 tail merge gate，且尚未 remote smoke；按 registry 规则标记为 `parking_lot_below_100k_no_smoke_no_register_merge`。下一步 false 侧不再把低阶小表 Z3 作为主线，应转向非小有限代数 / endpoint-role symbolic constructor，或为当前新的 `mul>mul` residual buckets 设计 fresh model generator。

### 2026-05-22 latest current false mining：topbucket extension 后复采样与 finite-model 负结果

在 true `topbucket_extension` 合入后，重新基于 latest current register 做 false-uncovered residual sample：

- summary：`data/processed/order5_strategy_registry/current_residual_after_topbucket_extension_false_mining_shape_12000_seed20260522_summary.json`
- residual sample：`data/processed/order5_strategy_registry/current_residual_after_topbucket_extension_false_mining_shape_12000_seed20260522_residual_sample.jsonl`
- false-uncovered sample：`12,000`
- current residual after true filter：`1,457`
- retained rate：`0.1214`
- coverage used：false `2,369,376,273`，true `1,335,125,626`，unresolved `211,191,301`，conflict `0`

top residual buckets 仍主要是 `mul>mul`：

| bucket | sample count | uniform residual estimate |
| --- | ---: | ---: |
| `d1>4/vc4 -> d1>3/vc3` | `14` | `2,029,292` |
| `d1>3/vc4 -> d2>3/vc3` | `10` | `1,449,494` |
| `d1>4/vc5 -> d1>3/vc4` | `10` | `1,449,494` |
| `var>mul d0>4/vc3 -> var>mul d0>4/vc4` | `10` | `1,449,494` |
| `d1>3/vc3 -> d1>4/vc3` | `10` | `1,449,494` |

#### fresh model generator：accepted false/opnorm/structured seed mutation

对 accepted false/opnorm/structured 表做 bounded mutation，目标是 latest top residual buckets：

- output：`data/processed/order5_strategy_registry/candidates/false_after_topbucket_extension_mutated_model_pool_20260522.jsonl`
- summary：`data/processed/order5_strategy_registry/candidates/false_after_topbucket_extension_mutated_model_pool_20260522_summary.json`
- seed models：`65`
- mutated/random models：`10,455`
- selected top-bucket pairs：`120`
- selected-hit model count：`0`
- full residual hit model count：`0`

结论：当前 top `mul>mul` residual 对既有 accepted false 表的单元格局部变异不敏感；没有可进入 predicate-family exact scoring 的新模型。

#### fresh model generator：non-small random order6/order7

为测试“非小有限代数”方向，给 `scripts/data/mutate_order5_residual_model_pool.py` 增加了 bounded random `order5/order6/order7` 参数，只用于 candidate-layer 探索。

两轮随机表 probe：

| scope | output | random models | hit model count |
| --- | --- | ---: | ---: |
| top 12 residual buckets | `data/processed/order5_strategy_registry/candidates/false_after_topbucket_extension_random_order6_7_model_pool_20260522_summary.json` | `4,000` | `0` |
| all `1,457` residual sample | `data/processed/order5_strategy_registry/candidates/false_after_topbucket_extension_random_order6_7_allresidual_model_pool_20260522_summary.json` | `4,000` | `0` |

结论：随机 order6/order7 有限表不是当前 residual 的有效入口；source 方程在随机表上几乎不成立，不能形成 usable false predicate seed。

#### latest residual model-family search

用已有高价值模型池在 latest residual sample 上重新做 beam family exact scoring：

- output：`data/processed/order5_strategy_registry/candidates/false_predicate_model_family_after_topbucket_extension_20260522.jsonl`
- summary：`data/processed/order5_strategy_registry/candidates/false_predicate_model_family_after_topbucket_extension_20260522_summary.json`
- model count：`231`
- beam family count：`1,614`
- exact scored：`614`
- best exact current false union increment：`42,235`
- `>=100k`：`0`
- `>=1M`：`0`

带 current true-overlap 的 greedy selection：

- output：`data/processed/order5_strategy_registry/candidates/false_predicate_model_family_after_topbucket_extension_min25k_truecheck_20260522.jsonl`
- summary：`data/processed/order5_strategy_registry/candidates/false_predicate_model_family_after_topbucket_extension_min25k_truecheck_20260522_summary.json`
- input candidates：`160`
- zero true-overlap candidates：`160`
- selected count：`2`
- cumulative exact current false union increment：`67,742`
- best selected candidate：`42,235`

这两个 selected tail seeds 的 true overlap 都是 `0`，但累计仍低于 `100k` tail merge gate；不 remote smoke、不合并 register，保留在 candidate parking lot。

#### shape predicate probe

单模型 + source/target shape predicate 压缩也没有形成可用块：

- output：`data/processed/order5_strategy_registry/candidates/false_shape_predicate_after_topbucket_extension_mixed_opnorm_20260522.jsonl`
- summary：`data/processed/order5_strategy_registry/candidates/false_shape_predicate_after_topbucket_extension_mixed_opnorm_20260522_summary.json`
- model count：`18`
- source shapes：`24`
- target shapes：`24`
- best exact union increment：`1,690`
- `>=100k`：`0`

结论：latest residual 的 false side 继续表现为 hard tail。现有 finite-model source/target predicate family、accepted-table mutation、随机 order6/order7 表、单模型 shape predicate 都不能达到 tail merge gate。下一步应停止扩大随机有限表 probe，转向 endpoint-role symbolic constructor：围绕 `mul>mul d1>4/vc4 or vc5 -> d1>3/d2>3` 的变量端点角色、重复变量位置和子项投影关系，先构造可证明 refuting witness family，再回填 finite/semantic certificate。

### 2026-05-22 false 总控：to-date predicate smoke 包合入 register

在 post-frontier true register 继续推进后，总控重新审计至今 candidate 层 false predicate family：

- merged pool：`data/processed/order5_strategy_registry/candidates/false_controller_to_date_predicate_family_ge25k_pool_20260522.jsonl`
- selection：`data/processed/order5_strategy_registry/candidates/false_controller_to_date_predicate_family_current_merge_selection_20260522.jsonl`
- selection summary：`data/processed/order5_strategy_registry/candidates/false_controller_to_date_predicate_family_current_merge_selection_20260522_summary.json`
- remote smoke input：`data/processed/order5_strategy_registry/candidates/false_controller_to_date_predicate_family_current_merge_smoke_20260522_input.jsonl`
- remote smoke summary：`data/processed/order5_strategy_registry/candidates/false_controller_to_date_predicate_family_current_merge_smoke_20260522_summary.json`

最新 current selection 只保留 `1` 个合适候选：

| 指标 | 数值 |
| --- | ---: |
| strategy key | `false.finmodel.predicatecheck.model_family.beam_after_k40.post_frontier_z3.batch01` |
| source count | `3,490` |
| target count | `59,086` |
| raw coverage | `205,023,972` |
| exact current false union increment | `59,038` |
| current true overlap | `0` |
| model family size | `4` |
| remote smoke | `4/4 accepted` |

该策略来自 post-frontier Z3 seed + opnorm/ETP mutated family：

- `z3_topbucket_order4_pair3_49148_52807`
- `opnorm_09.0123/0200/0030/0001`
- `etp_refutation492__identity__mut_r0c2v1`
- `etp_refutation442__mut_r0c1v0__rand0007`

总控已追加到 `data/processed/order5_strategy_registry/discovered_predicatecheck_bank.jsonl`，作为第 `13` 个 active predicatecheck bank row，`priority_start=620`。随后重算 register summary：

| 指标 | 合并后 |
| --- | ---: |
| deterministic false covered | `2,369,435,311` |
| deterministic true covered | `1,339,189,864` |
| unresolved estimate | `207,068,025` |
| conflict count | `0` |

验证：

- registry summary：`PYTHONPATH=src .venv/bin/python scripts/data/summarize_order5_strategy_coverage.py --reuse-true-from-output --update-source-target-cache`，conflict `0`
- remote smoke：`PYTHONPATH=src .venv/bin/python scripts/lean_certificates/verify_order5_paircheck_remote_smoke.py ... --base-urls http://10.220.69.172:8888,http://10.220.69.153:8888 --max-workers 4`，`4/4 accepted`
- focused tests：`PYTHONPATH=src .venv/bin/python -m pytest tests/order5_strategy_registry/test_model_family_predicatecheck.py tests/order5_strategy_registry/test_structured_setcheck_strategy.py tests/order5_strategy_registry/test_explicit_pairs_rule.py -q`，`33 passed`

结论：本次总控合并将 candidate 层当前唯一满足 `>=25k` tail gate、零 true overlap、remote smoke 通过的 false predicate family 合入 register；其余 post-frontier endpoint/shape/random finite-table 候选仍低于合并门槛，继续保留在 parking lot。

### 2026-05-22 false hard-tail 续挖：post-frontier predicate merge 后的 Z3 与 endpoint-role 复核

在 `false.finmodel.predicatecheck.model_family.beam_after_k40.post_frontier_z3.batch01`
合入 register 后，基于最新 residual sample 继续做 false 侧 bounded finite-model
seed 与 predicate family 复核：

- residual sample：`data/processed/order5_strategy_registry/current_residual_after_false_post_frontier_z3_merge_shape_12000_seed20260522b_residual_sample.jsonl`
- summary：`data/processed/order5_strategy_registry/current_residual_after_false_post_frontier_z3_merge_shape_12000_seed20260522b_summary.json`
- coverage used：false `2,369,435,311`，true `1,339,189,864`，unresolved `207,068,025`，conflict `0`
- false-uncovered sample：`12,000`
- current residual after true filter：`1,457`
- retained rate：`0.1214`

#### bounded Z3 seed synthesis

| run | output | selected pair | sat model | status |
| --- | --- | ---: | ---: | --- |
| order4 top6 buckets | `data/processed/order5_strategy_registry/candidates/false_after_post_frontier_z3_merge_top6_z3_order4_models_20260522_summary.json` | `36` | `0` | `26` unsat, `10` unknown |
| order5 top4 buckets | `data/processed/order5_strategy_registry/candidates/false_after_post_frontier_z3_merge_top4_z3_order5_models_20260522_summary.json` | `12` | `0` | `3` unsat, `9` unknown |

结论：latest hard-tail 的 top `mul>mul` residual bucket 在小范围 order4/order5
Z3 上没有产生新的 finite-model seed；继续盲目扩大 Z3 pair 数或 timeout 的 ROI
不高。

#### model-family predicatecheck 重排

用已有高价值模型池重新在 post-merge residual 上做 beam family exact scoring：

- output：`data/processed/order5_strategy_registry/candidates/false_predicate_model_family_after_false_post_frontier_z3_merge_20260522.jsonl`
- summary：`data/processed/order5_strategy_registry/candidates/false_predicate_model_family_after_false_post_frontier_z3_merge_20260522_summary.json`
- model count：`200`
- beam family count：`1,659`
- exact scored：`200`
- best exact current false union increment：`13,870`
- `>=100k`：`0`
- `>=1M`：`0`

结论：post-frontier Z3 batch 合入后，旧 Z3/opnorm/ETP mutated/structured
模型池的剩余边际已经降到 `25k` smoke gate 以下；本轮不 remote smoke、
不合并 register。

#### endpoint-role predicate 压缩

在同一 latest residual sample 上重新跑端点角色谓词：

| mode | output | best exact union increment | `>=100k` |
| --- | --- | ---: | ---: |
| endpoint1 | `data/processed/order5_strategy_registry/candidates/false_endpoint_role_endpoint1_after_false_post_frontier_z3_merge_20260522_summary.json` | `935` | `0` |
| endpoint2 | `data/processed/order5_strategy_registry/candidates/false_endpoint_role_endpoint2_after_false_post_frontier_z3_merge_20260522_summary.json` | `121` | `0` |

结论：简单 endpoint-role finite-model predicate 在最新 register 下只剩极小
parking-lot tail。下一步 false 侧不应继续扩大现有 endpoint1/endpoint2
签名网格；应转向更强的 symbolic constructor，例如围绕 top `mul>mul`
bucket 的重复变量位置、子项包含关系、projection/absorbing witness family
构造新的可验证反例族，再回填 finite/semantic certificate。

### 2026-05-22 false 总控：to-date candidate register merge audit

总控按“只合并证据完整候选”的口径重新审计 candidate 层 false deterministic
策略：`post_frontier_z3.batch01` smoke 包已在上一轮正式进入 register，
本轮没有额外 append。

- audit summary：`data/processed/order5_strategy_registry/candidates/false_controller_to_date_register_merge_audit_20260522_summary.json`
- registered strategy key：`false.finmodel.predicatecheck.model_family.beam_after_k40.post_frontier_z3.batch01`
- register bank：`data/processed/order5_strategy_registry/discovered_predicatecheck_bank.jsonl`
- bank row：`13`
- manifest rows：`4` 个 witness shard，priority `620` 到 `623`
- exact current false union increment：`59,038`
- true overlap：`0`
- remote smoke：`4/4 accepted`

重算 register 后的当前口径：

| 指标 | 数值 |
| --- | ---: |
| deterministic false covered | `2,369,435,311` |
| deterministic true covered | `1,339,189,864` |
| unresolved estimate | `207,068,025` |
| conflict count | `0` |
| strategies manifest rows | `285` |
| false strategy rows | `250` |

candidate 层截至本次审计：

- `false_controller_to_date_predicate_family_min25k_union_latest_post_edge_recheck_20260522_summary.json`
  对已 smoked predicate family 重算后 selected `0`、cumulative increment `0`，
  没有新的 predicatecheck 可合并项。
- `false_affine_mod_after_false_post_frontier_z3_merge_mod12_19_20260522_summary.json`
  找到 mod17 affine setcheck tail 候选，best exact current false union
  increment `499,148`，`>=100k` 候选 `80`；但这些候选还没有
  current true-overlap 精算和 remote official judge smoke，不能作为
  register 层确定策略合并。

验证：

- `PYTHONPATH=src .venv/bin/python scripts/data/summarize_order5_strategy_coverage.py --reuse-true-from-output --update-source-target-cache`
  通过，conflict `0`
- `PYTHONPATH=src .venv/bin/python -m pytest tests/order5_strategy_registry/test_model_family_predicatecheck.py tests/order5_strategy_registry/test_structured_setcheck_strategy.py tests/order5_strategy_registry/test_explicit_pairs_rule.py -q`
  通过，`33 passed in 195.05s`

### 2026-05-22 true post-edge top40 extension register 合并

在 edge extension 与 post-frontier false predicate batch 合入后，按当前 register 口径重新采样 residual：

- sample summary：`data/processed/order5_strategy_registry/current_residual_after_edge_extension_shape_6000_seed20260522_summary.json`
- residual buckets：`data/processed/order5_strategy_registry/current_residual_after_edge_extension_shape_6000_seed20260522_residual_buckets.json`
- false-uncovered sample：`6,000`
- current residual after true filter：`716`
- retained rate：`0.1193`
- coverage used：false `2,369,435,311`，true `1,339,189,864`，unresolved `207,068,025`，conflict `0`

构建 current coverage profile v16：

- profile：`data/processed/order5_strategy_registry/candidates/current_coverage_profile_v16_20260522.json`
- true explicit pair count：`22,273,985`
- true source-target group count：`122`
- timings：registry build `120.18s`，profile build `143.36s`，total `263.54s`

对 post-edge residual top40 shape bucket 跑 `hconst-default-sandwich` exact scan。23 个 shape pair 命中，合并后满足 main register gate：

| 指标 | 数值 |
| --- | ---: |
| positive shape pair count | `23` |
| combined exact true union increment | `5,503,838` |
| conflict increment | `0` |
| remote smoke | `120/120 accepted` |
| pair-index SHA256 | `f3beea2cb85741cb0ce1018d3d37449376f3b42bc7d8efb6b3ef8b2df329f1da` |

最大几个 shape pair：

| rank | shape pair | exact union increment |
| ---: | --- | ---: |
| 26 | `d13/vc5 -> d23/vc4` | `705,456` |
| 13 | `d14/vc4 -> d23/vc5` | `701,520` |
| 30 | `d13/vc4 -> d14/vc5` | `617,108` |
| 9 | `d14/vc4 -> d13/vc5` | `567,220` |
| 14 | `d13/vc4 -> d13/vc3_rm1` | `287,732` |

`hstep-default-sandwich` 只完成 top01/top02 小探针；top02 union `81,040`，top03 full scan 超过两分半仍未完成，说明该 compiler 需要更强 prefilter，当前不作为 register batch 主线。

register 产物：

- strategy id：`true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.postedge_top40_extension.v1`
- combined hits：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge_top40_extension_full_v16_20260522_hits.jsonl`
- candidate summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge_top40_extension_full_v16_20260522_summary.json`
- register summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge_top40_extension_register_pair_index_cache_20260522_summary.json`
- smoke summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge_top40_extension_smoke_20260522_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_postedge_top40_extension_pair_indexes_20260522.txt`

full `coverage_summary()` 重算结果：

| 指标 | 数值 |
| --- | ---: |
| deterministic false covered | `2,369,435,311` |
| deterministic true covered | `1,344,693,702` |
| unresolved estimate | `201,564,187` |
| conflict count | `0` |
| strategy count | `286` |
| runtime | `16:35.67` |

验证：

- focused opnorm tests：`41 passed`
- full `tests/order5_strategy_registry` regression：`92 passed`

### 2026-05-22 false 总控：mod17 affine setcheck register gate 复核

在 post-edge true extension 合入后的最新 register 口径下，继续复核
candidate 层的 mod17 affine finite-model setcheck（有限模型集合检查）
候选。该方向的 coverage gate 通过，但 official smoke 仍未形成完整证据，
因此不合并 register。

- truecheck selection：`data/processed/order5_strategy_registry/candidates/false_affine_mod_after_false_post_frontier_z3_merge_mod12_19_truecheck_selection_20260522.jsonl`
- truecheck summary：`data/processed/order5_strategy_registry/candidates/false_affine_mod_after_false_post_frontier_z3_merge_mod12_19_truecheck_selection_20260522_summary.json`
- initial smoke summary：`data/processed/order5_strategy_registry/candidates/false_affine_mod17_truecheck_batch_smoke_20260522_summary.json`
- light alternate smoke summary：`data/processed/order5_strategy_registry/candidates/false_affine_mod17_top1_light_alt_smoke_top2_20260522_summary.json`
- gate audit：`data/processed/order5_strategy_registry/candidates/false_affine_mod17_register_gate_audit_20260522_summary.json`

筛选结果：

| 指标 | 数值 |
| --- | ---: |
| selected mod17 affine candidates | `7` |
| selected candidates true overlap | `0` |
| cumulative current false union increment | `3,071,381` |
| top candidate | `mod17 a7 b11 c0` |
| top candidate current false union increment | `499,148` |

remote official judge smoke：

| smoke | accepted | total | 结论 |
| --- | ---: | ---: | --- |
| initial representative batch | `8` | `23` | `15` 个 order5-source tier timeout |
| top1 light alternates | `0` | `4` | `1` rejected，`3` 个 run-id collision error |

light alternate 的 4 个代表 pair 均已用 Python `FiniteMagma` brute force
复核为 source 在 Fin17 表中成立、target 在 Fin17 表中不成立；但官方 judge
对至少一个 order5-source direct-match certificate 在约 `301s` 后返回 rejected，
其余短 prefix 重跑超过十分钟仍无本地结果。因此当前问题不是 coverage
或 true-overlap，而是 Fin17 direct-match certificate path 对 order5-source
representative 不稳定。

为后续合并做了一个 register builder 支撑改动：`discovered_setcheck_bank.jsonl`
如果出现带 `modulus/a/b/c` 或 `affine_*` 字段的 setcheck row，会走
symbolic affine source-set construction（符号 affine source 集构造），避免
对 17 阶显式 magma 做全量扫描。该支撑已用 focused test 固定；但本次没有
新增任何 active setcheck bank row。

当前 gate 结论：

- `mod17 affine` 批次：`parking_lot_certificate_path_blocked_no_register_merge`
- register summary 保持：false `2,369,435,311`，true `1,344,693,702`，
  unresolved `201,564,187`，conflict `0`

### 2026-05-22 true postedge2 top60 extension register 合并

`mod17 affine` 没有合入 register 后，当前 true 侧 register 口径仍停在
post-edge top40 extension。继续对该 residual 做 stratified sample，并用
v17 coverage profile 精算 `hconst-default-sandwich` compiler 的 top60 shape
候选；其中 23 个 shape pair 通过 exact union/conflict gate，合并为
`postedge2_top60_extension` register batch。

当前 residual sample：

- sample summary：`data/processed/order5_strategy_registry/current_residual_after_postedge_top40_extension_shape_8000_seed20260522_summary.json`
- residual buckets：`data/processed/order5_strategy_registry/current_residual_after_postedge_top40_extension_shape_8000_seed20260522_residual_buckets.json`
- false-uncovered sample：`8,000`
- current residual after true filter：`923`
- retained rate：`0.115375`
- coverage used：false `2,369,435,311`，true `1,344,693,702`，unresolved `201,564,187`，conflict `0`

构建 current coverage profile v17：

- profile：`data/processed/order5_strategy_registry/candidates/current_coverage_profile_v17_20260522.json`
- true explicit pair count：`27,777,823`
- true source-target group count：`122`
- false group count：`10,122`
- timings：registry build `122.61s`，profile build `149.17s`，total `271.79s`

top60 exact scan 合并结果：

| 指标 | 数值 |
| --- | ---: |
| positive shape pair count | `23` |
| combined exact true union increment | `6,295,929` |
| conflict increment | `0` |
| remote smoke | `120/120 accepted` |
| pair-index SHA256 | `67f0a2c68e86d1968b781e1456b61fc756892195a555bd186ea39b0aa8f247ae` |

最大几个 shape pair：

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

register 产物：

- strategy id：`true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.postedge2_top60_extension.v1`
- combined hits：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge2_top60_extension_full_v17_20260522_hits.jsonl`
- candidate summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge2_top60_extension_full_v17_20260522_summary.json`
- register summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge2_top60_extension_register_pair_index_cache_20260522_summary.json`
- smoke summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge2_top60_extension_smoke_20260522_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_postedge2_top60_extension_pair_indexes_20260522.txt`

full `coverage_summary()` 重算结果：

| 指标 | 数值 |
| --- | ---: |
| deterministic false covered | `2,369,435,311` |
| deterministic true covered | `1,350,989,631` |
| unresolved estimate | `195,268,258` |
| conflict count | `0` |
| strategy count | `287` |
| runtime | `18:08.88` |

验证：

- remote smoke：`120/120 accepted`
- focused opnorm tests：`43 passed`
- full `tests/order5_strategy_registry` regression：`95 passed in 501.57s`

### 2026-05-22 false 总控：to-date smoke package register 复核

在 `postedge2_top60_extension` 合入 true register 后，重新按最新 current
register 口径复核至今 candidate 层的 false deterministic smoke 包。本轮总控
只允许满足以下条件的候选进入 register：

- representative remote official judge smoke 全部 accepted；
- current true overlap 为 `0`；
- current false union marginal increment 达到尾部合并门槛 `25,000`；
- 合并后 `conflict_count` 保持 `0`。

复核产物：

- accepted predicate pool：`data/processed/order5_strategy_registry/candidates/false_controller_to_date_accepted_predicate_smoke_pool_20260522.jsonl`
- current rescore summary：`data/processed/order5_strategy_registry/candidates/false_controller_to_date_accepted_predicate_current_rescore_20260522_summary.json`
- merge selection summary：`data/processed/order5_strategy_registry/candidates/false_controller_to_date_accepted_predicate_current_merge_selection_20260522_summary.json`
- 总控 audit summary：`data/processed/order5_strategy_registry/candidates/false_controller_to_date_after_postedge2_register_merge_audit_20260522_summary.json`

结论：

| 项目 | 结果 |
| --- | ---: |
| accepted model-family predicate candidates | `16` |
| current positive remaining candidates | `4` |
| best remaining current false union increment | `8,920` |
| candidates with increment >= 100k | `0` |
| selected for merge at 25k gate | `0` |
| zero true overlap candidates | `16` |

已确认 `post_frontier_z3.batch01` smoke 包已经在
`discovered_predicatecheck_bank.jsonl` 第 13 行进入 register：

- strategy key：`false.finmodel.predicatecheck.model_family.beam_after_k40.post_frontier_z3.batch01`
- witness shards：`4`
- original current false union increment：`59,038`
- representative smoke：`4/4 accepted`
- register provenance：`controller_to_date_false_predicate_smoke_package_merge_20260522`

`mod17 affine` 批次仍不合并。其 true-overlap gate 通过，7 个候选累计
current false union increment 为 `3,071,381`，但 remote official judge smoke
不稳定：

| smoke | accepted | total | 结论 |
| --- | ---: | ---: | --- |
| initial representative batch | `8` | `23` | `15` 个 timeout |
| top1 light alternates | `0` | `4` | `1` rejected，`3` 个 request failed |

最终本轮没有新增 register row；重算 register 后保持：

| 指标 | 数值 |
| --- | ---: |
| deterministic false covered | `2,369,435,311` |
| deterministic true covered | `1,350,989,631` |
| unresolved estimate | `195,268,258` |
| conflict count | `0` |
| strategy count | `287` |
| false strategy rows | `250` |
| predicatecheck bank rows | `13` |
| setcheck bank rows | `40` |

### 2026-05-22 false 继续挖掘：hstep-tail mutation/setcheck gate

在最新 `current_residual_after_hstep_tail_false_mining` residual sample
上继续挖掘 false deterministic setcheck 候选。本轮只写 candidate 层，
不修改 `solver.py` 或正式 register。

复核产物：

- direct Z3 order4 synthesis summary：`data/processed/order5_strategy_registry/candidates/false_hstep_tail_top12_z3_order4_models_20260522_summary.json`
- top-bucket mutation summary：`data/processed/order5_strategy_registry/candidates/false_hstep_tail_mutated_model_pool_gen1_20260522_summary.json`
- all-residual mutation summary：`data/processed/order5_strategy_registry/candidates/false_hstep_tail_allres_mutated_model_pool_gen1_20260522_summary.json`
- setcheck rank：`data/processed/order5_strategy_registry/candidates/false_hstep_tail_allres_mutated_model_pool_gen1_setcheck_rank_20260522.jsonl`
- register selection summary：`data/processed/order5_strategy_registry/candidates/false_hstep_tail_allres_mutated_model_pool_gen1_register_selection_20260522_summary.json`
- targeted order5 Z3 summary：`data/processed/order5_strategy_registry/candidates/false_hstep_tail_mutation_hit_order5_z3_models_20260522_summary.json`
- targeted order5 setcheck rank：`data/processed/order5_strategy_registry/candidates/false_hstep_tail_mutation_hit_order5_z3_setcheck_rank_20260522.jsonl`
- order5 model-family search summary：`data/processed/order5_strategy_registry/candidates/false_predicate_hstep_tail_with_order5_z3_model_family_search_20260522_summary.json`
- gate audit summary：`data/processed/order5_strategy_registry/candidates/false_hstep_tail_mutation_setcheck_register_gate_audit_20260522_summary.json`

结果：

| 项目 | 结果 |
| --- | ---: |
| Z3 order4 selected pairs | `96` |
| Z3 sat models | `0` |
| top-bucket mutation models scored | `15,492` |
| top-bucket mutation sample-hit models | `0` |
| all-residual mutation models scored | `20,775` |
| all-residual mutation sample-hit models | `117` |
| best setcheck current false union increment | `26,530` |
| setcheck candidates >= 100k | `0` |
| true-overlap checked candidates | `20` |
| zero true-overlap candidates | `20` |
| greedy selected candidate count | `10` |
| greedy cumulative current false union increment | `89,871` |
| targeted order5 Z3 selected pairs | `8` |
| targeted order5 Z3 sat models | `8` |
| best targeted order5 setcheck increment | `13,973` |
| best order5-augmented model-family increment | `26,530` |
| order5-augmented model-family candidates >= 100k | `0` |

结论：这批候选 true-overlap gate 通过，但 best 单候选和 greedy
累计增量都低于 `100,000` 的尾部 smoke/register 门槛；从 mutation
命中 pair 反推的 order5 Z3 模型虽然 `8/8` sat 且 Python verified，
但单表 setcheck 和 order5-augmented model-family search 仍没有放大到
`100,000`。remote official judge smoke 未运行，register 不追加。候选
保留在 candidate parking，后续若要继续 false 侧，需要优先寻找新模型族
或更高命中的 residual 分层，而不是继续局部扰动已有 witness 表。

### 2026-05-22 false round2：fresh current residual tail batch

上一轮 hstep-tail residual sample 的 `coverage_used` 已落后于当前 register。
本轮先基于最新 `coverage_summary.json` 重新采样 current residual，再继续
false finite-model mining。

fresh residual 采样：

- summary：`data/processed/order5_strategy_registry/current_residual_false_mining_round2_shape_16000_seed20260522_summary.json`
- residual sample：`data/processed/order5_strategy_registry/current_residual_false_mining_round2_shape_16000_seed20260522_residual_sample.jsonl`
- coverage used：false `2,369,435,311`，true `1,354,729,736`，unresolved `191,528,153`，conflict `0`
- sample size：`16,000`
- current residual sample count：`1,708`
- true-filter retained rate：`0.10675`

探索产物：

- top-bucket order5 Z3：`data/processed/order5_strategy_registry/candidates/false_round2_top10_z3_order5_models_20260522_summary.json`
- low-target-complexity order5 Z3：`data/processed/order5_strategy_registry/candidates/false_round2_low_target_complexity_order5_z3_models_20260522_summary.json`
- low-target setcheck rank：`data/processed/order5_strategy_registry/candidates/false_round2_low_target_complexity_order5_z3_setcheck_rank_20260522.jsonl`
- fresh model-family search：`data/processed/order5_strategy_registry/candidates/false_predicate_round2_fresh_residual_with_order5_z3_model_family_search_20260522_summary.json`
- fresh mutation pool：`data/processed/order5_strategy_registry/candidates/false_round2_fresh_residual_mutated_model_pool_gen1_20260522_summary.json`
- fresh mutation setcheck rank：`data/processed/order5_strategy_registry/candidates/false_round2_fresh_residual_mutated_model_pool_gen1_setcheck_rank_20260522.jsonl`
- selection summary：`data/processed/order5_strategy_registry/candidates/false_round2_fresh_residual_mutated_model_pool_gen1_register_selection_20260522_summary.json`
- smoke build summary：`data/processed/order5_strategy_registry/candidates/false_round2_fresh_residual_mutated_model_pool_gen1_smoke_20260522_build_summary.json`
- remote smoke summary：`data/processed/order5_strategy_registry/candidates/false_round2_fresh_residual_mutated_model_pool_gen1_smoke_remote_20260522_summary.json`
- gate audit summary：`data/processed/order5_strategy_registry/candidates/false_round2_fresh_residual_tail_batch_register_gate_audit_20260522_summary.json`
- top100 selection summary：`data/processed/order5_strategy_registry/candidates/false_round2_fresh_residual_mutated_model_pool_gen1_register_selection_top100_20260522_summary.json`
- top100 smoke build summary：`data/processed/order5_strategy_registry/candidates/false_round2_fresh_residual_mutated_model_pool_gen1_top100_smoke_20260522_build_summary.json`
- top100 remote smoke summary：`data/processed/order5_strategy_registry/candidates/false_round2_fresh_residual_mutated_model_pool_gen1_top100_smoke_remote_20260522_summary.json`
- top100 gate audit summary：`data/processed/order5_strategy_registry/candidates/false_round2_fresh_residual_tail_batch_top100_register_gate_audit_20260522_summary.json`

结果：

| 项目 | 结果 |
| --- | ---: |
| top-bucket order5 Z3 selected pairs | `50` |
| top-bucket order5 Z3 sat models | `0` |
| low-target order5 Z3 selected pairs | `40` |
| low-target order5 Z3 sat models | `2` |
| best low-target order5 setcheck increment | `13,218` |
| order5/fresh model-family best increment | `26,743` |
| order5/fresh model-family candidates >= 100k | `0` |
| fresh mutation models scored | `18,309` |
| fresh mutation sample-hit models | `329` |
| fresh mutation best setcheck increment | `31,027` |
| fresh mutation setcheck candidates >= 100k | `0` |
| true-overlap checked candidates | `30` |
| zero true-overlap candidates | `30` |
| greedy selected candidate count | `12` |
| greedy cumulative current false union increment | `119,323` |
| representative remote smoke | `32/32 accepted` |
| top100 true-overlap checked candidates | `100` |
| top100 zero true-overlap candidates | `100` |
| top100 greedy selected candidate count | `40` |
| top100 greedy cumulative current false union increment | `186,883` |
| top100 representative remote smoke | `103/103 accepted` |

结论：单个候选仍未达到 `100,000` tail gate，但 fresh mutation 的
top30 greedy batch 在 true-overlap 为 `0` 的条件下累计新增
`119,323`，并且 representative remote official judge smoke `32/32`
accepted。继续扩展到 top100 后，40-row greedy batch 累计新增
`186,883`，所有 top100 candidate 的 true-overlap 仍为 `0`，
representative smoke `103/103 accepted`。该扩展批次已形成
candidate-layer register-ready tail batch；
本挖掘 session 按技能边界不直接追加正式 register，后续由总控决定
是否接受 `40` 个 setcheck row 换取约 `187k` 的 false 覆盖增量。
总控已在后续 current registry 下完成合并复核并追加 register，见下方
“false round2 fresh setcheck top100 register 合并”。

### 2026-05-22 true postedge3 top80 extension register 合并

postedge2 top60 extension 合入后，继续对最新 current residual 做
stratified sample。样本显示 true filter 后保留率从上一轮 `0.115375`
降到 `0.1087`，但 `mul>mul -> mul>mul` residual top80 中仍有一个
同族 `hconst-default-sandwich` batch 满足 register gate。

当前 residual sample：

- sample summary：`data/processed/order5_strategy_registry/current_residual_after_postedge2_top60_extension_shape_10000_seed20260522_summary.json`
- residual buckets：`data/processed/order5_strategy_registry/current_residual_after_postedge2_top60_extension_shape_10000_seed20260522_residual_buckets.json`
- false-uncovered sample：`10,000`
- current residual after true filter：`1,087`
- retained rate：`0.1087`
- coverage used：false `2,369,435,311`，true `1,350,989,631`，unresolved `195,268,258`，conflict `0`

构建 current coverage profile v18：

- profile：`data/processed/order5_strategy_registry/candidates/current_coverage_profile_v18_20260522.json`
- true explicit pair count：`34,073,752`
- true source-target group count：`122`
- false group count：`10,122`
- timings：registry build `125.06s`，profile build `152.49s`，total `277.56s`

对 residual top80 中 47 个 `mul>mul -> mul>mul` bucket 跑
`hconst-default-sandwich` exact scan；其中 19 个 positive shape pair
合并后满足 main register gate：

| 指标 | 数值 |
| --- | ---: |
| positive shape pair count | `19` |
| combined exact true union increment | `3,740,105` |
| conflict increment | `0` |
| remote smoke | `120/120 accepted` |
| pair-index SHA256 | `9ee3b27bcf4e6f6ae4d55d65e3903a6241bb47975abda6b3c534b5db250bd6f2` |

最大几个 shape pair：

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

register 产物：

- strategy id：`true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.postedge3_top80_extension.v1`
- scan index：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_after_postedge2_top80_v18_20260522_scan_index.json`
- combined hits：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge3_top80_extension_full_v18_20260522_hits.jsonl`
- candidate summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge3_top80_extension_full_v18_20260522_summary.json`
- register summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge3_top80_extension_register_pair_index_cache_20260522_summary.json`
- smoke summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge3_top80_extension_smoke_20260522_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_postedge3_top80_extension_pair_indexes_20260522.txt`

full `coverage_summary()` 重算结果：

| 指标 | 数值 |
| --- | ---: |
| deterministic false covered | `2,369,435,311` |
| deterministic true covered | `1,354,729,736` |
| unresolved estimate | `191,528,153` |
| conflict count | `0` |
| strategy count | `288` |
| runtime | `19:43.21` |

验证：

- remote smoke：`120/120 accepted`
- focused opnorm tests：`45 passed`
- full `tests/order5_strategy_registry` regression：`97 passed in 495.80s`

### 2026-05-22 true postedge4 top100 extension register 合并

postedge3 top80 extension 合入后，继续对最新 current residual 做
stratified sample。样本中 true filter 后保留率继续降到 `0.1051666667`；
`hconst-default-sandwich` 在前排 bucket 基本清空，但 top100 后排仍有
18 个 positive shape pair，合并后仍满足 main register gate。

当前 residual sample：

- sample summary：`data/processed/order5_strategy_registry/current_residual_after_postedge3_top80_extension_shape_12000_seed20260522_summary.json`
- residual buckets：`data/processed/order5_strategy_registry/current_residual_after_postedge3_top80_extension_shape_12000_seed20260522_residual_buckets.json`
- false-uncovered sample：`12,000`
- current residual after true filter：`1,262`
- retained rate：`0.1051666667`
- coverage used：false `2,369,435,311`，true `1,354,729,736`，unresolved `191,528,153`，conflict `0`

构建 current coverage profile v19：

- profile：`data/processed/order5_strategy_registry/candidates/current_coverage_profile_v19_20260522.json`
- true explicit pair count：`37,813,857`
- true source-target group count：`122`
- false group count：`10,122`
- timings：registry build `134.01s`，profile build `153.50s`，total `287.51s`

对 residual top100 bucket 跑 `hconst-default-sandwich` exact scan；
其中 18 个 positive shape pair 合并后满足 main register gate：

| 指标 | 数值 |
| --- | ---: |
| positive shape pair count | `18` |
| combined exact true union increment | `3,117,295` |
| conflict increment | `0` |
| remote smoke | `120/120 accepted` |
| pair-index SHA256 | `eca638eeb2bcb2a8f514baf21704e1649d4e7fb0f9b273dac6a60da84a15e77e` |

最大几个 shape pair：

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

register 产物：

- strategy id：`true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.postedge4_top100_extension.v1`
- scan index：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_after_postedge3_top100_v19_20260522_scan_index.json`
- combined hits：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge4_top100_extension_full_v19_20260522_hits.jsonl`
- candidate summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge4_top100_extension_full_v19_20260522_summary.json`
- register summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge4_top100_extension_register_pair_index_cache_20260522_summary.json`
- smoke summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge4_top100_extension_smoke_20260522_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_postedge4_top100_extension_pair_indexes_20260522.txt`

full `coverage_summary()` 重算结果：

| 指标 | 数值 |
| --- | ---: |
| deterministic false covered | `2,369,435,311` |
| deterministic true covered | `1,357,847,031` |
| unresolved estimate | `188,410,858` |
| conflict count | `0` |
| strategy count | `289` |
| runtime | `20:56.58` |

验证：

- remote smoke：`120/120 accepted`
- focused opnorm tests：`47 passed`
- full `tests/order5_strategy_registry` regression：`99 passed in 511.62s`

### 2026-05-22 false round2 fresh setcheck top100 register 合并

总控在 true postedge4 top100 extension 合入后的 current registry 上，
重新复核 false round2 fresh mutation setcheck top100 smoke package。复核
没有使用旧 true 覆盖数字：重新跑 greedy selection 和 true-overlap
precheck 后，top100 候选仍全部与 current true registry 零重叠，40-row
batch 的累计 false union increment 仍为 `186,883`。

register 复核产物：

- current merge selection：`data/processed/order5_strategy_registry/candidates/false_controller_round2_fresh_setcheck_top100_current_merge_selection_20260522.jsonl`
- current merge selection summary：`data/processed/order5_strategy_registry/candidates/false_controller_round2_fresh_setcheck_top100_current_merge_selection_20260522_summary.json`
- register append summary：`data/processed/order5_strategy_registry/candidates/false_controller_round2_fresh_setcheck_top100_register_append_20260522_summary.json`
- register merge verified summary：`data/processed/order5_strategy_registry/candidates/false_controller_round2_fresh_setcheck_top100_register_merge_verified_20260522_summary.json`
- register bank：`data/processed/order5_strategy_registry/discovered_setcheck_bank.jsonl`

合并结果：

| 项目 | 结果 |
| --- | ---: |
| appended setcheck rows | `40` |
| priority range | `624..663` |
| current true-overlap sum | `0` |
| cumulative current false union increment | `186,883` |
| representative remote smoke | `103/103 accepted` |
| smoke backend | `http://10.220.69.172:8888` |

coverage summary 变化：

| 指标 | 合并前 | 合并后 |
| --- | ---: | ---: |
| deterministic false covered | `2,369,435,311` | `2,369,622,194` |
| deterministic true covered | `1,357,847,031` | `1,357,847,031` |
| unresolved estimate | `188,410,858` | `188,223,975` |
| conflict count | `0` | `0` |

验证：

- coverage regenerate：`PYTHONPATH=src .venv/bin/python scripts/data/summarize_order5_strategy_coverage.py --reuse-true-from-output --update-source-target-cache`
- focused registry tests：`24 passed in 548.43s`
- full `tests/order5_strategy_registry` regression：`103 passed in 615.09s`

并发 true 侧 full summarize 完成后，当前总 register summary 进一步变为：
false `2,369,622,194`，true `1,359,760,747`，unresolved
`186,310,259`，conflict `0`。false 侧本批合并增量仍为
`186,883`。

### 2026-05-22 true hconst-default-sandwich postedge5 top120 register 合并

总控把 true 侧可用 candidate batch 推进到 register 层。该 batch 使用
postedge4 + false round2 fresh setcheck 后的 current register 作为基准，
对 top120 residual shape 运行 `hconst-default-sandwich` exact scan。19 个
positive bucket 合并后仍超过 main gate，且 current false conflict 为 `0`。

register 复核产物：

- v20 coverage profile：`data/processed/order5_strategy_registry/candidates/current_coverage_profile_v20_after_postedge4_top100_20260522.json`
- scan index：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_after_postedge4_top120_v20_20260522_scan_index.json`
- combined hits：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge5_top120_extension_full_v20_20260522_hits.jsonl`
- register summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge5_top120_extension_register_pair_index_cache_20260522_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_postedge5_top120_extension_pair_indexes_20260522.txt`
- smoke summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge5_top120_extension_smoke_20260522_summary.json`
- smoke retry summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge5_top120_extension_smoke_20260522_retry_summary.json`

合并结果：

| 项目 | 结果 |
| --- | ---: |
| strategy id | `true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.postedge5_top120_extension.v1` |
| positive shape pair count | `19` |
| exact true union increment | `1,913,716` |
| current false conflict increment | `0` |
| representative remote smoke | `120/120 accepted` |
| pair-index SHA256 | `8c4a1283bf1363d76a0238021dc01e08c568e5888735aa2f85259ab7bdd9c53b` |

coverage summary 变化：

| 指标 | 合并前 | 合并后 |
| --- | ---: | ---: |
| deterministic false covered | `2,369,622,194` | `2,369,622,194` |
| deterministic true covered | `1,357,847,031` | `1,359,760,747` |
| unresolved estimate | `188,223,975` | `186,310,259` |
| conflict count | `0` | `0` |

验证：

- remote smoke：首轮 `119/120 accepted`，唯一失败为 `REMOTE_SIMPLE_API_REQUEST_FAILED`；失败记录单独 retry 后 `1/1 accepted`，合计 `120/120 accepted`
- full coverage regenerate：`.venv/bin/python scripts/data/summarize_order5_strategy_coverage.py`
- full `coverage_summary()` runtime：约 `25m`，远超 6 分钟固定超时，但进程期间 CPU/RSS 持续变化，属于正常长跑而不是 hang
- focused opnorm tests：`49 passed in 24.93s`
- full `tests/order5_strategy_registry` regression：`103 passed in 615.77s`

后续优化建议：

- register gate 不应只按 6 分钟 wall-clock 杀 full `coverage_summary()`；应至少看进程健康、CPU/RSS、阶段性 cache 写入，或单独给 true/false 大 cache 合并更长 timeout。
- 主循环先用 coverage profile delta 做 quick gate：`union_increment >= 1M`、`conflict_increment == 0`、remote smoke accepted 后再进入 register。
- full `coverage_summary()` 保留为最终长跑 gate，或改为基于现有 profile 的增量 summary，避免每个 candidate 都重建全 pair-space union。

### 2026-05-22 true hconst-default-sandwich postedge6 sample-hit top20 tail register 合并

postedge5 合入后，重新从 current residual 抽样 `18,000` 条 false-uncovered
pair，其中 `1,861` 条仍是 current unresolved，retained rate 为
`0.1033888889`。直接继续扫 top residual bucket 的 ROI 已下降，因此先在
residual sample 上跑 fast matcher probe，再只扩展 `hconst-default-sandwich`
命中的 top20 shape pair。该 batch 仍达到百万级 main register gate。

探索与 register 复核产物：

- residual sample summary：`data/processed/order5_strategy_registry/current_residual_after_postedge5_top120_extension_shape_18000_seed20260522_summary.json`
- fast matcher probe：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_fast_hconst_default_after_postedge5_residual_sample_20260522_summary.json`
- v22 coverage profile：`data/processed/order5_strategy_registry/candidates/current_coverage_profile_v22_after_postedge5_top120_20260522.json`
- scan index：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_after_postedge5_samplehit_top20_v22_20260522_scan_index.json`
- combined hits：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge6_samplehit_top20_tail_full_v22_20260522_hits.jsonl`
- candidate summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge6_samplehit_top20_tail_full_v22_20260522_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_postedge6_samplehit_top20_tail_pair_indexes_20260522.txt`
- smoke summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge6_samplehit_top20_tail_smoke_20260522_summary.json`

合并结果：

| 项目 | 结果 |
| --- | ---: |
| strategy id | `true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.postedge6_samplehit_top20_tail.v1` |
| positive shape pair count | `20` |
| exact true union increment | `2,008,676` |
| current false conflict increment | `0` |
| representative remote smoke | `120/120 accepted` |
| pair-index SHA256 | `ebd47b400aac1e2ab990cbee781447cd3ad13936bfe7ee4d70f1dbd4589611ec` |

coverage summary 变化：

| 指标 | 合并前 | 合并后 |
| --- | ---: | ---: |
| deterministic false covered | `2,369,622,194` | `2,369,622,194` |
| deterministic true covered | `1,359,760,747` | `1,361,769,423` |
| unresolved estimate | `186,310,259` | `184,301,583` |
| conflict count | `0` | `0` |

验证：

- remote smoke：`120/120 accepted`
- full coverage regenerate：`.venv/bin/python scripts/data/summarize_order5_strategy_coverage.py`
- focused opnorm tests：`51 passed in 24.99s`
- full `tests/order5_strategy_registry` regression：`105 passed in 654.23s`

本轮 full `coverage_summary()` 继续表现为 CPU 满负载长跑，耗时约 30 分钟。
后续夜跑主循环应避免每个 candidate 都立即跑 full summary：先用 v22
coverage profile delta、pair-index digest、remote smoke 和 focused
discoverability test 做 quick gate，再把 full summary 放到 register batch
末尾统一跑。

### 2026-05-22 true hconst-default-sandwich postedge7 sample-hit top20 tail register 合并

postedge6 合入后继续采样 `20,000` 条 false-uncovered pair，其中 `2,041`
条仍是 current unresolved，retained rate 为 `0.10205`。fast matcher probe
显示同 family 仍有尾部信号：`hconst=173/2041`、
`hconst_default_sandwich=230/2041`，但命中几乎仍在
`mul>mul -> mul>mul`。因此本轮继续使用 sample-hit top20 bucket exact scan，
作为同 family tail batch，而不是把它误当成新的 `var>mul` 模板。

探索与 register 复核产物：

- residual sample summary：`data/processed/order5_strategy_registry/current_residual_after_postedge6_samplehit_top20_tail_shape_20000_seed20260522_summary.json`
- fast matcher probe：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_fast_hconst_default_after_postedge6_residual_sample_20260522_summary.json`
- v23 coverage profile：`data/processed/order5_strategy_registry/candidates/current_coverage_profile_v23_after_postedge6_samplehit_top20_tail_20260522.json`
- scan index：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_after_postedge6_samplehit_top20_v23_20260522_scan_index.json`
- combined hits：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge7_samplehit_top20_tail_full_v23_20260522_hits.jsonl`
- candidate summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge7_samplehit_top20_tail_full_v23_20260522_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_postedge7_samplehit_top20_tail_pair_indexes_20260522.txt`
- smoke summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge7_samplehit_top20_tail_smoke_20260522_summary.json`

合并结果：

| 项目 | 结果 |
| --- | ---: |
| strategy id | `true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.postedge7_samplehit_top20_tail.v1` |
| positive shape pair count | `20` |
| exact true union increment | `2,769,157` |
| current false conflict increment | `0` |
| representative remote smoke | `120/120 accepted` |
| pair-index SHA256 | `fd0e15124305ea9b9d19a9b28ef8b05c7781181cdb1c5df62bb0343d6a91975e` |

coverage summary 变化：

| 指标 | 合并前 | 合并后 |
| --- | ---: | ---: |
| deterministic false covered | `2,369,622,194` | `2,369,622,194` |
| deterministic true covered | `1,361,769,423` | `1,364,538,580` |
| unresolved estimate | `184,301,583` | `181,532,426` |
| conflict count | `0` | `0` |
| strategy count | `331` | `332` |

验证：

- remote smoke：`120/120 accepted`
- full coverage regenerate：`.venv/bin/python scripts/data/summarize_order5_strategy_coverage.py`
- focused opnorm tests：`53 passed in 29.11s`
- full `tests/order5_strategy_registry` regression：`107 passed in 670.05s`

### 2026-05-22 false candidate 层总控复核

在 false round2 fresh setcheck top100 smoke package 合入 register，并发 true
postedge5 top120 extension 合入后，总控重新检查至今 candidate 层的 false
deterministic 策略。结论是：已 smoke 通过且仍适合进 register 的部分只有
前述 top100 setcheck 包；其他 candidate 当前要么已被 register 吸收，要么低于
tail gate，要么缺少稳定 certificate smoke 路径。

总控审计产物：

- audit summary：`data/processed/order5_strategy_registry/candidates/false_controller_candidate_layer_after_top100_postedge5_audit_20260522_summary.json`
- accepted predicate rescore：`data/processed/order5_strategy_registry/candidates/false_controller_to_date_accepted_predicate_current_rescore_after_top100_postedge5_20260522_summary.json`
- top220 remainder selection：`data/processed/order5_strategy_registry/candidates/false_round2_fresh_residual_mutated_model_pool_gen1_top220_after_top100_merge_selection_20260522_summary.json`
- affine truecheck selection：`data/processed/order5_strategy_registry/candidates/false_affine_mod_round3_after_postedge5_falsemerge_mod8_23_truecheck_selection_20260522_summary.json`

candidate 层复核：

| 候选线 | current 结果 | register 决策 |
| --- | ---: | --- |
| round2 top220 remainder after top100 | `54` selected，累计新增 `14,487` | parking lot，低于 `100,000` tail gate |
| accepted predicate smoke pool | `16` 候选，best increment `6,756`，`ge_100k=0` | parking lot / subsumed |
| round3 residual model-family search | `120` 候选，best increment `5,576`，`ge_100k=0` | parking lot |
| round3 mutated model pool | `15,062` mutated models，`0` hit | 无候选 |
| affine mod8..23 rerank | rank best `499,148`，truecheck 累计 `4,256,474`，true overlap `0` | 暂不合并，仍被 remote smoke/certificate 稳定性阻塞 |

round3 residual sample 显示最新残差已经明显碎片化：`16,000` 个
false-uncovered sample 只留下 `1,645` 个 current unresolved sample，
retained rate 为 `0.1028125`；最大 shape bucket 只有 `17/1,645`。

affine mod17 仍是当前 false 侧最大未落地信号：10 个 true-overlap 为零的
候选累计可贡献 `4,256,474` false union increment，但旧的
`false_affine_mod17_register_gate_audit_20260522_summary.json` 已记录
representative remote smoke 不稳定。除非先解决 affine certificate/smoke
路径，否则不进入 register。

### 2026-05-22 false smoke package 总控合并确认

按总控口径复核 candidate 层后，`round2_fresh_mutation_gen1` top100
setcheck smoke package 已正式进入 register 层；本轮不再重复追加。该包在
register 中对应 `40` 条 setcheck strategy，priority 为 `624..663`，
累计 false union increment 为 `186,883`，remote smoke 为 `103/103
accepted`，current true overlap 为 `0`。

最新 register 层状态：

| 指标 | 当前值 |
| --- | ---: |
| discovered setcheck bank rows | `80` |
| discovered predicatecheck bank rows | `13` |
| round2 fresh mutation gen1 strategy rows | `40` |
| deterministic false covered | `2,369,622,194` |
| deterministic true covered | `1,361,769,423` |
| unresolved estimate | `184,301,583` |
| conflict count | `0` |

本次总控确认产物：

- merge audit summary：`data/processed/order5_strategy_registry/candidates/false_controller_to_date_smoke_package_register_layer_merge_audit_20260522_summary.json`
- top100 merge summary：`data/processed/order5_strategy_registry/candidates/false_controller_round2_fresh_setcheck_top100_register_merge_verified_20260522_summary.json`
- latest predicate rescore：`data/processed/order5_strategy_registry/candidates/false_controller_to_date_smoked_predicate_current_rescore_after_top100_20260522_summary.json`

剩余 false candidate 层复核：

| 候选线 | 最新 current 结果 | register 决策 |
| --- | ---: | --- |
| accepted predicate smoke pool | best increment `6,756`，`ge_100k=0` | parking lot，不追加 |
| round3 residual model-family search | best increment `5,576`，`ge_100k=0` | parking lot |
| affine lowmod2..16 rerank | best increment `37,964`，`ge_100k=0` | parking lot |
| affine mod17 formula/native probes | top1 smoke `0/4 accepted` | certificate path 不稳定，不追加 |

验证：

- rescore：`.venv/bin/python scripts/data/rescore_order5_predicate_family_candidates.py --input-jsonl data/processed/order5_strategy_registry/candidates/false_controller_accepted_predicate_pool_from_smoke_20260521.jsonl --input-jsonl data/processed/order5_strategy_registry/candidates/false_controller_to_date_predicate_family_current_merge_selection_20260522.jsonl --output-jsonl data/processed/order5_strategy_registry/candidates/false_controller_to_date_smoked_predicate_current_rescore_after_top100_20260522.jsonl --summary-json data/processed/order5_strategy_registry/candidates/false_controller_to_date_smoked_predicate_current_rescore_after_top100_20260522_summary.json --top-k 200 --min-increment 1 --update-source-target-cache`
- coverage regenerate：`.venv/bin/python scripts/data/summarize_order5_strategy_coverage.py --reuse-true-from-output --update-source-target-cache`
- focused registry tests：`20 passed in 381.10s`

### 2026-05-22 false round4 after postedge6 复核

基于 postedge6 后的 current residual sample，false-uncovered `20,000`
样本只剩 `2,041` 个 current unresolved，retained rate 为 `0.10205`。
总控确认 top100 smoke package 已在 register 层，不重复追加；round4 只作为
新一轮候选挖掘和阻塞复核。

round4 mutation pool 从 `100` 个 seed model 扩展出 `13,132` 个
mutated model，但只有 `2` 个模型命中 residual sample，best full hit 只有
`1` 个 pair。后续 predicate family search 使用 `220` 个模型，beam 出
`2,511` 个 family，精确评分 `231` 个，best exact current false union
increment 为 `12,695`，`ge_100k=0`，因此仍归入 parking lot，不进入
register。

affine mod17 证书路径继续阻塞：`Fin.ofNat` formula/named style 与 direct
native style 的 top1 representative smoke 均为 `0/4 accepted`，状态为
`incorrect`；direct split/refine probe 已生成 `6` 条输入，但本地 polling
长时间无输出后被停止，没有形成可用 accepted summary。该线保留为 false 侧
最大信号之一，但在 stable remote smoke/certificate path 解决前不合并。

本轮审计产物：

- round4 audit summary：`data/processed/order5_strategy_registry/candidates/false_round4_after_postedge6_false_mining_audit_20260522_summary.json`
- round4 mutation summary：`data/processed/order5_strategy_registry/candidates/false_round4_after_postedge6_mutated_model_pool_gen1_20260522_summary.json`
- round4 predicate summary：`data/processed/order5_strategy_registry/candidates/false_predicate_round4_after_postedge6_model_family_search_20260522_summary.json`
- round4 residual sample summary：`data/processed/order5_strategy_registry/current_residual_after_postedge6_samplehit_top20_tail_shape_20000_seed20260522_summary.json`

### 2026-05-22 false round5 after postedge6 negative mining

继续沿 postedge6 后 `2,041` 条 current residual sample 做 false 侧挖掘。
本轮目标不是直接扩大 register，而是确认 round4 之后几个可能方向是否还有
可提升到 `100,000` tail gate 的确定性 false 策略。

Z3 pair-specific finite model synthesis（按 pair 合成有限模型）先跑
order4 top20 residual bucket：`80` 个 selected pair 中 `60` 个 `unsat`、
`20` 个 `unknown`、`0` 个 `sat`。随后把这 `20` 个 unknown pair 提升到
order5、`6s` timeout 复查，结果仍是 `20/20 unknown`，没有产出唯一模型。

mutation/random pool 方向也没有新信号：以 round4、round2 fresh、hstep tail、
round4 predicate family 和 order5 Z3 seed 为输入，允许 order6 random model，
共生成 `10,317` 个模型，在 all-residual `320` selected pair 上 `0` hit。

endpoint-role predicatecheck（端点角色谓词检查）使用 postedge6 residual
重新打分，结果全部远低于合并门槛：

| signature mode | best increment | ge_100k |
| --- | ---: | ---: |
| endpoint1 | `485` | `0` |
| endpoint2 | `50` | `0` |
| leafseq | `1` | `0` |

因此 round5 不追加 register row。本轮信号说明：postedge6 后的 false 残差
已经不适合继续用浅层 finite-model mutation、top-bucket Z3 或 endpoint-role
predicate 做主线推进；下一步更适合切向 affine certificate path 修复，或针对
具体高频 residual shape 设计新的 algebraic family，而不是扩大当前三类搜索。

round5 产物：

- audit summary：`data/processed/order5_strategy_registry/candidates/false_round5_after_postedge6_negative_mining_audit_20260522_summary.json`
- order4 Z3 summary：`data/processed/order5_strategy_registry/candidates/false_round5_after_postedge6_z3_order4_top20_20260522_summary.json`
- order5 Z3 summary：`data/processed/order5_strategy_registry/candidates/false_round5_after_postedge6_z3_order5_unknown20_20260522_summary.json`
- order6 mutation summary：`data/processed/order5_strategy_registry/candidates/false_round5_after_postedge6_allres_order6_mutated_pool_20260522_summary.json`
- endpoint1 summary：`data/processed/order5_strategy_registry/candidates/false_endpoint_predicate_after_postedge6_endpoint1_20260522_summary.json`
- endpoint2 summary：`data/processed/order5_strategy_registry/candidates/false_endpoint_predicate_after_postedge6_endpoint2_20260522_summary.json`
- leafseq summary：`data/processed/order5_strategy_registry/candidates/false_endpoint_predicate_after_postedge6_leafseq_20260522_summary.json`

### 2026-05-22 false affine mod17 direct_split light-alt 复核

继续沿当前最大 false 侧未落地信号 affine mod17 做 certificate/smoke
阻塞定位。`mod17.a7.b11.c0` top candidate 的 current false union increment
为 `499,148`，lowcpu truecheck batch 累计为 `4,256,474`，true overlap 为
`0`。此前原始 representative pair 中 order4-source tier 可以用 Fin17 table
证书 accepted，但 order5-source tier 在 table、formula 和 direct_split/refine
路径上都不稳定。

本轮把 affine alternate smoke 生成脚本补充 `direct_split` 证书模式，并重新
选择低复杂度 order5-source representative pairs：两个
`new_order5_source_to_order4_target`、两个
`new_order5_source_to_order5_target`。四条 source 都是 2 变量、depth `5`、
node count `12` 的最轻 order5-source 候选；target 侧包含 commutativity
`x * y = y * x` 这类低复杂度 order4 方程。

remote smoke 使用 remote-http primary backend、短 run-id、单并发和 no-cache，
排除了之前 light-alt top2 的 run-id 409 冲突。结果仍为 `0/4 accepted`，
四条全部 `REMOTE_SIMPLE_API_REJECTED`，每条 elapsed 都约 `301.5s`：

| tier | pair | elapsed | status |
| --- | ---: | ---: | --- |
| order5 -> order4 | `30345 -> 43` | `301.50s` | rejected |
| order5 -> order4 | `40133 -> 43` | `301.51s` | rejected |
| order5 -> order5 | `4899 -> 55569` | `301.47s` | rejected |
| order5 -> order5 | `4899 -> 55627` | `301.48s` | rejected |

结论：affine mod17 阻塞不是 representative pair 过重或 run-id 冲突，而是
Fin17/order5-source certificate 证明时间墙。该 batch 继续保持
`do_not_merge_register`；除非出现 materially faster certificate encoding
（例如不是 Fin17 全表 `decideFin!` 的证明路径），否则不应继续在同一
representative-pair 维度调参。false 主线应转向非 Fin17 的 algebraic family
或其他具备稳定 remote smoke 路径的候选来源。

本轮产物：

- script patch：`scripts/data/find_order5_affine_smoke_alternates.py`
- input summary：`data/processed/order5_strategy_registry/candidates/false_affine_mod17_top1_direct_split_light_alt_o5sources_20260522_input_summary.json`
- remote summary：`data/processed/order5_strategy_registry/candidates/false_affine_mod17_top1_direct_split_light_alt_o5sources_20260522_summary.json`
- audit summary：`data/processed/order5_strategy_registry/candidates/false_affine_mod17_direct_split_light_alt_o5source_smoke_audit_20260522_summary.json`

### 2026-05-22 false bilinear small-mod probe

按 affine mod17 阻塞后的转向建议，试探一个小阶非线性 algebraic family：

```text
x * y = a*x + b*y + d*x*y + c (mod n),  n in {2,3,4,5}, d != 0
```

这个 family 的动机是保留小阶 finite table certificate 的稳定性，避免 Fin17
order5-source `decideFin!` 的约 `301s` 证明时间墙。搜索只在 postedge6 后
`2,041` 条 current residual sample 上做 discovery，再对 sample 命中的 top
candidate 做 exact scoring。

结果为 `sample_candidate_count=0`：在 `mod 2..5` 的所有去重 bilinear table
中，没有任何模型命中 postedge6 residual sample pair。因此该 family 当前不做
true-overlap、remote smoke 或 register 合并；它作为“非 Fin17 小阶非线性
代数族”已被快速排除。

产物：

- summary：`data/processed/order5_strategy_registry/candidates/false_bilinear_mod2_5_postedge6_residual_rank_20260522_summary.json`
- candidate JSONL：`data/processed/order5_strategy_registry/candidates/false_bilinear_mod2_5_postedge6_residual_rank_20260522.jsonl`

### 2026-05-22 true hconst-default-sandwich postedge8 exact top10 combined tail register 合并

按总控要求，把 true candidate 层中已经具备 register 条件的
`hconst-default-sandwich` tail batch 合入 register。该 batch 来自 postedge8 后
current residual sample 命中的 10 个 shape pair exact scan，低于 `1M` 主线
gate，但属于同一稳定 proof compiler 的 tail batch，且 exact current union
increment 为 `677,528`、false conflict 为 `0`。

register 复核产物：

- v25 coverage profile：`data/processed/order5_strategy_registry/candidates/current_coverage_profile_v25_current_after_postedge8_20260522.json`
- combined candidate summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge8_exact_top10_combined_tail_20260522_summary.json`
- register summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge8_exact_top10_combined_tail_register_pair_index_cache_20260522_summary.json`
- pair-index cache：`data/processed/order5_strategy_registry/opnorm_hconst_default_sandwich_postedge8_exact_top10_combined_tail_pair_indexes_20260522.txt`
- remote smoke summary：`data/processed/order5_strategy_registry/candidates/true_template_opnorm_hconst_default_sandwich_postedge8_exact_top10_combined_tail_smoke_20260522_summary.json`

合并结果：

| 项目 | 结果 |
| --- | ---: |
| strategy id | `true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse.postedge8_exact_top10_combined_tail.v1` |
| positive shape pair count | `10` |
| exact true union increment | `677,528` |
| current false conflict increment | `0` |
| representative remote smoke | `100/100 accepted` |
| pair-index SHA256 | `9e7f6a3b7a10cc74212dd197cb412d7210dc86091ddcfc298fe4981a9fa94c28` |

coverage summary 变化：

| 指标 | 合并前 | 合并后 |
| --- | ---: | ---: |
| deterministic false covered | `2,369,622,194` | `2,369,622,194` |
| deterministic true covered | `1,365,748,955` | `1,366,426,483` |
| unresolved estimate | `180,322,051` | `179,644,523` |
| conflict count | `0` | `0` |
| strategy count | `333` | `334` |

验证：

- remote smoke：`100/100 accepted`
- full coverage regenerate：`PYTHONPATH=src .venv/bin/python scripts/data/summarize_order5_strategy_coverage.py --update-source-target-cache`
- focused smoke/discoverability tests：`4 passed in 28.50s`
- full `tests/order5_strategy_registry` regression：`111 passed in 646.94s`
- data tool regression：`tests/data/test_order5_strategy_mining_state.py tests/data/test_summarize_order5_strategy_coverage.py`，`7 passed in 0.09s`

## 参考产物

- `artifacts/runs/2026-05-21/opnorm-current-residual-cv100-20260521/remote_final_detail.json`
- `artifacts/runs/2026-05-21/opnorm-current-residual-cv500-20260521/combined_cv500_summary.json`
- `artifacts/runs/2026-05-21/opnorm-current-residual-shape-stratified-20260521/shape_bucket_analysis.json`
- `artifacts/runs/2026-05-21/opnorm-current-residual-shape-stratified-20260521/remote_final_detail.json`
- `artifacts/runs/2026-05-21/opnorm-current-residual-shape-stratified-20260521/sampling/current_residual_shape_stratified_top20x15_tail100_seed20260523_manifest.json`
