# AGENTS.md - Math Distill Stage 2

本文件是本项目的本地会话级工作规则。上级工作区规则仍然有效；如果有冲突，以本文件中更具体、与本项目直接相关的规则为准。

本文件只保留长期稳定、每次进入仓库都应生效的规则。具体到 Stage 2 solver 工作流的步骤、目录职责、输入输出和禁止行为，以仓库内 `skills/stage2-*/` 和 `docs/architecture.md` 为准。

## 工作根目录

- 本项目当前作为团队 monorepo 的个人工作区存在，个人工作根目录是 `members/wubing/`。
- 本目录内的 `skills/`、`docs/`、`scripts/`、`src/`、`data/`、`external/`、`solvers/` 和 `submissions/` 路径，除非另有说明，都相对 `members/wubing/` 解释。
- 如果 shell 当前在 monorepo 根目录 `math-distill-equational-stage2/`，运行本项目命令前先 `cd members/wubing`，或把工具的 `workdir` 设为 `members/wubing/`。
- 根目录的公共 `docs/`、`datasets/`、`solvers/` 是团队公共区；不要把个人工作区命令误跑到 monorepo 根目录。

## 文档语言

- 本项目新增文档默认使用中文。
- 必须保留英文术语时，第一次出现尽量写成“英文术语（中文解释）”或“中文解释（English term）”。
- 引用官方接口、代码符号、文件名、命令、Lean theorem 名称时，可以直接使用英文或原文。

## 项目目标

- 当前目标是构建可提交的 Stage 2 官方 Solo `solver.py`。
- 官方当前规则要求每题输出 Lean 4 可验证 certificate（证书），没有明文要求每题必须调用 LLM。
- mass zhangkang 的 `gemma-4-31b` chat endpoint 当前可用于本地 LLM 实验；LLM fallback 仍必须以官方 judge 验证 certificate 为得分边界。
- 输出目标是可提交、可复现、Lean 4 可验证的 judge JSON certificate（评测 JSON 证书）闭环。

## 技能优先原则

- 涉及“start train”“继续训练”“持续推进”“不再逐步询问下一步”等自主 Stage 2 Solo solver 迭代闭环时，优先使用：
  - `stage2-train-start`
- 涉及 Stage 2 官方 solver 评估、run 分析、solver 改进时，优先使用仓库内以下技能：
  - `stage2-train-evaluate`
  - `stage2-train-analyze-run`
  - `stage2-train-improve-solver`
  - `stage2-train-offline-explore-solver`
  - `stage2-train-proof-seed`
- 涉及 solver `current`、`drafts`、`versions`、promote、rollback 或同步到官方提交目录时，优先使用：
  - `stage2-train-version-solver`
- 涉及比赛规则、官方页面/API、官方 judge/evaluation 仓库和本地 `data/raw/references/` 快照更新时，优先使用：
  - `stage2-info-competition`
- 涉及 Stage 2 Solo baseline 简报、版本对比报告、领导/团队沟通材料时，优先使用：
  - `stage2-report-solver-baseline`
- 涉及用户要求把指定文件、报告、实验产物或目录同步到 wubing 交接目录时，优先使用：
  - `stage2-sync-wubing-files`
- 涉及 Stage 2 strategy registry 的总入口、继续推进、下一步，或需要在“继续探索下一个策略”和“生成当前 registry 报告”之间分流时，优先使用：
  - `stage2-strategy-start`
- 涉及并行挖掘 true/false 确定性策略、9 亿级 residual 缩减、总控 session、候选落盘文档或新开 true/false session 时，优先使用：
  - `stage2-strategy-start`
  - `stage2-strategy-mine-true-template`
  - `stage2-strategy-mine-false-predicate`
- 涉及系统性挖掘 finite model setcheck 策略、枚举有限运算表、按 current union increment 排序、选择下一个 `false.finmodel.setcheck.*` 候选时，优先使用：
  - `stage2-strategy-mine-setcheck`
- 涉及挖掘 `true.proof.templatecheck.*`、singleton/product/projection/law-instance true 模板、top shape bucket 的 true deterministic coverage，且不立即修改 `solver.py` 时，优先使用：
  - `stage2-strategy-mine-true-template`
- 涉及从 paircheck bank、finite-model hits 或 shape bucket 反推 `false.finmodel.predicatecheck.*`，且不立即修改正式 registry 时，优先使用：
  - `stage2-strategy-mine-false-predicate`
- 涉及 Stage 2 strategy registry、order5 策略覆盖、finite model setcheck/paircheck/predicatecheck、coverage union/conflict/canonical priority、策略探索或 registry JSON 更新，且不立即修改 `solver.py` 时，优先使用：
  - `stage2-strategy-explore`
- 涉及 Stage 2 strategy registry 覆盖报告、active strategy 简报、soundness evidence 汇总、coverage delta 或下一策略建议时，优先使用：
  - `stage2-strategy-report`
- 涉及离线使用 Codex/GPT 生成、验证、保存 Stage 2 true Lean certificate 到全局 proof bank，且不立即修改 `solver.py` 时，优先使用：
  - `stage2-proofbank-start`
  - `stage2-proofbank-nightly-loop`
  - `stage2-proofbank-sample-candidates`
  - `stage2-proofbank-generate-true-certificate`
  - `stage2-proofbank-verify-import`
  - `stage2-proofbank-maintain`
  - `stage2-proofbank-quality-audit`
- `stage2-proofbank-*` 技能只负责离线 certificate attempt bank（证书尝试库）的生成、验证和维护；不等同于 solver 训练闭环。只有用户明确要求把 accepted certificate 转化为 solver template、focused test 或版本提升时，才切换到 `stage2-train-*`。
- `stage2-strategy-*` 技能只负责离线 strategy registry（策略注册表）的探索、验证和报告；不等同于 solver 训练闭环，也不等同于 proof bank 证书生成。并行 true/false 挖掘时，子 session 默认只写 `data/processed/order5_strategy_registry/candidates/` 候选产物，正式 registry 合并由总控 session 处理。
- proof bank 相关项目私有技能统一使用 `stage2-proofbank-` 前缀；不要和 `stage2-train-proof-seed` 混用。
- 如果当前任务没有合适技能，或现有技能无法安全覆盖任务边界，必须先反馈人工并等待确认。
- 如果后续出现稳定重复的 Stage 2 工作流，但现有技能无法覆盖，应优先补充新的 `stage2-*` 项目技能，再扩大使用范围。
- 比赛相关项目私有技能统一使用 `stage2-` 前缀；新建或重命名技能优先采用 `stage2-<领域>-<动作>`，例如 `stage2-train-*` 表示 solver 训练/评估闭环，`stage2-report-*` 表示人工触发的沟通报告，`stage2-info-*` 表示官方信息和外部讨论同步。
- 不要在普通 solver 迭代中顺手批量重命名技能；技能目录名、frontmatter `name`、`agents/openai.yaml`、文档引用和历史触发词必须作为单独迁移一起处理。

## 代码组织

- 可测试业务逻辑放在 `src/math_distill_stage2/`。
- 官方 Solo 提交只放在 `submissions/solo_official/solver.py`；该目录必须只有这一份普通文件。
- `scripts/` 只放命令行入口；根目录不再放真实命令脚本。
- 命令入口按 `src/math_distill_stage2/` 的业务边界分层：
  - `scripts/evaluator/`
  - `scripts/error_analysis/`
  - `scripts/counterexample/`
  - `scripts/data/`
  - `scripts/lean_certificates/`
  - `scripts/public_eval/`
- 新增脚本必须放入对应子目录；不要在 `scripts/` 根目录新增兼容入口。
- 不提交 `__pycache__`、大型原始数据或不可压缩大表；官方 `solver.py` 大小限制以 `500000` bytes 为当前硬约束。

## 文档位置

- `docs/README.md`：文档索引和写作规范。
- `docs/architecture.md`：当前项目架构设计，是持续更新的活文档；架构相关内容统一维护在这里，不新增分散的架构说明文档。
- `docs/experiments/`：探索实验记录。
- `docs/reports/`：面向领导和团队沟通的短报告。
- `docs/superpowers/`：保留自动化规划、设计和实施计划文档。

## 验证要求

- 修改 `solver.py` 前先补 focused test（聚焦测试），再实现。
- 修改代码后优先运行相关测试。
- 文档变更至少检查路径、命令和链接是否准确。
- Stage 2 official judge（官方验证器）或 Lean certificate（证书）批量预检必须使用远程 judge backend；默认使用 `remote-http`/`remote-judge-v2` 指向 `http://10.220.69.172:8890` 的 judge-v2 control 服务。certificate 校验不设置 legacy fallback；大量证书校验优先走 judge-v2 `/jobs`。
- 本机硬件资源有限，不再把本地 Docker/Lean judge 作为默认或优先验证路径；除非用户单独明确要求排查本地环境问题，否则不要发起本地批量 judge/Lean 预检。
