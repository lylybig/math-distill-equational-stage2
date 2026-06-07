# Cheatsheet 优化流程设计

更新时间：2026-04-30

## 目标

Cheatsheet（提示表）优化的目标不是让本地代码替模型作答，而是让 `gpt-oss-120b` 更稳定地直接输出可解析、真假正确、Lean 4 可验证的 judge JSON certificate（评测 JSON 证书）。

本文档不是模型输入，不会传给 evaluator（评估器）。它是 human-in-the-loop（人工在环）和后续自动化 harness（实验编排器）的操作规程：规定如何编辑 cheatsheet、如何记录版本、如何用 train/dev/test 防止调参污染，以及未来 agent 只能在哪个环节介入。

## 当前原则

1. Evaluator（评估器）只负责运行固定 dataset（数据集）和固定 cheatsheet，记录请求、解析、verdict checker（真假检查器）、Lean 4 verifier（Lean 4 验证器）和指标。
2. Evidence bank（证据库）、失败样例和 Lean 错误日志只用于离线分析和下一版 cheatsheet，不作为评估时输入。
3. Test split（测试集）只用于冻结版本后的 baseline（基线评估），不用于日常调参。
4. Train/dev mini runs（小规模训练/开发集运行）用于快速迭代 cheatsheet。
5. 从 `current/` 发起正式评测前，必须先创建 `drafts/<draft-id>/` 快照；实验结果、promote/reject 决策和后续版本冻结都应绑定到 draft，而不是直接绑定到可继续编辑的 `current/`。

## Cheatsheet 文件结构

当前 cheatsheet 按数据集阶段分目录，每个阶段再分英文运行版和中文复查版：

- `cheatsheets/smoke/current/`：smoke flow 使用。
- `cheatsheets/smoke/drafts/`：smoke 每次评测前从 `current/` 固定出来的只读实验快照。
- `cheatsheets/smoke/versions/`：smoke 候选版本。
- `cheatsheets/mini/current/`：train-mini、dev-mini 和 test baseline 使用。
- `cheatsheets/mini/drafts/`：mini 每次评测前从 `current/` 固定出来的只读实验快照。
- `cheatsheets/mini/versions/`：mini 候选版本。
- `stage2_judge_json_certificate.en.md`：英文运行版，是 evaluator 模型输入。
- `stage2_judge_json_certificate.zh.md`：中文人工复查版，只用于人类审阅、规则讨论、实验记录和复盘，不传给 evaluator。
- `manifest.json`：记录当前版本、基于版本、来源 run、调整内容、sha256 和 accept/reject 状态。

英文运行版必须保持 Markdown 分节结构：

- `Verdict Rules`：真假判断规则。
  - `True Strict Rules`：选择 `true` 的严格条件。
  - `False Strict Rules`：选择 `false` 的严格条件。
  - `Heuristic Rules`：来自 Stage 1 和本项目实验的启发式规则。
- `Lean 4 Certificate Rules`：Lean 4 证书生成规则。
  - 记录本实验不断总结的 Lean 失败模式和修复规则。
  - 禁止把不可验证的 renderer（渲染器）或本地查表逻辑混进 evaluator。
- `Output Format Rules`：输出格式规则。
  - 只描述模型应该输出什么，确保 parser（解析器）稳定抽取。

新增规则时应优先放进对应章节，不要把所有内容堆到文件末尾。

中文复查版不要求逐字翻译英文版，但必须同步记录关键策略、禁用模式和人工复查重点。英文版发生会影响模型行为的变化时，应同步更新中文版对应说明。

## Cheatsheet 版本管理

当前工作文件始终是：

```text
cheatsheets/mini/current/stage2_judge_json_certificate.en.md
cheatsheets/mini/current/stage2_judge_json_certificate.zh.md
cheatsheets/mini/current/manifest.json
```

`current/` 表示正在编辑和快速迭代的工作态 cheatsheet，不代表已接受版本。

评测前先从 `current/` 创建一个 draft：

```bash
python scripts/cheatsheets/create_draft_cheatsheet.py \
  --current-dir cheatsheets/mini/current \
  --drafts-root cheatsheets/mini/drafts \
  --draft-id draft-2026-04-30-dev-mini-v1 \
  --based-on v2026-04-30-dev-mini-v0 \
  --notes "tighten false certificate rules before dev-mini rerun"
```

`drafts/` 保存每次评测绑定的只读快照。评测结果、失败分析和 accept/reject 应首先绑定到对应 `drafts/<draft-id>/manifest.json` 或同名实验记录，不应回写到旧 draft，也不应直接把一次评测结果只记在 `current/` 上。

当一个候选版本值得保留时，用 `scripts/cheatsheets/version_cheatsheet.py` 从已评测 draft 发布快照：

```bash
python scripts/cheatsheets/version_cheatsheet.py \
  --draft-dir cheatsheets/mini/drafts/draft-2026-04-30-dev-mini-v1 \
  --version v2026-04-30-dev-mini-v1 \
  --source-run artifacts/runs/2026-04-30-stage2-evaluator-dev-mini-v1 \
  --metrics artifacts/runs/2026-04-30-stage2-evaluator-dev-mini-v1/summary.json \
  --notes "first markdown structured cheatsheet"
```

脚本会写入：

```text
cheatsheets/<stage>/versions/<version>/stage2_judge_json_certificate.en.md
cheatsheets/<stage>/versions/<version>/stage2_judge_json_certificate.zh.md
cheatsheets/<stage>/versions/<version>/stage2_judge_json_certificate.md
cheatsheets/<stage>/versions/<version>/manifest.json
```

其中 `.en.md` 是运行版，`.zh.md` 是人工复查版，`.md` 是兼容旧命令的英文别名。`manifest.json` 记录 version（版本号）、source draft（来源 draft）、source run（来源实验）、summary metrics（指标快照）、文件大小和 sha256。版本目录只保存值得比较或复现的候选，不保存每一次微小编辑。

三层状态分工如下：

- `current/`：可继续编辑的工作态。
- `drafts/`：评测前固定下来的只读实验快照，用来绑定 run 和决策。
- `versions/`：已冻结、可比较、可复现的候选态 cheatsheet。

正式 baseline 必须引用某个已发布版本，或在运行记录中明确记录所用 draft 和其 sha256。

历史 `manifest.json` 中的 `source_path` 保留生成当时的原始路径，不做 retroactive rewrite（追溯改写）。

## 短期优化流程

短期采用 human-in-the-loop（人工在环）流程：

1. 先编辑 `cheatsheets/<stage>/current/`，并更新 `current/manifest.json`。
2. 评测前创建 draft：`python scripts/cheatsheets/create_draft_cheatsheet.py --current-dir cheatsheets/mini/current --drafts-root cheatsheets/mini/drafts --draft-id <draft-id> --based-on <base-version-or-draft> --notes "<notes>"`
3. 跑 smoke 或 train-mini；评估命令使用 draft 路径，而不是 `current/`：
   `python scripts/evaluator/run_stage2_evaluator.py --dataset data/processed/splits/train.jsonl --cheatsheet cheatsheets/mini/drafts/<draft-id>/stage2_judge_json_certificate.en.md --run-dir artifacts/runs/<train-mini-run> --limit 10 --timeout-seconds 180 --no-rerun-failed --max-concurrency 32 --failed-rerun-concurrency 4`
4. 用 `python scripts/error_analysis/analyze_stage2_run.py --run-dir artifacts/runs/<train-mini-run>` 从 `per_run.jsonl` 汇总失败类型：
   - request/format failure（请求或格式失败）
   - verdict failure（真假判断失败）
   - Lean syntax/elaboration failure（Lean 语法或 elaboration 失败）
   - Lean semantic failure（证书语义不匹配）
5. 人工把高频、可泛化的失败模式转成 `current/` cheatsheet 规则；不要回写已经评测过的 draft。
6. 重新创建新 draft，再跑 dev-mini：
   `python scripts/evaluator/run_stage2_evaluator.py --dataset data/processed/splits/dev.jsonl --cheatsheet cheatsheets/mini/drafts/<new-draft-id>/stage2_judge_json_certificate.en.md --run-dir artifacts/runs/<dev-mini-run> --limit 20 --timeout-seconds 180 --no-rerun-failed --max-concurrency 32 --failed-rerun-concurrency 4`
7. 只有 dev-mini 的 parse、verdict、Lean 指标明显改善，才考虑把对应 draft 冻结为版本，或扩大 dev 规模后再跑 full test baseline。

并发策略：

- 第一轮批量跑默认 `--max-concurrency 32`，包括 train-mini、dev-mini 和 full test baseline。
- 失败重跑默认 `--failed-rerun-concurrency 4`。
- smoke 可以保持较小并发，用来检查流程健康。

## 代码组织

错误归因和失败分类属于可测试的业务逻辑，放在 `src/math_distill_stage2/error_analysis/`：

- `stage2_run.py`：读取 evaluator run，分类 request/parse/verdict/Lean 失败，输出 `errors.jsonl`、`failure_taxonomy.json`、`analysis.md`。

`scripts/` 只保留命令行入口，根目录不再放真实命令脚本：

- `scripts/error_analysis/`：分析类入口，例如 `analyze_stage2_run.py`。
- `scripts/evaluator/`：评估和 smoke 入口。
- `scripts/cheatsheets/`：cheatsheet draft 创建、版本发布和后续候选管理入口。
- `scripts/counterexample/`：反模型搜索、反例证书、反例资产和 evidence bank 入口。
- `scripts/data/`：公开数据下载、索引、split 和覆盖率分析入口。
- `scripts/lean_certificates/`：Lean smoke certificate 生成入口。
- `scripts/public_eval/`：公开集 harness 入口。

## 长期自动化方向

长期可以把 cheatsheet 优化落实到代码，但应放在独立 harness（实验编排器）里，不应塞进 evaluator：

- `src/math_distill_stage2/error_analysis/` + `scripts/error_analysis/analyze_stage2_run.py`：读取 `per_run.jsonl`，输出 failure taxonomy（失败分类）、代表样例、Lean 错误聚类和指标变化。
- `scripts/propose_cheatsheet_patch.py`：输入分析报告和当前 cheatsheet，生成候选 patch（候选补丁），但不自动接受。
- `scripts/run_cheatsheet_candidate.py`：对候选 cheatsheet 跑固定 train/dev mini suites（小套件），输出 accept/reject 所需指标。

Agent 可以用于 proposal（改进提案）阶段，但 harness 必须负责：

- 固定数据切片。
- 固定运行参数。
- 落盘候选版本。
- 复评并比较指标。
- 根据门槛 accept/reject。

不要让 agent 在单轮对话里直接依据主观判断改完 cheatsheet 后跳过复评。

## 接受门槛

当前建议门槛：

- Smoke：request success、parse success 必须接近 100%，至少有一条 Lean 通过。
- Train-mini：Lean pass rate（Lean 通过率）和 final accuracy（最终准确率）必须比上一候选提高，不能显著降低 parse success。
- Dev-mini：重点看 final accuracy、F1、verdict accuracy、Lean strict pass rate 是否同步改善。
- Full test baseline：只在 cheatsheet 冻结后运行，并记录为里程碑结果。
