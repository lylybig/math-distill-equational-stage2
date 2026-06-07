# Source Index

Updated: 2026-05-21

## Primary Sources

- Stage 2 overview:
  <https://competition.sair.foundation/competitions/mathematics-distillation-challenge-equational-theories-stage2/overview>
  - 2026-04-29 核对：Core Task 要求 solver 为每题提交 Lean 4 certificate；answer format 为 judge call JSON，包含 `call`、`verdict`、`code`。
  - 2026-04-29 旧工作假设：曾按用户确认把“每题调用 `gpt-oss-120b`”记录为项目策略。
  - 2026-05-06 修正：官方规则没有明文要求每题必须调用 LLM；官方要求是提交 Lean 4 certificate 并通过 deterministic Lean judge。LLM access 是可用资源，`gpt-oss-120b` 是当前官方仓库 `pipeline/config.json` 中的参考配置，最终 evaluation model/configuration 仍为 TBD。
  - 2026-05-06 核对：页面嵌入的 competition bootstrap JSON 与 Stage 2 API 均显示 `updatedAt=2026-05-05T05:53:44Z`、`participantCount=134`、`pythonMaxBytes=512000`、`cheatsheetMaxBytes=512000`、`allowDraftSubmissions=false`。
  - 2026-05-06 渲染页面核对：overview 已列出官方 Stage 2 仓库、Solo/Marathon 两个 track、`solver.py` 单文件提交、Stage 2 official start `2026-05-01 12:00 UTC` 和 deadline `2026-08-31 23:59 AoE`。
  - 2026-05-11 核对：页面嵌入的 competition bootstrap JSON 与 Stage 2 API 仍显示 `updatedAt=2026-05-05T05:53:44Z`、`pythonMaxBytes=512000`、`cheatsheetMaxBytes=512000`、`allowDraftSubmissions=false`、`publicCodePrefix=EQT02`；`participantCount` 更新为 `147`。
  - 2026-05-12 核对：页面嵌入的 competition bootstrap JSON 与 Stage 2 API 仍显示 `updatedAt=2026-05-05T05:53:44Z`、`pythonMaxBytes=512000`、`cheatsheetMaxBytes=512000`、`allowDraftSubmissions=false`、`publicCodePrefix=EQT02`；`participantCount` 更新为 `148`。
  - 2026-05-13 核对：Stage 2 API 与 contributor-network 页面嵌入的 competition bootstrap JSON 仍显示 `updatedAt=2026-05-05T05:53:44Z`、`pythonMaxBytes=512000`、`cheatsheetMaxBytes=512000`、`allowDraftSubmissions=false`、`publicCodePrefix=EQT02`；`participantCount` 更新为 `151`。
  - 2026-05-18 核对：Stage 2 API 与 overview bootstrap JSON 仍显示 `updatedAt=2026-05-05T05:53:44Z`、`pythonMaxBytes=512000`、`cheatsheetMaxBytes=512000`、`allowDraftSubmissions=false`、`publicCodePrefix=EQT02`、`leaderboardPublished=false`、`playgroundEnabled=true`；`participantCount` 更新为 `165`。
  - 2026-05-21 核对：Stage 2 API 与 overview bootstrap JSON 仍显示 `updatedAt=2026-05-05T05:53:44Z`、`pythonMaxBytes=512000`、`cheatsheetMaxBytes=512000`、`allowDraftSubmissions=false`、`publicCodePrefix=EQT02`、`leaderboardPublished=false`、`playgroundEnabled=true`；`participantCount` 更新为 `170`。
  - 本地快照：`data/raw/references/sair_api/competition_stage2_overview.html` 和 `data/raw/references/sair_api/competition_stage2_overview_bootstrap.json`。
- Stage 2 API snapshot:
  <https://server-9527.sair.foundation/api/competitions/mathematics-distillation-challenge-equational-theories-stage2>
  - 本地快照：`data/raw/references/sair_api/competition_stage2.json`。
- Competition list API:
  <https://server-9527.sair.foundation/api/competitions>
  - 本地快照：`data/raw/references/sair_api/competitions.json`。
- SAIR Contributor Network public solver snapshot:
  <https://competition.sair.foundation/contributor-network/mathematics-distillation-challenge-equational-theories-stage2/EQT02-S00018>
  - 2026-05-13 下载：ChristopherBrock 发布的 Stage 2 Solo solver `Euler:`，public code `EQT02-S00018`，`publishedAt=2026-05-12T15:50:26Z`。
  - 本地快照：`data/raw/references/sair_contributor_network/mathematics-distillation-challenge-equational-theories-stage2/EQT02-S00018/page.html`、`bootstrap.json`、`solver.py`、`metadata.json`。
- Stage 2 official judge/evaluation repository:
  <https://github.com/SAIRcompetition/equational-theories-lean-stage2>
  - 2026-05-06 核对：main commit `6805e2323018fbd8a85f41ca09fc33d74d5a02a5`，commit time `2026-05-03T00:20:28Z`。
  - 2026-05-06 核对：Stage 2 playground 的 solver template API 需要登录态；未登录抓取返回 `401`。本地以官方 repository 浅克隆中的 `examples/solo/` 作为 Solo reference demos 的公开可复现来源，不再在 raw references 中重复落盘。
  - 2026-05-11 核对：main commit 仍为 `6805e2323018fbd8a85f41ca09fc33d74d5a02a5`；官方 raw `pipeline/config.json` 的 LLM 参考配置为 `openai/gpt-oss-120b`、provider `deepinfra/bf16`、`max_output_tokens=65536`、`temperature=0.0`、`reasoning_effort=medium`、`seed=0`。`rules/evaluation.md` 仍将 final evaluation model/configuration/problem set 标为 TBD（待定）。
  - 2026-05-12 核对：GitHub `main` 仍为 `6805e2323018fbd8a85f41ca09fc33d74d5a02a5`；新增本地 raw snapshot `judge/verify.py`，用于追踪 proof policy、`BANNED_PROOF_TOKENS` 和 allowlist 检查实现。
  - 2026-05-18 核对：GitHub 远端 `main` 仍为 `6805e2323018fbd8a85f41ca09fc33d74d5a02a5`，commit time `2026-05-03T00:20:28Z`；官方 raw `pipeline/config.json` 仍为 Solo `3600s`、Lean `300s`、submitted Lean code `100000` bytes、false certificate `20000` bytes、solver source `500000` bytes、LLM `openai/gpt-oss-120b` / `deepinfra/bf16` / `65536` tokens。
  - 2026-05-21 核对：GitHub 远端 `main` 仍为 `6805e2323018fbd8a85f41ca09fc33d74d5a02a5`，commit time `2026-05-03T00:20:28Z`；官方 raw `pipeline/config.json` 仍为 Solo `3600s`、Lean `300s`、submitted Lean code `100000` bytes、false certificate `20000` bytes、solver source `500000` bytes、LLM `openai/gpt-oss-120b` / `deepinfra/bf16` / `65536` tokens。
  - 2026-05-21 核对：官方 README 与 Solo/Marathon 文档显示 solver sandbox 当前除 Python 标准库外批准 `sympy==1.13.3`；`numpy`、`z3`、`networkx` 等未在批准列表中。
  - 本地快照：`data/raw/references/stage2_judge/README.md`、`rules/overview.md`、`rules/evaluation.md`、`docs/solo_mode.md`、`docs/marathon_mode.md`、`judge/verify.py`、`pipeline/config.json`、`lean-toolchain`、`main_commit.json`。
  - 本地目录：`external/equational-theories-lean-stage2/` 当前存在官方仓库文件树但不是 git clone（缺少 `.git`）；2026-05-21 未覆盖该目录，规则事实以 `data/raw/references/stage2_judge/` 快照和 `git ls-remote` 远端 HEAD 为准。
- SAIR Zulip channel: `Math Distillation Challenge - equational theories`
  - Site: <https://zulip.sair.foundation>
  - 2026-05-12 同步：归档 2026-05-11 可见消息 3 条，最新 message id `2060`。
  - 2026-05-18 同步：重新准备 `/Users/zetyun2026/.zuliprc` 后成功归档 5 条新消息，覆盖 `2026-05-12`、`2026-05-13`、`2026-05-15`、`2026-05-17`，最新 message id `2078`。
  - 2026-05-11 message `2057` 讨论 Lean tactics：Zulip 口径是提交证明可以使用标准 Lean 4 / Mathlib tactics；规则边界不是 tactic 名称本身，而是 elaborated proof（展开后证明）使用的 axiom/declaration 是否通过官方 judge allowlist 和 banned-token 检查。此条作为讨论线索；权威实现以官方 `judge/verify.py` 快照为准。
  - 2026-05-15 messages `2072`、`2073`：YZ 讨论 Stage 2 final eval 的计划口径，包括 planned model tracks（计划模型赛道）为 `GPT-OSS-120B` 和 `Gemma-4-31B`、不同模型作为 separate tracks（独立赛道）、Solo mode 每题独立评估、Marathon final evaluation 当前建议不超过 100 题且 true implications 比例更高。此为 Zulip 讨论线索；官方页面/API 与 `rules/evaluation.md` 对 final evaluation model/configuration/problem set 仍为 TBD（待定）。
  - 2026-05-21 同步：归档 15 条新消息，覆盖 `2026-05-19`、`2026-05-20`、`2026-05-21`，最新 message id `2101`。
  - 2026-05-20 message `2097`：YZ 说明 judge 的 `code` 字段是 complete Lean file（完整 Lean 文件），可在主证明前声明 helper `theorem`、`def`、`lemma`、`namespace` 或 `notation`，但需要暴露顶层 `def submission : Goal := ...` 或类型匹配 `Goal` 的 term。此为 Zulip 讨论线索；`judge/verify.py` 当前实现确认提交 Lean 会原样写入 `Submission.lean`，再检查 `example : Goal := submission`。
  - 2026-05-21 messages `2100`、`2101`：YZ 明确表示 order 5 implications（5 阶等式蕴含）会包含在 final evaluation（最终评测）中；具体比例仍取决于 community feedback 和 co-organizers 的最终决定。此为 Zulip 讨论线索；官方页面/API 与 `rules/evaluation.md` 对 evaluation problem sets 仍为 TBD（待定）。
  - 本地归档：`data/raw/references/zulip/math-distillation-challenge-equational-theories/messages/YYYY-MM-DD.jsonl`、`data/raw/references/zulip/math-distillation-challenge-equational-theories/state.json`。
  - 本地摘要：`docs/zulip-digests/YYYY-MM-DD.md`。
- Gemma 4 31B model card:
  <https://huggingface.co/google/gemma-4-31B>
  - 2026-05-07 核对：`31B Dense` 的 model card context length 为 `256K tokens`。
  - 2026-05-07 本地 mass endpoint 运行证据：`artifacts/runs/2026-05-07/official-opnorm-sample200-gemma/results/sample_200.json` 中 37 次 LLM 调用均被拒绝，错误显示当时部署 `max_model_len=max_total_tokens=20480`。同日服务重启后，`/v1/models` 返回 `max_model_len=65536`。因此 `20480` 和 `65536` 都是 endpoint 部署限制，不是 Gemma 4 31B 理论上下文窗口。
  - 2026-05-07 本地复测证据：`artifacts/runs/2026-05-07/official-opnorm-llmfailed37-gemma4096/llm_failed_37_max4096_header_check.json` 记录 37 个旧 LLM 失败 prompt 在 `max_tokens=4096` 下均通过请求头校验，未再触发上下文窗口错误。
- Selected public problems:
  <https://huggingface.co/datasets/SAIRfoundation/equational-theories-selected-problems>
- Stage 1 benchmark metadata:
  <https://huggingface.co/datasets/SAIRfoundation/equational-theories-benchmark>
- Stage 1 local judge:
  <https://github.com/SAIRcompetition/equational-theories-stage1-judge>
- Equational Theories Project:
  <https://teorth.github.io/equational_theories/>
  - GitHub repository：<https://github.com/teorth/equational_theories>
  - 2026-05-09 下载 Blueprint PDF：`data/raw/references/etp/blueprint.pdf`，128 页，SHA256 `8872e86261ed688acdd997ea17bf9f5e26f1fbf6a37ad230f71fcf1b2b4acafd`。
  - 2026-05-09 下载 Paper PDF：`data/raw/references/etp/paper.pdf`，74 页，SHA256 `78fdb86682093f2a91472a7dcaa86e171e5df3c4ba0c100af245b1c9ef0a1c3b`。
  - 本地数据快照：`data/raw/references/etp/README.md`、`data/raw/references/etp/full_entries.json`、`data/raw/references/etp/blueprint.pdf`、`data/raw/references/etp/paper.pdf`。
  - 本地浅克隆：`external/equational_theories/`，2026-05-09 HEAD `b99c0e486501e5b0690ef3fe5250d3aa57e63478`。
- A Spine Isolation Theorem for Magma Implications:
  <https://zenodo.org/records/19658028>
  - 2026-05-09 核对：Zenodo `latest` API 显示该论文共有 3 个版本；最新版为 record `19658028`，version `v3`，DOI `10.5281/zenodo.19658028`，publication date `2026-04-19`，resource type 为 preprint。
  - 2026-05-09 下载最新版：`spine-isolation-theorem.pdf`，Zenodo checksum `md5:1eda0f3a3305eb120c49db3785898f20`，本地校验通过。
  - 本地最新版快照：`data/raw/references/papers/zenodo-19658028/record.json` 和 `data/raw/references/papers/zenodo-19658028/spine-isolation-theorem.pdf`。
  - 本地历史版快照：`data/raw/references/papers/zenodo-19380600/` 保存 v1.0，record `19380600`，DOI `10.5281/zenodo.19380600`。
- Spine Isolation Theorem Lean 4 formalization:
  <https://github.com/mysticflounder/equational-magma-theorems>
  - 2026-05-09 核对并浅克隆：HEAD commit `0d794208ec2c0188948090ae0d536e184d094eb5`，commit time `2026-04-19T20:15:32-07:00`，commit subject `v3: tightened text + v2 mirror-count fix re-applied (266)`。
  - 本地浅克隆：`external/equational-magma-theorems/`，包含 `SpineIsolation/*.lean`、论文 Markdown/PDF 和 mirror count 脚本。
- Tao launch post:
  <https://terrytao.wordpress.com/2026/03/13/mathematics-distillation-challenge-equational-theories/comment-page-1/>

## Local Reference Projects

- `../Math-Distill-Decision-Tree`: Stage 1/LLM and hard2/hard3 experiments.
- `../equational-theories-stage1-judge`: local copy/fork of the Stage 1 judge
  with `hard2_200` and `hard3_400` example snapshots.
- `../mathematics-distillation-challenge-equational-theories`: prior prompt and
  cheatsheet experiment workspace.
- `external/equational-theories-lean-stage2/`: expected local official Stage 2
  judge/evaluation repository path; as of 2026-05-21 it contains a file tree
  but is not a git clone, so use raw snapshots plus remote HEAD checks for
  authoritative update status until the path is repaired.
- `external/equational-magma-theorems/`: local shallow clone of the Spine Isolation
  Theorem Lean 4 formalization and accompanying paper assets.

## Download Policy

Default downloads are intentionally bounded:

- download all selected public problem JSONL files
- download small benchmark metadata files
- download ETP `full_entries.json` and README files
- do not download Stage 1 benchmark `runs.jsonl` or `cells.jsonl` by default
  because the full benchmark storage is large and not needed for the first
  certificate generator

If full run-level benchmarking becomes useful later, add an explicit script
flag rather than making it default.
