# Stage 2 比赛要求分析

更新时间：2026-05-21

## 2026-05-21 官方页面/API 快照

本次已重新抓取 Stage 2 overview 页面和公开 API，并落盘到：

- `data/raw/references/sair_api/competition_stage2_overview.html`
- `data/raw/references/sair_api/competition_stage2_overview_bootstrap.json`
- `data/raw/references/sair_api/competition_stage2.json`
- `data/raw/references/sair_api/competitions.json`
- `data/raw/references/stage2_judge/README.md`
- `data/raw/references/stage2_judge/rules/overview.md`
- `data/raw/references/stage2_judge/rules/evaluation.md`
- `data/raw/references/stage2_judge/docs/solo_mode.md`
- `data/raw/references/stage2_judge/docs/marathon_mode.md`
- `data/raw/references/stage2_judge/judge/verify.py`
- `data/raw/references/stage2_judge/pipeline/config.json`
- `data/raw/references/stage2_judge/lean-toolchain`
- `data/raw/references/stage2_judge/main_commit.json`

当前官网页面嵌入的 bootstrap JSON 与 API 字段一致，核心变化是：

- `updatedAt`: `2026-05-05T05:53:44Z`（Asia/Shanghai: `2026-05-05 13:53:44`）
- `participantCount`: `170`（2026-05-18 本地记录为 `165`；2026-05-13 本地记录为 `151`）
- `pythonMaxBytes`: `512000`
- `cheatsheetMaxBytes`: `512000`
- `allowDraftSubmissions`: `false`
- `leaderboardPublished`: `false`
- `playgroundEnabled`: `true`
- `publicCodePrefix`: `EQT02`

页面描述明确写出：pre-registration（预注册）在 `2026-04-23` 开放，Stage 2 在
`2026-05-01 12:00 UTC` 正式开始，提交截止为 `2026-08-31 23:59 AoE`。API 字段中
`submissionDeadline=2026-09-01T11:59:59Z`，换算为 Asia/Shanghai 是
`2026-09-01 19:59:59`。

当前 API 的 `details` 仍为 `null`，`startTime` 仍为 `null`，但渲染后的官网
overview 已公开 official Stage 2 judge/evaluation repository（官方 Stage 2 评测/评测器仓库）：

- <https://github.com/SAIRcompetition/equational-theories-lean-stage2>
- main commit: `6805e2323018fbd8a85f41ca09fc33d74d5a02a5`
- commit time: `2026-05-03T00:20:28Z`
- local official repo path: `external/equational-theories-lean-stage2/`

2026-05-21 核对时，`external/equational-theories-lean-stage2/` 目录存在官方仓库文件树但不是 git clone（缺少 `.git`），因此没有覆盖该目录；`git ls-remote` 显示远端 `main` 仍为 `6805e2323018fbd8a85f41ca09fc33d74d5a02a5`。本次规则事实以 `data/raw/references/stage2_judge/` 中从官方 raw/API 重新下载的快照为准。

官方仓库当前 commit message 说明 solver sandbox（求解器沙箱）在 `python:3.11-slim`
基础上额外批准 `sympy==1.13.3` 作为第三方包。官方 README 和 Solo/Marathon
文档同时明确：除标准库和批准列表外，没有 `numpy`、`z3`、`networkx` 等包；如需新增包，应向官方开 issue 说明用例。

官方仓库确认 Stage 2 提交形态是单文件 `solver.py`，并分为 Solo 和 Marathon 两个
track（赛道）。公开页面和 `rules/evaluation.md` 仍标注部分 scoring/model/problem-set
细节 TBD（待定），需要持续跟踪。

## Stage 2 最新 Core Task

根据 Stage 2 overview 页面，Stage 2 已明确从 Stage 1 的 true/false prediction（真假判断）升级为 certificate-producing solver（证书生成求解器）任务。

核心任务：

- 输入一对等式 `Equation 1` 和 `Equation 2`。
- 如果 implication（蕴含）为 **true**：输出 Lean 4 proof（Lean 4 证明），证明 hypothesis equation（前提等式）蕴含 goal equation（目标等式）。
- 如果 implication（蕴含）为 **false**：输出 Lean 4 proof certificate（Lean 4 证明证书），也就是 finite magma witness（有限岩浆见证），证明存在一个满足前提但不满足目标的 magma。
- 两种方向都必须是 machine-verifiable certificate（机器可验证证书）。
- deterministic Lean judge（确定性 Lean 评测器）负责接受或拒绝每个答案。

Stage 2 页面描述的 answer format（答案格式）是 solver 通过 judge call 提交证书：

```json
{ "call": "judge", "verdict": "true", "code": "<Lean code>" }
```

或：

```json
{ "call": "judge", "verdict": "false", "code": "<Lean code>" }
```

`code` 字段必须是可被 Lean 4 judge 验证的代码。一个问题被解决，当且仅当 judge 返回 `accepted`。

## LLM 调用规则口径修正

2026-05-06 重新核对官方 `rules/evaluation.md`、`docs/solo_mode.md` 和 README 后，需要修正 2026-04-29 的旧工作假设：官方当前规则没有明文要求每题必须调用 `gpt-oss-120b` 或任何 LLM。

官方规则的关键口径是：

- Stage 2 的得分边界是 Lean 4 certificate（证明证书/反例证书）能否被 deterministic Lean judge 接受。
- `rules/evaluation.md` 使用条件句 “If the solver uses LLM calls in Solo”，说明 LLM 是可用资源而不是必选项。
- `docs/solo_mode.md` 写的是 solver “may issue” 任意数量的 `judge` 和 `llm` requests。
- 官方 README 把 baseline demo 标成 sequential brute-force, no LLM（零 token 成本），并列出 deterministic counterexample, no LLM needed 的示例路径。

因此，本项目不再把“每题必须调用 `gpt-oss-120b`”记录为全局硬约束。后续 solver 设计应同时允许：

- deterministic certificate generator（确定性证书生成器）：本地搜索、图路径、反模型表和 Lean 代码生成后，直接通过官方 judge 验证。
- LLM-mediated certificate generator（大模型辅助证书生成器）：用当前本地默认 `gemma-4-31b` 或官方最终指定模型生成/补全候选 Lean certificate，再交给 judge 验证。

如果某次实验继续采用 LLM-output-as-certificate（模型输出即证书）闭环，仍必须在 run 配置和实验记录中明确标成实验策略；模型返回的 `verdict` 和 `code` 不应在 LLM 调用后做语义修复、模板替换、确定性渲染或查表改写。这个限制只约束该实验流，不是官方比赛对所有 solver 的硬规则。

## Judge 状态和 Proof Policy

Stage 2 页面列出的 judge status（评测状态）：

- `accepted`：证书验证成功。
- `unparsed`：原始 JSON 无法解析。
- `malformed`：JSON 可解析，但不符合 schema（结构约束）。
- `incomplete_proof`：proof 使用了 `sorry`、`admit` 或被禁止的 axiom/declaration。
- `incorrect`：proof 结构有效，但 Lean 无法验证。

Stage 2 页面列出的 proof policy（证明策略限制）：

- Allowed trusted axioms（允许的可信公理）：`propext`、`Quot.sound`、`Classical.choice`。
- Allowed declarations（允许声明）：按问题配置 allowlist（如果指定）。
- 使用 `sorry`、`admit` 或 disallowed axioms/declarations（被禁止公理/声明）的证明会被判为 `incomplete_proof`。

2026-05-12 追加同步 Zulip 频道 `Math Distillation Challenge - equational theories` 后，message `2057` 给出 Lean tactics 的实务口径：提交证明可以使用标准 Lean 4 / Mathlib tactics，例如 `simp`、`grind`、`omega`、`aesop`、`decide`；judge policy 的边界是 elaborated proof（展开后证明）的 axiom/declaration 依赖，而不是 tactic 名称本身。此信息来自 Zulip 讨论，仍应以官方 judge 实现为权威边界。

当前 `data/raw/references/stage2_judge/judge/verify.py` 中的 `ProofPolicy` 明确包含 `allowed_axioms`、`allowed_declarations`、`allowed_declaration_prefixes`；`BANNED_PROOF_TOKENS` 覆盖 proof holes、debug output、elaboration-time IO/metaprogramming 和 unsafe/kernel-bypass constructs。结论：solver/proof generator 可以尝试 tactic-based certificate（基于 tactic 的证书），但每个候选仍必须通过官方 judge；若 tactic 展开后依赖不在 allowlist 内，仍会被拒绝。

2026-05-20 Zulip message `2097` 进一步说明 `code` 字段是 complete Lean file（完整 Lean 文件），不仅是 tactic body（tactic 主体）：可以在主证明之前声明 helper `theorem`、`def`、`lemma`、`namespace` 或 `notation`，但文件需要暴露顶层 `def submission : Goal := ...`，或一个类型与 `Goal` 匹配的 term。此条是 Zulip 讨论口径；权威实现以 `judge/verify.py` 为准。当前 `verify.py` 确认会把提交的 `code` 原样写成 `Submission.lean`，再在独立 judge 文件中检查 `example : Goal := submission`。

补充注意：`judge/verify.py` 代码内置默认值仍是 `MAX_CODE_LENGTH=50000`、`MAX_FALSE_CERT_BYTES=10000`，但官方 `pipeline/config.json` 和 Solo 文档传入的当前评测预算是 `max_code_length=100000`、`max_false_cert_bytes=20000`。本项目面向 official runner（官方运行器）时以 `pipeline/config.json` 的预算为准；单独调用 `judge/verify.py` 时应显式传入配置或设置环境变量，避免误用内置默认值。

## Solver Budget

Stage 2 官方仓库当前列出的资源预算：

| 资源 | 限制 | 来源/说明 |
| --- | ---: | --- |
| Solo wall-clock per problem | 3600 seconds | `rules/evaluation.md`、`docs/solo_mode.md`、`pipeline/config.json` |
| LLM max output tokens per call | 65536 | `rules/evaluation.md`、`pipeline/config.json` |
| Submitted Lean code | 100 KB / `100000` bytes | `docs/solo_mode.md`、`pipeline/config.json` |
| False certificate payload | 20 KB / `20000` bytes | `docs/solo_mode.md`、`pipeline/config.json` |
| Solver source | 500 KB / `500000` bytes | official repo `pipeline/config.json`; SAIR API 同时暴露 `pythonMaxBytes=512000` |

Solver runtime（求解器运行环境）当前批准的第三方 Python 包只有：

| Package | Version | 说明 |
| --- | --- | --- |
| `sympy` | `1.13.3` | 官方文档说明可用于 term parsing（项解析）、substitution（替换）、equation normalization（等式规范化）等符号处理；magma reasoning（岩浆推理）仍需注意非结合语义。 |

这意味着 solver（求解器）可以混合使用 deterministic strategies（确定性策略）、counterexample search（反例搜索）、pattern matching（模式匹配）、symbolic proof construction（符号证明构造）和 LLM calls（大模型调用）。但最终是否得分取决于 Lean judge 是否接受证书。

Marathon track（马拉松赛道）预算当前需特别标注一个官方文档内部不一致点：

- `rules/evaluation.md` 写成 `compression_ratio × N × 3600s`，N=100、默认 `0.5`
  时是 `180000s`。
- `README.md` 和 `docs/marathon_mode.md` 写成 Marathon per-problem reference
  `600s + 65536 tokens`，N=100、默认 `0.5` 时是 `30000s`。

后续适配 Marathon 时应以官方代码和最新文档再次核对，不能只硬编码其中一个数字。

## 当前本地 LLM 实验参数

本项目当前实验闭环使用 mass zhangkang OpenAI-compatible endpoint（OpenAI 兼容接口）调用 `gemma-4-31b`：

- base URL（接口根地址）：`http://60.171.65.125:30197/v1`
- model（模型）：`gemma-4-31b`
- seed（随机种子）：`0`
- temperature（采样温度）：`0`
- configured max output tokens（当前本地配置的最大输出 token）：`1024`
- stream（流式响应）：`true`
- LLM HTTP timeout（LLM HTTP 超时）：`60s`
- SDK retry（SDK 重试）：disabled（禁用）
- max concurrency（首轮最大并发）：`32`
- failed rerun concurrency（失败重跑并发）：`4`
- rerun（重跑）：支持；当前默认最多重跑 `1` 轮格式失败或请求失败样例。

注意：这里的 rerun 只表示重新调用同一 prompt，让模型重新输出 judge JSON；本地仍不修改模型返回的 `verdict` 或 `code`。

上下文窗口口径：

- 官方模型卡层面：Hugging Face `google/gemma-4-31B` 记录 `31B Dense` context length 为 `256K tokens`。
- 当前 mass 部署层面：2026-05-07 `sample200` opnorm 评估中，37 次 LLM 请求都被服务端拒绝，错误为 `max_tokens=65536` 超过 `max_model_len=max_total_tokens=20480`。同日服务重启后，`/v1/models` 返回 `max_model_len=65536`，但 `max_tokens=65536` 对非空 prompt 仍会失败，因为 prompt 本身也占用同一个上下文窗口。
- 因此不能把 `20480` 或 `65536` 记成 Gemma 4 31B 模型理论上下文窗口；它们只是不同时间点的 endpoint 部署限制。当前本地评估把 `max_output_tokens` 降为 `1024`，优先降低显存预留和排队/生成延迟。

官方 Stage 2 repo 当前 `pipeline/config.json` 中的 LLM 配置快照：

- model: `openai/gpt-oss-120b`
- provider: `deepinfra/bf16`
- max output tokens: `65536`
- temperature: `0.0`
- reasoning effort: `medium`
- seed: `0`

但 `rules/evaluation.md` 仍把 final evaluation model（最终评测模型）和最终 generation
parameters（生成参数）标为 TBD。因此，官方 raw 配置中的 `openai/gpt-oss-120b` 仍只能记录为当前候选/参考配置；`gemma-4-31b` 只保留为本项目本地 mass endpoint 实验配置，不记录为官方最终评测模型或项目全局的“每题必调”规则。

2026-05-18 Zulip 同步新增一个讨论线索：YZ 在 2026-05-15 messages `2072`、`2073`
中回复 Stage 2 final official eval（最终官方评测）问题，表示当前 planned model
tracks（计划模型赛道）是 `GPT-OSS-120B` 和 `Gemma-4-31B`，社区可建议新增模型，且
different models will be treated as separate tracks（不同模型作为独立赛道）。同一回复还说
Solo mode 每题独立评估；Marathon mode 当前建议 final evaluation 不超过 100 题，且由于
false implications 在 Stage 2 更容易，最终集预计包含更多 true implications。此信息仍是
Zulip 讨论上下文，官方页面/API 和 `rules/evaluation.md` 对 final evaluation
model/configuration/problem set 仍为 TBD（待定），不能作为提交硬约束。

2026-05-21 Zulip 同步新增两个与 official private test（官方私有测试集）组成相关的线索：

- message `2100`：YZ 明确表示 order 5 implications（5 阶等式蕴含）会包含在 final evaluation（最终评测）中。
- message `2101`：order 5 的确切比例仍取决于 community feedback（社区反馈）和 co-organizers（共同组织者）的最终决定。

这两条仍是 Zulip 讨论上下文；官方页面/API 和 `rules/evaluation.md` 对 evaluation problem sets（评测题集）仍写为 TBD。因此策略上应继续把 order5 deterministic coverage（5 阶确定性覆盖）作为高优先级，但不要把具体比例写死。

## 公开 API 当前元数据

Stage 2 overview 页面和 API 当前显示：

- competition id: `mathematics-distillation-challenge-equational-theories-stage2`
- status: `active`
- public code prefix: `EQT02`
- submission start: `2026-04-22T10:00:00Z`
- submission start in Asia/Shanghai: `2026-04-22 18:00:00`
- official start: `2026-05-01 12:00 UTC`
- deadline: `2026-09-01T11:59:59Z`
- deadline in Asia/Shanghai: `2026-09-01 19:59:59`
- `pythonMaxBytes`: `512000`
- `cheatsheetMaxBytes`: `512000`
- `allowDraftSubmissions`: `false`
- `playgroundEnabled`: `true`
- `leaderboardPublished`: `false`
- `participantCount`: `170`
- API/page `updatedAt`: `2026-05-05T05:53:44Z`
- official Stage 2 repo main commit: `6805e2323018fbd8a85f41ca09fc33d74d5a02a5`
- official Lean toolchain: `leanprover/lean4:v4.30.0-rc2`

注意：当前 API 的 `details` 仍为 `null`。截至 `2026-05-21` 抓取时，official repository 已公开 Python solver interface（Python 求解器接口）、local judge/harness（本地评测器/测试框架）和 demo solvers（示例求解器）；private evaluation set（私有评测集）、final scoring rules（最终计分规则）和 final evaluation model/configuration（最终评测模型/配置）仍为 TBD。

## 修正后的公开数据范围

The earlier "1200 public problems" wording came from Stage 1 launch material:
`normal=1000` plus `hard=200`.

The current released selected-problems dataset contains these public subsets:

- `normal`: 1000
- `hard`: 200
- `hard1`: 69
- `hard2`: 200
- `hard3`: 400

For this Stage 2 repo, the working public regression suite excludes `hard`
because it duplicates the older hard/hard1 slice in the current workflow. The
default public regression suite is:

- `normal`: 1000
- `hard1`: 69
- `hard2`: 200
- `hard3`: 400

Default total: 1669 rows.

## 策略影响

Stage 2 的核心不再是只优化 prompt 输出 `TRUE/FALSE`，而是构建 Lean certificate-producing solver（生成 Lean 证书的求解器）。Lean judge 是唯一得分边界；LLM、cheatsheet、反模型搜索和图搜索都只是生成候选 certificate 的手段。

当前最合理的方向是 hybrid certificate generator（混合证书生成器）：

1. Parse each input equation into a canonical form and map it to an ETP
   equation id.
2. 优先建设 deterministic certificate path（确定性证书路径）：implication graph（蕴含图）证明路径、finite magma counterexample（有限岩浆反例）、本地 proof/countermodel template（证明/反例模板）和官方 judge 自检。
3. 用 compact proof/countermodel bank（压缩证明/反模型库）做离线错误分析、提交压缩设计和 LLM prompt evidence（提示证据），但不再把它定义为只能服务于每题 LLM prompt。
4. LLM-mediated evaluator 继续用于证明补全、错误修复实验和 cheatsheet 迭代；这条路径需要解析模型输出的 judge call JSON：
   `{"call": "judge", "verdict": "...", "code": "<Lean code>"}`。
5. 对任何来源的候选 certificate，最终都必须交给官方 deterministic Lean judge 验证；公开集标签检查只用于离线实验，不是正式评测依据。
6. 如果某轮实验选择“模型输出即证书”，本地只做 JSON schema（结构约束）校验和 Lean 验证，不在 LLM 之后改写 `verdict` 或 `code`。

## 工程优先级

1. Reproducibility first: every download, index, and generated artifact must be
   rebuildable from scripts.
2. Lean verification first: do not trust model text unless Lean accepts it.
3. Compression-aware design: `512000` bytes is enough for a real solver, but
   not enough for raw 22M lookup tables.
4. Avoid overfitting public problems: public subsets are regression tests, not
   the full target distribution.

## 当前覆盖率快照

Using the ETP `full_entries.json` index and default 1669-row public set:

- positives: 819 / 819 have an implication path in the ETP graph
- negatives: 60 / 850 have a direct finite fact/counterexample entry

在已接入 size-2 本地反模型后，负例合并覆盖已经提升到 `498/850`，剩余 `352` 个公开负例未覆盖。已经落盘的 pure Lean 4 反例资产中，`438/438` 个证书已通过 Docker Lean 4.29.1 验证。

这意味着负例反例资产已经形成第一批可复用 ground truth（真值资产）。下一步应把它压缩成 compact counterexample evidence bank（紧凑反模型证据库），用于离线错误分析、cheatsheet 迭代和后续提交压缩设计，并保留 Lean 证书作为可验证来源。

当前已经新增 `scripts/counterexample/build_counterexample_evidence_bank.py` 作为这一压缩步骤的入口。输出 JSONL 不作为 evaluator 运行时输入；正式 baseline 使用 `--dataset data/processed/splits/test.jsonl`、`--cheatsheet cheatsheets/mini/current/stage2_judge_json_certificate.en.md`、`--max-concurrency 32` 和 `--failed-rerun-concurrency 4`。

## 直接风险

- Official Stage 2 repository（官方 Stage 2 仓库）已经公开；本项目当前 evaluator/solver 架构还没有适配官方 Solo/Marathon protocol（协议）和官方 Lean toolchain `v4.30.0-rc2`。
- 本地 `external/equational-theories-lean-stage2/` 当前不是 git clone，后续若需要依赖该目录做差异分析，应先修复为干净浅克隆；规则事实暂以 raw snapshot 和远端 HEAD 为准。
- 官方文档内部对 Marathon 默认时间预算存在不一致，适配前需要以代码和最新文档再次核对。
- `rules/evaluation.md` 仍把 final scoring rules（最终计分规则）、evaluation model（评测模型）、evaluation configuration（评测配置）和 private evaluation set（私有评测集）标为 TBD。
- Some negative implications have no finite counterexample; they need special
  handling rather than assuming every false case is finitely refutable.
- The parent git worktree has unrelated dirty files. This repo must keep its
  changes scoped under `Math-Distill-Stage2/`.

## 来源

- Stage 2 overview：<https://competition.sair.foundation/competitions/mathematics-distillation-challenge-equational-theories-stage2/overview>
- Stage 2 API：<https://server-9527.sair.foundation/api/competitions/mathematics-distillation-challenge-equational-theories-stage2>
- Official Stage 2 repository：<https://github.com/SAIRcompetition/equational-theories-lean-stage2>
- Zulip channel `Math Distillation Challenge - equational theories`：2026-05-21 已同步到最新 message id `2101`；本次新增归档 `data/raw/references/zulip/math-distillation-challenge-equational-theories/messages/2026-05-19.jsonl`、`2026-05-20.jsonl`、`2026-05-21.jsonl`，摘要见 `docs/zulip-digests/`。
- 本地抓取时间：2026-05-21（官方页面/API/judge raw 快照与 Zulip 同步）。
