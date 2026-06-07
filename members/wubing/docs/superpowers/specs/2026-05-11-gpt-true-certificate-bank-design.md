# GPT True Certificate Bank 设计

## 背景

当前 Stage 2 Solo solver 已经形成 no-LLM runtime（无运行时大模型依赖）主线：`solver.py` 只靠 deterministic certificate generation（确定性证书生成）和官方 judge 验证计分。历史运行也显示，直接增加 runtime LLM fallback（运行时大模型兜底）没有带来稳定 accepted 增益。

但剩余 true failures（真命题失败样本）仍然需要大量 Lean 4 certificate（证明证书）探索。当前 VSCode Codex/GPT-5.5 可以作为离线 proof synthesizer（证明合成器）：在任务对话中阅读单题 prompt，生成 Lean proof body，再由本地脚本包装并交给官方 Stage 2 judge 验证。

因此需要一个全局、可复查、可扩展的 proof bank（证明库）来保存 Codex/GPT 生成的 true certificate attempts（真命题证书尝试）。第一阶段只生成、验证、归档证书尝试，不修改 solver，不决定证书如何进入 solver template。

## 目标

建立全局 `gpt_true_certificates` proof bank，用于保存 Stage 2 true proof certificate attempts：

- 从候选 true implication（真蕴含）池生成 prompt pack。
- 当前 Codex 会话根据 prompt item 合成 Lean proof body。
- 保存 raw response（原始模型响应）、提取后的 proof body、完整 certificate、official judge result（官方评测器结果）。
- 将所有 attempts 写入 append-only ledger（只追加账本）。
- 将 official judge accepted 的 attempts 派生到 accepted index（通过索引）。
- 支持后续检查、重建索引、再验证和离线分析。

## 非目标

第一阶段不做：

- 不修改 `solver.py`。
- 不修改 `submissions/solo_official/solver.py`。
- 不新增 known-proof table（已知证明表）。
- 不做 solver template mining（求解器模板挖掘）。
- 不运行 solver evaluation ladder（评测阶梯）作为本流程的一部分。
- 不从 `test_locked` individual failures（单题失败）建候选池。
- 不把 Codex/GPT raw output 视为 accepted；只认官方 judge `accepted`。
- 不接外部 GPT API；需要 GPT 时由当前 Codex 任务会话执行 proof synthesis。
- 不做多模型比较、repair loop（修复循环）或大批量无界生成。

## 总体数据流

```text
candidate pool
  -> prompt_pack/*.md
  -> stage2-proofbank-generate-true-certificate
  -> raw_responses/*.txt
  -> stage2-proofbank-verify-import
  -> generated_attempts.jsonl + judge_results/
  -> stage2-proofbank-maintain
  -> global proof bank
```

`stage2-proofbank-*` 工作流生成的是离线 certificate facts（证书事实），不是 solver 改进。只有用户明确要求把 accepted certificates 转成 focused tests、proof seeds 或 solver templates 时，才切换到 `stage2-train-*` 工作流。

## 全局 Bank 目录

全局长期数据放在：

```text
data/processed/proof_banks/gpt_true_certificates/
  bank_manifest.json
  problems.jsonl
  attempts.jsonl
  accepted.jsonl
  latest_by_problem.jsonl
  bank_summary.json
  certificates/
  proof_bodies/
  prompts/
  raw_responses/
  judge_results/
```

事实源：

- `bank_manifest.json`
- `problems.jsonl`
- `attempts.jsonl`
- content-addressed files（内容寻址文件）

派生索引：

- `accepted.jsonl`
- `latest_by_problem.jsonl`
- `bank_summary.json`

如果派生索引与 `attempts.jsonl` 冲突，优先相信 `attempts.jsonl`，然后重建索引。

## Run Artifact 目录

单次生成批次保存在：

```text
artifacts/proof_bank_runs/YYYY-MM-DD/<source_run_id>/
  manifest.json
  input_problems.jsonl
  prompt_pack/
  raw_responses/
  generated_attempts.jsonl
  extraction_errors.jsonl
  proof_bodies/
  certificates/
  judge_results/
  summary.json
```

`source_run_id` 只用于 provenance（来源追踪）和审计，不决定全局 bank 的主键。

## Problem Key

全局问题主键不使用 `true_1738_1258` 或 ETP equation id。第一版采用 signature-first（规范签名优先）方案：

```text
problem_key = implication:sig:<eq1_signature_sha16>:<eq2_signature_sha16>
```

生成规则：

1. 用 `canonical_equation_signature(equation1)` 生成 `eq1_signature`。
2. 用 `canonical_equation_signature(equation2)` 生成 `eq2_signature`。
3. 对两个 signature 分别做 SHA-256，取前 16 个 hex 字符。
4. implication 是有向的，`eq1 -> eq2` 和 `eq2 -> eq1` 是不同 key。

示例：

```json
{
  "problem_key": "implication:sig:8d91e0c3a94b72f1:0af52c91d673ba8e",
  "problem_aliases": [
    "implication:etp:eq1738:eq1258",
    "order4_splits/dev_fast:true_1738_1258"
  ],
  "source_problem_id": "true_1738_1258",
  "source_dataset": "order4_splits/dev_fast",
  "eq1_id": 1738,
  "eq2_id": 1258,
  "eq1_signature": "v0=((v1*v1)*((v2*v0)*v0))",
  "eq2_signature": "v0=(v0*(((v1*v2)*v0)*v0))"
}
```

`source_problem_id`、`eq1_id`、`eq2_id` 都是 provenance 字段，可以为空。未来 order5 或无标签候选题只要有方程文本，也可以进入同一套 key scheme。

## 核心 Ledger

### `problems.jsonl`

一题一行，按 `problem_key` 去重。

```json
{
  "schema_version": 1,
  "problem_key": "implication:sig:<h1>:<h2>",
  "problem_aliases": ["implication:etp:eq1738:eq1258"],
  "eq1_id": 1738,
  "eq2_id": 1258,
  "equation1": "<premise equation text>",
  "equation2": "<goal equation text>",
  "eq1_signature": "<canonical premise signature>",
  "eq2_signature": "<canonical goal signature>",
  "expected_verdict": true,
  "first_seen_dataset": "order4_splits/dev_fast",
  "source_datasets": ["order4_splits/dev_fast"],
  "created_at": "2026-05-11T00:00:00Z"
}
```

### `attempts.jsonl`

append-only 主账本，所有 Codex/GPT attempts 都进入这里，包括 accepted、rejected、skipped、error 和 timeout。

```json
{
  "schema_version": 1,
  "attempt_id": "attempt:gpt-true-cert-order4-wide-20260511-001:000001",
  "problem_key": "implication:sig:<h1>:<h2>",
  "certificate_kind": "true_proof",
  "generator_mode": "codex_task",
  "generator_tool": "VSCode Codex",
  "generator_model": "codex-gpt-5.5",
  "prompt_template": "stage2_true_certificate_v2_trace",
  "prompt_sha256": "<sha256>",
  "raw_response_sha256": "<sha256>",
  "extracted_proof_body_sha256": "<sha256>",
  "proof_body_sha256": "<sha256>",
  "certificate_sha256": "<sha256>",
  "normalization_actions": ["replace_star_with_diamond"],
  "judge_backend": "official-stage2-judge",
  "judge_commit": "6805e2323018fbd8a85f41ca09fc33d74d5a02a5",
  "lean_version": "4.30.0-rc2",
  "official_judge_status": "accepted",
  "judge_status": "accepted",
  "judge_error_kind": "none",
  "judge_error_subkind": null,
  "judge_error_summary": null,
  "judge_result_sha256": "<sha256>",
  "source_run_id": "gpt-true-cert-order4-wide-20260511-001",
  "created_at": "2026-05-11T00:00:00Z"
}
```

### `accepted.jsonl`

派生索引，只收 `judge_status == accepted` 且 official judge 状态为 `accepted` 的 true proof attempts。

唯一性建议：

```text
(problem_key, certificate_sha256, judge_commit)
```

同一题可以保留多个不同 accepted certificates。第一阶段不选择“最佳证书”。

### `latest_by_problem.jsonl`

派生索引，用于快速查看每题当前状态：

```json
{
  "problem_key": "implication:sig:<h1>:<h2>",
  "latest_attempt_id": "<attempt id>",
  "latest_status": "accepted",
  "accepted_attempt_count": 2,
  "rejected_attempt_count": 5,
  "best_known_certificate_sha256": "<sha256>",
  "updated_at": "2026-05-11T00:00:00Z"
}
```

`best_known_certificate_sha256` 只用于检索便利，不代表 solver 策略选择。

## Source Run Manifest

一次 proof bank generation run 的 `manifest.json` 至少记录：

```json
{
  "schema_version": 1,
  "source_run_id": "gpt-true-cert-order4-wide-20260511-001",
  "created_at_utc": "2026-05-11T00:00:00Z",
  "purpose": "Generate offline Lean 4 true certificates for unsolved order4 true failures.",
  "bank_id": "gpt_true_certificates",
  "input": {
    "source_dataset": "order4_true_failure_pool/v1",
    "problem_count": 3,
    "selection_policy": "unsolved true problems without accepted certificate in bank",
    "input_sha256": "<sha256>"
  },
  "generator": {
    "mode": "codex_task",
    "tool": "VSCode Codex",
    "model": "codex-gpt-5.5",
    "automation": "current_task_skill",
    "prompt_template": "stage2_true_certificate_v2_trace",
    "prompt_template_sha256": "<sha256>"
  },
  "constraints": {
    "certificate_kind": "true_proof",
    "must_pass_official_judge": true,
    "max_attempts_per_problem": 1,
    "max_items_per_codex_generation_batch": 3,
    "max_wall_seconds_per_judge_call": 120
  },
  "judge": {
    "backend": "official-stage2-judge",
    "judge_repo_commit": "6805e2323018fbd8a85f41ca09fc33d74d5a02a5",
    "docker_image": "math-distill-stage2-official-judge:official-6805e23",
    "lean_version": "4.30.0-rc2"
  }
}
```

## Prompt Pack

每个 prompt item 是一个 Markdown 文件：

```text
artifacts/proof_bank_runs/YYYY-MM-DD/<source_run_id>/prompt_pack/000001.md
```

必须包含：

- artifact routing：`source_run_id`、`item_id`、`raw_response_path`
- problem identity：`problem_key`、`source_problem_id`、`source_dataset`、`eq1_id`、`eq2_id`
- premise equation 和 goal equation
- judge wrapper
- required output shape
- allowed / forbidden Lean constructs
- optional trace hint

Codex 生成技能写入：

```text
artifacts/proof_bank_runs/YYYY-MM-DD/<source_run_id>/raw_responses/000001.txt
```

raw response 应尽量只包含一个 JSON object：

```json
{
  "verdict": "true",
  "proof": "intro x y z\ncalc\n  <proof steps>"
}
```

`proof` 是插入到以下 wrapper 后的 tactic body：

```lean
import JudgeProblem

def submission : Goal := by
  intro G _ h
  <proof>
```

如果 Codex 找不到证明，也必须写入 raw response：

```json
{
  "verdict": "true",
  "proof": "",
  "notes": "No self-contained proof found within this bounded generation attempt."
}
```

## Prompt Policy

第一版使用：

```text
v2_trace if trace exists, else v1_minimal
max_attempts_per_problem = 1
proof_style = strict_calc
```

默认鼓励：

```text
intro, let, have, calc, exact, fun, rfl, Eq.trans, Eq.symm, .trans, .symm, congrArg
```

默认禁止：

```text
sorry, admit, axiom, unsafe, import, theorem headers, def submission,
external theorem names, congr_arg, *
```

`simp`、`grind`、`rw` 第一版不鼓励作为主路径；如果模型使用，仍必须由 official judge 验证。

## Extraction 和 Normalization

verify/import 阶段按顺序提取：

1. strict JSON
2. fenced JSON block
3. fenced Lean block
4. bare Lean proof body fallback

允许的轻量归一化：

- 去掉 Markdown fence。
- 去掉误输出的 theorem / `def submission` wrapper。
- 如果包含 `intro G _ h`，去掉 wrapper 和该行。
- 统一缩进。
- 将 proof body 中的 `*` 替换成 `◇`。
- 将 `congr_arg` 替换成 `congrArg`。

每个归一化动作必须写入 `normalization_actions`。第一版不做语义修复，例如自动翻转 `.symm`、补 lemma、修 have 类型或做 repair loop。

## Official Judge Result

verify/import 使用官方 Stage 2 judge。raw answer payload 形状：

```json
{
  "call": "judge",
  "verdict": "true",
  "code": "<full certificate code>"
}
```

官方状态与 bank 状态映射：

```text
official accepted          -> judge_status = accepted
official unparsed          -> judge_status = rejected
official malformed         -> judge_status = rejected
official incomplete_proof  -> judge_status = rejected
official incorrect         -> judge_status = rejected
runner timeout             -> judge_status = timeout
adapter exception          -> judge_status = error
preflight skip             -> judge_status = skipped
```

`judge_error_kind` 第一版使用：

```text
none
no_certificate_extracted
invalid_json_or_payload
forbidden_construct
lean_parse_error
lean_unknown_identifier
lean_type_error
lean_unsolved_goals
lean_tactic_failure
lean_timeout
judge_protocol_error
generator_error
unknown
```

raw judge result 必须按 SHA-256 保存到 `judge_results/`，`attempts.jsonl` 只保存摘要和 hash。

## Bank Merge

merge 必须幂等：

```text
same attempt_id + same hashes      -> skip
same attempt_id + different hashes -> hard error
same problem_key + same signatures -> merge aliases/source_datasets
same problem_key + different signatures -> hard error
```

accepted 索引只接收：

```text
judge_status == accepted
certificate_kind == true_proof
official_judge_status == accepted
```

`accepted.jsonl`、`latest_by_problem.jsonl`、`bank_summary.json` 是派生索引，merge 后应重建。

## Check 和 Rebuild

`check` 应验证：

- `bank_manifest.json` schema 可读。
- `problems.jsonl` 和 `attempts.jsonl` 每行 JSON 合法。
- `problem_key` 和 equation signatures 可重算一致。
- `attempt_id` 唯一。
- 所有 SHA-256 引用文件存在且 hash 一致。
- accepted attempts 有 official accepted judge evidence。
- 派生索引可由 `attempts.jsonl` 重建且一致。

`rebuild` 只重建：

- `accepted.jsonl`
- `latest_by_problem.jsonl`
- `bank_summary.json`

不修改 `attempts.jsonl` 或 `problems.jsonl`。

## 新增技能

新增四个项目私有技能：

```text
stage2-proofbank-start
stage2-proofbank-generate-true-certificate
stage2-proofbank-verify-import
stage2-proofbank-maintain
```

职责：

- `stage2-proofbank-start`：编排小批次 proof bank 闭环。
- `stage2-proofbank-generate-true-certificate`：当前 Codex/GPT 阅读 prompt item，合成 proof body，保存 raw response；不验证、不声称 accepted。
- `stage2-proofbank-verify-import`：提取 raw responses，包装 certificate，运行 official judge，写 generated attempts。
- `stage2-proofbank-maintain`：初始化、merge、check、rebuild 全局 bank。

技能与 `stage2-train-*` 的边界：

- `stage2-proofbank-*` 只生成和维护离线 certificate attempt bank。
- `stage2-train-*` 才能修改 solver、写 focused tests、promote versions。
- 从 accepted certificate 到 solver template 的转化必须作为后续单独训练流程处理。

## 后续脚本边界

后续实现阶段可新增：

```text
src/math_distill_stage2/proof_bank/
scripts/lean_certificates/proof_bank_init.py
scripts/lean_certificates/proof_bank_build_prompt_pack.py
scripts/lean_certificates/proof_bank_import_responses.py
scripts/lean_certificates/proof_bank_merge_run.py
scripts/lean_certificates/proof_bank_check.py
scripts/lean_certificates/proof_bank_rebuild_indexes.py
tests/proof_bank/
```

脚本负责确定性工作；Codex proof synthesis 由 `stage2-proofbank-generate-true-certificate` 技能在当前任务对话中完成。

## MVP 范围

第一版完成标准：

- 能从 candidate pool 选 50-100 个 true proof 目标。
- 每次 Codex 生成批次限定 1-3 个 prompt items。
- 每个已处理目标都有 attempt record 或 extraction error。
- 每个 attempt 可追溯 prompt、raw response、proof body、certificate、judge result、source run。
- accepted certificates 可从 `accepted.jsonl` 检索。
- 全局 bank 通过 `check`。
- accepted/latest 索引可从 attempts 重建。
- 重复 merge 同一 run 不改变结果。

MVP 不做：

- repair loop
- 多模型比较
- 自动 template mining
- solver 修改
- 大批量无界生成

## 风险与控制

### 误用为 known-proof table

控制：第一阶段不提供 export-to-solver 命令；accepted index 只叫 accepted attempts，不叫 solutions。任何 solver 使用都必须另走 `stage2-train-*`。

### 对评测集过拟合

控制：不从 `test_locked` individual failures 建池；source datasets 全量记录；proof bank accepted 数不等同于 solver 得分。

### GPT 输出不可复现

控制：保存 prompt、raw response、model/tool、prompt template hash、source run、full certificate 和 judge result。不声称模型调用可复现，只保证产物可复查和可再验证。

### Judge 版本漂移

控制：每条 attempt 保存 judge commit、Docker image、Lean version、proof policy 摘要。后续 judge 更新时新增 reverify run，不覆盖旧事实。

### 数据体积膨胀

控制：内容按 SHA-256 去重；ledger 只存摘要；raw responses 和 judge results 是否纳入 git 由后续体积决定。

### 输出污染或违规构造

控制：preflight 拦截 forbidden constructs；最终只信 official judge；accepted 记录保存 direct declarations 和 axioms。

### 自动归一化改变语义

控制：只做轻量、可审计 normalization；保存 extracted proof body 和 normalized proof body；不做语义 repair。

### 成本和资源失控

控制：MVP 小批量；每题一次 attempt；Codex generation 每次 1-3 题；judge 并发和 timeout 有上限；大批量/云/付费任务必须人工确认。

## 需要同步的长期规则

后续落地时应最小更新：

- `AGENTS.md`：加入 `stage2-proofbank-*` 技能优先原则和与 `stage2-train-*` 的边界。
- `docs/architecture.md`：加入离线 true proof bank 层，说明它是离线证书事实库，不直接修改 solver。
