# Data And Code Inventory

Updated: 2026-05-21

## Raw Data

- `data/raw/huggingface/selected_problems/normal.jsonl` - 1000 public normal rows
- `data/raw/huggingface/selected_problems/hard1.jsonl` - 69 public hard1 rows
- `data/raw/huggingface/selected_problems/hard2.jsonl` - 200 public hard2 rows
- `data/raw/huggingface/selected_problems/hard3.jsonl` - 400 public hard3 rows
- `hard.jsonl` is intentionally excluded from default raw data because it
  duplicates the hard/hard1 slice for this workflow.
- `data/raw/huggingface/benchmark/` - small Stage 1 benchmark metadata,
  leaderboard, model registry, and prompt template
- `data/raw/references/sair_api/` - competition API snapshots
- `data/raw/references/sair_contributor_network/` - public Contributor Network
  solver snapshots, including page HTML, bootstrap JSON, extracted `solver.py`,
  and retrieval metadata.
- `data/raw/references/stage2_judge/` - official Stage 2 judge/evaluation
  repository raw snapshots, including rules, Solo/Marathon docs,
  `judge/verify.py`, `pipeline/config.json`, `lean-toolchain`, and
  `main_commit.json`.
- `data/raw/references/etp/full_entries.json` - ETP proven-result index source
- `data/raw/references/stage1_judge/` - Stage 1 judge README/model config
- `data/raw/references/zulip/` - official discussion archive snapshots used by
  `stage2-info-zulip-channel`; latest local sync is message id `2101`
  across archived dates through `2026-05-21`.
- `data/raw/manifest.json` - download manifest with source URLs and counts

## Processed Data

- `data/processed/public_problem_index.jsonl` - 1669 default public rows with
  `eq1_signature` and `eq2_signature`
- `data/processed/public_problem_index.summary.json` - public row summary
- `data/processed/splits/train.jsonl`、`dev.jsonl`、`test.jsonl` - deterministic
  train/dev/test split（确定性训练/开发/测试集划分）
- `data/processed/splits/manifest.json` - split ratios（划分比例）、seed（随机种子）
  和按 `subset + answer` 分层统计
- `data/processed/public_coverage_summary.json` - ETP graph/fact coverage over
  the default public set
- `data/processed/etp/etp_implications.jsonl` - 10674 ETP implication entries
- `data/processed/etp/etp_facts.jsonl` - 1698 ETP fact/countermodel entries
- `data/processed/etp/etp_unconditionals.jsonl` - 1 unconditional entry
- `data/processed/etp/etp_result_index.summary.json` - ETP index summary
- `data/assets/counterexamples/` - counterexample asset dataset（反例资产数据集）；
  每个 `eq1-<id>-eq2-<id>/` 问题目录保存 `problem.json`、`latest.json`
  和多轮 `runs/<run-id>/certificate.lean`、`countermodel.json`、`verification.json`。

## External Code

- `external/equational_theories/` - shallow clone of
  `teorth/equational_theories`; needed for Lean certificate generation.
- `external/equational-theories-stage1-judge/` - shallow clone of
  `SAIRcompetition/equational-theories-stage1-judge`; useful for reference
  parsing/judge behavior and Stage 1 compatibility.
- `external/equational-theories-lean-stage2/` - expected official Stage 2
  judge/evaluation repository path. As of 2026-05-21 this directory contains
  the official file tree but is not a git clone, so update status is tracked
  from `data/raw/references/stage2_judge/` and `git ls-remote` until the local
  path is repaired.

## Local Code

- `src/math_distill_stage2/equations.py` - parser and canonical equation
  signatures.
- `src/math_distill_stage2/dataset_io.py` - JSONL IO, counts, summaries.
- `src/math_distill_stage2/etp_entries.py` - ETP `full_entries.json` indexing.
- `src/math_distill_stage2/implication_graph.py` - implication graph path and
  fact lookup helpers.
- `src/math_distill_stage2/lean_certificates.py` - Lean smoke certificate
  generation helpers.
- `src/math_distill_stage2/counterexample/` - counterexample package（反例包），统一管理反模型搜索、反例资产、资产验证和已验证索引。
- `src/math_distill_stage2/counterexample/finite_magma.py` - finite magma evaluator
  and exhaustive countermodel search core（有限岩浆求值器和穷举反模型搜索核心）。
- `src/math_distill_stage2/counterexample/search.py` - countermodel search run
  orchestration（反模型搜索运行编排），写出可复现 run artifacts。
- `src/math_distill_stage2/public_eval.py` - public-set evaluation harness
  helpers（公开集实验编排器辅助代码），用于写出可复现 run artifacts（运行产物）。
- `src/math_distill_stage2/counterexample/verified_index.py` - verified counterexample
  index builder（已验证反例索引构建器），把公开问题、反模型和 Lean 证书关联落盘。
- `src/math_distill_stage2/lean_executor/` - Lean executor package
  （Lean 执行器包），统一管理不同后端。
- `src/math_distill_stage2/lean_executor/base.py` - Lean executor interface
  （Lean 执行器接口），定义任务、结果和统一命令执行格式。
- `src/math_distill_stage2/lean_executor/docker.py` - Docker Lean backend
  （Docker Lean 后端），用只读挂载和 `--network none` 隔离验证证书；这是当前默认 Lean 执行后端。
- `src/math_distill_stage2/counterexample/assets.py` - counterexample asset
  exporter（反例资产导出器），把已验证反例索引转换为全局资产目录。
- `src/math_distill_stage2/counterexample/verifier.py` - counterexample asset
  verifier（反例资产验证器），批量验证 `data/assets/counterexamples/.../certificate.lean`
  并刷新索引状态。
- `src/math_distill_stage2/counterexample/evidence.py` - counterexample evidence
  bank builder（反例证据库构建器），从已验证反例资产生成 offline analysis
  JSONL（离线分析 JSONL）；这是 cheatsheet 优化材料，不是 evaluator 运行时输入。
- `scripts/data/download_public_data.py` - reproducible bounded source downloader.
- `scripts/data/build_problem_index.py` - public selected-problem index builder.
- `scripts/data/build_dataset_splits.py` - deterministic train/dev/test dataset
  splitter（确定性训练/开发/测试集划分命令行入口）。
- `scripts/data/build_etp_result_index.py` - ETP proven-result index builder.
- `scripts/data/analyze_public_coverage.py` - public coverage analysis.
- `scripts/lean_certificates/generate_lean_smoke_certificates.py` - smoke certificate generator.
- `scripts/public_eval/run_public_eval.py` - public evaluation harness CLI（公开集实验编排器命令行入口）；
  写入 `artifacts/runs/<run_id>/`，可通过 `--countermodels` 接入本地反模型库。
- `scripts/counterexample/search_countermodels.py` - finite magma countermodel search CLI
  （有限岩浆反模型搜索命令行入口）；读取 public eval 的未覆盖负例并写入
  `artifacts/runs/<run_id>/`。
- `scripts/counterexample/generate_countermodel_certificates.py` - countermodel Lean certificate
  generator CLI（反模型 Lean 证书生成命令行入口）；从 `countermodels.jsonl`
  生成单个证书和 `batch.lean`。
- `scripts/counterexample/build_verified_counterexample_index.py` - verified counterexample index
  CLI（已验证反例索引命令行入口）；生成 `verified_counterexamples.jsonl`。
- `scripts/counterexample/export_counterexample_assets.py` - counterexample asset exporter
  CLI（反例资产导出命令行入口）；把已验证反例索引转换为全局资产目录。
- `scripts/counterexample/verify_counterexample_assets.py` - counterexample asset verifier
  CLI（反例资产验证命令行入口）；当前使用 Docker backend。
- `scripts/counterexample/build_counterexample_evidence_bank.py` - counterexample evidence bank
  CLI（反例证据库命令行入口）；输出用于离线分析和 cheatsheet 优化的 JSONL。
- `scripts/evaluator/run_stage2_smoke.py` - Stage 2 evaluator smoke flow（评估器冒烟流程），
  默认用测试集前 5 题、`cheatsheets/smoke/current/` 英文运行版 cheatsheet 和 Docker Lean 4 verification 验证真实流程；
  LLM request timeout（请求超时）默认 `180s`，并默认关闭失败重跑以保持快速反馈。
- `scripts/error_analysis/analyze_stage2_run.py` - Stage 2 run failure analysis CLI（失败分析命令行入口），
  核心逻辑在 `src/math_distill_stage2/error_analysis/`。
- `scripts/data/sync_zulip_channel.py` - Zulip channel sync CLI（Zulip 频道同步入口），
  保存 `data/raw/references/zulip/` 快照，并为 `docs/zulip-digests/` 摘要提供输入。
- `scripts/cheatsheets/create_draft_cheatsheet.py` - cheatsheet draft snapshot CLI（提示表 draft 快照命令行入口），
  把 `cheatsheets/<stage>/current/` 固定到 `cheatsheets/<stage>/drafts/<draft-id>/`，用于评测前快照和实验绑定。
- `scripts/cheatsheets/version_cheatsheet.py` - cheatsheet version snapshot CLI（提示表版本快照命令行入口），
  把已评测 draft 和指标快照发布到 `cheatsheets/<stage>/versions/<version>/`。
- `cheatsheets/smoke/current/` - smoke 工作态 cheatsheet，包含英文运行版、中文复查版和 `manifest.json`。
- `cheatsheets/smoke/drafts/` - smoke 评测前从 `current/` 生成的只读实验快照。
- `cheatsheets/mini/current/` - mini 工作态 Stage 2 evaluator cheatsheet，
  用于 train/dev mini 和候选迭代，包含英文运行版、中文复查版和 `manifest.json`。
- `cheatsheets/mini/drafts/` - mini 评测前从 `current/` 生成的只读实验快照，
  用于把 run、指标和 accept/reject 决策绑定到具体 prompt 快照。
- `cheatsheets/mini/versions/` - 重要 cheatsheet 候选版本快照和 `manifest.json`。
- `.env` - local evaluator env（本地评估器环境变量），当前包含 mass zhangkang endpoint
  使用的 dummy API key（占位接口密钥）。

## Docker Images

- `docker/lean4-executor/Dockerfile` - Lean 4 executor image（Lean 4 执行镜像）；
  当前默认安装 `leanprover/lean4:v4.29.1`，用于本地 Docker 验证并为后续
  Kubernetes Pod 迁移保留一致入口。

## Smoke Certificates

- `certificates/smoke/positive_equation2_implies_equation3.lean`
- `certificates/smoke/positive_path_equation2_implies_equation8.lean`
- `certificates/smoke/negative_equation23_not_implies_equation39.lean`

All three were checked with:

```bash
cd external/equational_theories
lake build equational_theories.Subgraph
lake env lean /abs/path/to/certificate.lean
```

## Verification

Run:

```bash
pytest -q
python scripts/data/download_public_data.py
python scripts/data/build_problem_index.py
python scripts/data/build_dataset_splits.py
python scripts/data/build_etp_result_index.py
python scripts/data/analyze_public_coverage.py
python scripts/lean_certificates/generate_lean_smoke_certificates.py
python scripts/public_eval/run_public_eval.py
python scripts/counterexample/search_countermodels.py --max-order 2 --max-problems 20
python scripts/public_eval/run_public_eval.py --countermodels artifacts/runs/<countermodel-run>/countermodels.jsonl
python scripts/counterexample/generate_countermodel_certificates.py --countermodels artifacts/runs/<countermodel-run>/countermodels.jsonl
python scripts/counterexample/build_verified_counterexample_index.py --countermodels artifacts/runs/<countermodel-run>/countermodels.jsonl --certificate-run artifacts/runs/<certificate-run>
python scripts/counterexample/export_counterexample_assets.py --verified-counterexamples artifacts/runs/<certificate-run>/verified_counterexamples.jsonl --run-id <asset-run-id>
docker build --network host -t lean4:v4.29.1 docker/lean4-executor
python scripts/counterexample/verify_counterexample_assets.py --root data/assets/counterexamples --run-id <asset-run-id> --backend docker --workers 6 --timeout-seconds 60
python scripts/counterexample/build_counterexample_evidence_bank.py --output artifacts/runs/<run-id>/counterexample_evidence.jsonl
python scripts/evaluator/run_stage2_smoke.py
python scripts/evaluator/run_stage2_evaluator.py --dataset data/processed/splits/test.jsonl --cheatsheet cheatsheets/mini/current/stage2_judge_json_certificate.en.md --max-concurrency 32 --failed-rerun-concurrency 4 --run-dir artifacts/runs/<evaluator-run>
```
