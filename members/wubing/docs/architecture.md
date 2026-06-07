# 项目架构设计

更新时间：2026-05-21

## 目标

本项目面向 SAIR Mathematics Distillation Challenge - Equational Theories - Stage 2，当前目标是构建可提交的官方 Solo `solver.py`：

- 输入官方 runner 发送的单题 JSON。
- 如果 `Equation 1` 蕴含 `Equation 2`，输出 Lean 4 可验证的 proof certificate（证明证书），并通过 judge call 提交：
  `{"call": "judge", "verdict": "true", "code": "<Lean code>"}`。
- 如果不蕴含，输出 Lean 4 可验证的 finite magma counterexample certificate（有限岩浆反例证书），并通过 judge call 提交：
  `{"call": "judge", "verdict": "false", "code": "<Lean code>"}`。
- 一个问题被视为 solved（已解决），当且仅当官方 deterministic Lean judge（确定性 Lean 评测器）返回 `accepted`。
- 官方当前规则没有明文要求每题必须调用 LLM。LLM fallback 只能产出候选 certificate，得分边界仍然是官方 judge 的 `accepted`。
- 官方 `solver.py` 大小限制以 `500000` bytes 为当前硬约束。
- 2026-05-21 Zulip 讨论线索显示 order 5 implications（5 阶等式蕴含）会进入 final evaluation（最终评测），具体比例仍待官方最终决定；因此 order5 deterministic coverage（5 阶确定性覆盖）继续作为 solver 优先方向。

## 当前架构

项目当前分为八层：

1. 数据快照层
   - `data/raw/` 保存官方和公开来源的本地快照。
   - `scripts/data/download_public_data.py` 负责可复现下载。
   - `data/raw/references/zulip/` 保存外部讨论快照；`docs/zulip-digests/` 保存人工可读摘要。

2. 规范化索引层
   - `src/math_distill_stage2/equations.py` 解析 magma equation（岩浆等式），并生成 canonical signature（规范签名）。
   - `scripts/data/build_problem_index.py` 生成公开问题索引。
   - `scripts/data/build_dataset_splits.py` 从公开问题索引生成 deterministic train/dev/test split（确定性训练/开发/测试集划分）。
   - `scripts/data/build_etp_result_index.py` 从 ETP `full_entries.json` 提取 implication（蕴含）和 fact/countermodel（事实/反模型）索引。

3. 图搜索和覆盖率层
   - `src/math_distill_stage2/implication_graph.py` 提供 implication graph（蕴含图）的路径搜索和事实查找。
   - `scripts/data/analyze_public_coverage.py` 统计公开集覆盖率。
   - baseline 公开集结果：正例 `819/819` 有 ETP 路径覆盖；负例 `60/850` 有直接有限反例覆盖。
   - 接入 size-2 本地反模型后，负例合并覆盖为 `498/850`，剩余 `352` 个负例未覆盖。

4. 证书生成层
   - `src/math_distill_stage2/lean_certificates.py` 生成 Lean smoke certificate（冒烟证书）。
   - `scripts/lean_certificates/generate_lean_smoke_certificates.py` 生成正例直接证明、正例路径组合证明、负例 `Fin 2` 反例证书。
   - `src/math_distill_stage2/counterexample/finite_magma.py` 和 `src/math_distill_stage2/counterexample/search.py` 已能枚举小阶 finite magma 并输出反模型搜索产物。
   - `scripts/counterexample/generate_countermodel_certificates.py` 已能把 `countermodels.jsonl` 转换为 Lean `Fin n` 反例证书和合并验证文件。
   - `scripts/counterexample/build_verified_counterexample_index.py` 已能把公开问题、Python 反模型、Lean 证书路径、证书哈希和 Lean 验证状态关联成 `verified_counterexamples.jsonl`。
   - `src/math_distill_stage2/counterexample/evidence.py` 和 `scripts/counterexample/build_counterexample_evidence_bank.py` 已能把全局反例资产压缩成 offline analysis（离线分析）可用的 JSONL evidence bank（证据库），不作为 evaluator 运行时输入。
   - 官方 judge 当前把 solver 输出的 Lean `code` 作为完整 `Submission.lean` 原样编译，再检查 `example : Goal := submission`；因此 certificate generator（证书生成器）可以在主 `submission` 前生成 helper `theorem`、`def`、`lemma`、`namespace` 或 `notation`，但仍必须满足 proof policy（证明策略）和大小预算。

5. Lean 执行与验证层
   - `src/math_distill_stage2/lean_executor/` 定义 Lean executor（Lean 执行器）包。
   - `src/math_distill_stage2/lean_executor/base.py` 定义 `LeanTask`、`LeanExecutor` 和 `LeanExecutionResult`。
   - `src/math_distill_stage2/lean_executor/docker.py` 支持用本地 Docker 隔离执行 Lean 4 证书，默认镜像来自 `src/math_distill_stage2/docker_images.py` 的官方 Stage 2 judge 镜像常量。
   - `src/math_distill_stage2/counterexample/verifier.py` 面向 `data/assets/counterexamples/<problem_key>/runs/<run_id>/certificate.lean` 批量验证并刷新 `verification.json`、`latest.json`、`index.jsonl`、`summary.json`。
   - `docker/official-stage2-judge/Dockerfile` 固定官方 judge/evaluation 仓库 commit 和 Lean toolchain。

6. 外部验证层
   - `external/equational-theories-lean-stage2/` 是官方 Stage 2 judge/evaluation 仓库的期望本地路径；当前目录有官方文件树但不是 git clone，规则事实以 `data/raw/references/stage2_judge/` 快照和远端 HEAD 核对为准。
   - `src/math_distill_stage2/official_stage2_judge.py` 封装官方 `judge/verify.py`。
   - `src/math_distill_stage2/official_stage2_batch.py` 提供 Docker-only 批量验证，以及 judge-v2 远程批量证书校验客户端。
   - Stage 2 official judge（官方验证器）批量预检默认走 judge-v2 control：`http://10.220.69.172:8890`。证书校验调用 `/jobs` 或 `/verify`，由 control 调度 worker；Lean certificate 远程校验不设置 legacy fallback。

7. 官方 Solo solver 层
   - `submissions/solo_official/solver.py` 是唯一官方提交文件；`submissions/solo_official/` 目录必须只包含这一份普通文件。
   - `solvers/solo_official/current/solver.py` 是当前工作态 solver。
   - `solvers/solo_official/drafts/YYYY-MM-DD/dN/` 保存候选草稿，每个目录包含 `solver.py`、`manifest.json`、`notes.md` 等必要记录。
   - `solvers/solo_official/versions/YYYY-MM-DD/vN/` 保存已晋升版本；禁止覆盖已有版本。
   - 官方 runner 产物会保存 `solver_snapshot.json`，并把提交副本放在 `artifacts/runs/YYYY-MM-DD/<run-id>/submission/solver.py`，用于复现当次评测。
   - `stage2-train-version-solver` 负责 promote、rollback、同步 `submissions/solo_official/solver.py`，以及校验版本哈希、accepted rate（通过率）和 manifest。

8. 实验闭环与技能层
   - public eval harness MVP 已完成，入口是 `scripts/public_eval/run_public_eval.py`。
   - countermodel search MVP 已完成，入口是 `scripts/counterexample/search_countermodels.py`。
   - 官方 Solo runner 入口是 `scripts/evaluator/run_official_solo_history.py` 和 `scripts/evaluator/run_official_solo_history_parallel.py`。
   - Stage 2 run failure analysis（运行失败分析）核心逻辑在 `src/math_distill_stage2/error_analysis/`；CLI 是 `scripts/error_analysis/analyze_stage2_run.py`。CLI 只负责参数解析和落盘，分类规则、taxonomy（分类表）和 Markdown 报告渲染属于 `src` 业务逻辑。
   - proof bank（证明库）相关业务逻辑在 `src/math_distill_stage2/proof_bank/`，CLI 在 `scripts/lean_certificates/proof_bank_*.py`。
   - 仓库根目录 `skills/` 保存 `stage2-*` 项目私有技能；这些技能负责编排评测、失败分析、solver 改进、proof bank 离线生成、报告和外部信息同步，不替代可复现 harness 的确定性执行职责。
   - `stage2-info-competition` 负责官方页面、API 和 judge/evaluation 仓库快照同步；`stage2-info-zulip-channel` 负责外部讨论同步；`stage2-train-version-solver` 负责 solver 版本生命周期。

## LLM 执行约定

当前 `solver.py` 可以把 LLM 作为 fallback：

- base URL（接口地址）：mass zhangkang OpenAI-compatible endpoint。
- model（模型）：`gemma-4-31b`。
- temperature（采样温度）：`0`。
- API key（接口密钥）读取顺序：`CLIPROXYAPI_API_KEY`，然后 `OPENAI_API_KEY`。
- LLM 输出不能绕过 judge；只有官方 runner 返回 `accepted` 才算 solved。

示例命令：

```bash
python scripts/evaluator/run_official_solo_history.py \
  --suite dev_fast \
  --run-id <run-id>

python scripts/error_analysis/analyze_stage2_run.py \
  --run-dir artifacts/runs/<run-id>

python scripts/lean_certificates/verify_official_stage2_batch.py \
  --input artifacts/runs/<candidate-run>/candidate_answers.jsonl \
  --output artifacts/runs/<candidate-run>/official_verify.jsonl \
  --summary artifacts/runs/<candidate-run>/official_verify.summary.json \
  --artifact-dir artifacts/runs/<candidate-run>/official_stage2_judge \
  --image math-distill-stage2-official-judge:official-6805e23 \
  --max-workers 2 \
  --resume
```

## 计划中的目标架构

下一阶段需要把当前工具链收敛成可提交 solver：

1. 正例证明管线
   - 输入规范签名，映射到 ETP equation id。
   - 在压缩后的 implication graph 中查找证明路径。
   - 将路径转换为 Lean theorem composition（定理组合）证书。
   - 批量验证公开集正例。

2. 负例反模型管线
   - 对未覆盖负例搜索小阶 finite magma（有限岩浆）。
   - 找到满足 `Equation 1` 且不满足 `Equation 2` 的运算表。
   - 生成 pure Lean 4 `Fin n` counterexample certificate（纯 Lean 4 反例证书），不依赖 `mathlib` 或 `equational_theories`。
   - 建立全局 counterexample asset dataset（反例资产数据集），每个问题目录保存 `problem.json`、`latest.json` 和多轮 run 结果。
   - 用 Docker Lean executor（Docker Lean 执行器）批量验证资产证书，后续迁移到 Kubernetes Pod。

3. LLM certificate / evaluator 闭环
   - 本地解析器只做 minimal extraction/schema validation（最小抽取/结构校验），检查 `verdict`、Lean 片段和必要元数据。
   - 模型返回的证明是候选 certificate（证书）材料；正式提交仍以官方 judge 结果为准。
   - 格式失败或请求失败可以 rerun（重跑）同一问题；rerun 仍必须重新调用模型。

4. 提交封装
   - 暴露官方要求的 Python solver 输入/输出接口（待官方 judge 仓库进一步确认）。
   - 将模型输出的 judge call JSON 原样转交官方 judge，前提是通过最小 schema 校验。
   - 禁止依赖网络和大型本地原始文件。
   - 将必要图数据、方程映射和反模型数据压缩到官方大小限制内。

5. 实验闭环 harness
   - 提供统一入口运行公开集、子集、holdout slice（保留评测切片）或指定失败样例。
   - 每轮输出 `manifest.json`、`metrics.json`、`predictions.jsonl`、`errors.jsonl`、`analysis.md`、`decision.json` 等可复现产物。
   - 支持多轮 loop（循环）：评测 baseline，挖掘错误，调用可替换 strategy 生成 proposal（改进提案），构建候选版本，复评，按门槛 accept/reject（接受/拒绝），再进入下一轮。
   - Solver candidate（求解器候选）必须落盘版本快照和指标快照；test baseline（测试集基线）只在候选冻结后运行，避免用 test split 调参。
   - 自动循环必须有停止条件，例如最大轮数、最大耗时、连续无提升轮数、体积上限、Lean 验证通过率和 holdout 不回归要求。

## 当前最高优先级

1. 保持 `submissions/solo_official/solver.py` 可提交、可复现、低于大小限制，并确保提交目录只有这一份文件。
2. 用官方 Solo runner 跑 `dev_fast`、`dev_main`、`test_locked`，持续分析失败样例。
3. 通过 `stage2-train-improve-solver` 小步改进确定性模板和 fallback 逻辑。
4. 通过 `stage2-train-version-solver` 管理草稿、晋升版本、回滚和官方提交目录同步。
5. 通过 proof bank 离线积累 accepted true certificate，再明确转化为 solver template 或 focused test。
6. 持续跟踪官方 Stage 2 judge（评测器）细节和 Zulip 讨论，一旦规则变化立即适配。

## 架构迭代规则

- `docs/architecture.md` 记录“当前采用的架构”，需要随着实现变化直接更新。
- 每次实验探索写入 `docs/experiments/`，尤其是负例搜索覆盖率、Lean 验证耗时、压缩率和失败样例。
- 自动化实验的原始产物写入 `artifacts/runs/YYYY-MM-DD-HHMMSS-短名称/`；`docs/experiments/` 只保存人类可读的结论和下一步。
- 多轮自动实验中，harness 负责确定性执行和复评，skill/strategy 负责可替换的错误分析与改进建议；两者通过落盘文件通信。
- 如果文档与代码不一致，优先相信代码和最新可复现实验结果，然后更新文档。
