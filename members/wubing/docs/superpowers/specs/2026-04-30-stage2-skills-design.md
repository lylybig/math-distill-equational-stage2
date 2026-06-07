# Stage 2 技能体系设计

## 背景

当前 `Math-Distill-Stage2` 已经具备可复现的 Stage 2 基础闭环：

- `scripts/evaluator/run_stage2_evaluator.py` 负责标准评测。
- `scripts/error_analysis/analyze_stage2_run.py` 负责失败归因与报告生成。
- `scripts/cheatsheets/version_cheatsheet.py` 负责冻结 cheatsheet 候选版本。

现阶段缺少的是一套项目内、可版本管理、职责清晰的 skill（技能）体系，用来把“评测、分析、优化 cheatsheet、冻结候选”组织成统一工作流，同时保持 evaluator（评估器）和后续 harness（实验编排器）的确定性边界不被破坏。

比赛相关技能需要与其他已有技能显式区分，并体现它们只服务于本地 Stage 2 项目。

## 目标

第一版 Stage 2 技能体系需要满足以下目标：

1. 技能放在仓库根目录 `skills/` 下，随项目一起版本管理、评审和复现。
2. 技能采用专用流程节点拆分，而不是先做总控技能。
3. 技能以 `stage2-` 作为统一前缀，形成独立命名空间。
4. 技能直接复用现有 CLI 和落盘产物，不复制一层业务实现。
5. 技能边界必须清楚区分：
   - 确定性执行由现有脚本和后续 harness 负责。
   - 技能负责编排约束、错误分析消费规则和 cheatsheet 工作态编辑。
6. `stage2-optimize-cheatsheet` 可以直接修改 `cheatsheets/*/current/`，但必须遵守项目硬约束。
7. 在 `current/` 和 `versions/` 之间引入 `drafts/` 层，用于保存评测前快照、实验结果和 accept/reject 决策，避免工作态改动丢失实验上下文。

## 非目标

第一版不包含以下内容：

- 不实现 `stage2-loop` 总控技能。
- 不新增技能专用 Python 包装脚本。
- 不让技能替代 `run_stage2_evaluator.py`、`analyze_stage2_run.py`、`version_cheatsheet.py` 的业务逻辑。
- 不把 evidence bank（证据库）或逐题资产注入 evaluator 运行时。
- 不让技能在 LLM 输出之后修复、重写或替换 Lean code。
- 不在本轮设计中引入自动 accept/reject 决策器。

## 命名与目录

项目私有技能统一放在仓库根目录：

```text
skills/
  stage2-evaluate/
  stage2-analyze-run/
  stage2-optimize-cheatsheet/
  stage2-version-cheatsheet/
```

虽然最初期望使用 `stage2_` 前缀，但本地技能校验器要求技能 `name` 使用 hyphen-case（连字符命名），因此第一版统一采用 `stage2-` 前缀。该前缀保留了“比赛专用技能命名空间”的语义，同时兼容标准技能发现与校验约束。

## Cheatsheet 状态层级

调整后的 cheatsheet 生命周期分为三层：

```text
cheatsheets/<stage>/
  current/
  drafts/
    <draft-id>/
  versions/
    <version>/
```

- `current/`
  - 当前工作态。
  - 允许连续手工编辑。
  - 不承载正式实验历史，只记录“当前正在编辑什么”。
- `drafts/`
  - 工作中候选快照。
  - 默认规则是“每次准备发起一次评测前，先从 `current/` 生成一个 `draft`”。
  - `draft` 必须绑定单次评测或一组固定评测，并记录：
    - 基于哪个 `version` 或上一个 `draft`
    - 创建时的 cheatsheet 内容与哈希
    - 对应 run
    - 指标结果
    - accept/reject 或 promote/reject 状态
  - 允许手工额外创建 checkpoint，但默认不要求对每次编辑都自动快照。
- `versions/`
  - 正式冻结候选。
  - 只保存值得长期比较、回退或作为里程碑引用的版本。
  - 不承载高频试错。

## 技能清单

### 1. `stage2-evaluate`

用途：运行一轮标准 Stage 2 evaluator。

职责：

- 读取用户指定或默认的 dataset（数据集）、cheatsheet（提示表）和 `run_dir`。
- 如果本次评测目标是 `current/` 工作态，先创建一个 `draft` 快照，再用该 `draft` 参与评测。
- 如果用户显式指定某个 `draft` 或 `version`，直接评测该快照，不回写上游 cheatsheet 内容。
- 调用 `scripts/evaluator/run_stage2_evaluator.py` 或 smoke flow 入口。
- 确保默认参数与项目约定一致，例如：
  - 第一轮批量评测默认 `max_concurrency=32`
  - 失败重跑默认 `failed_rerun_concurrency=4`
  - 默认 `gpt-oss-120b`
  - 默认 Docker Lean 4 verification（Lean 4 验证）

输出：

- `cheatsheets/<stage>/drafts/<draft-id>/...`，当本轮评测从 `current/` 发起时
- `per_run.jsonl`
- `summary.json`
- `config.snapshot.json`
- `rerun_history.json`

允许改动范围：

- 仅写 `artifacts/runs/<run-id>/`

禁止行为：

- 不改 cheatsheet。
- 不改模型原始输出。
- 不把 evidence bank 作为 evaluator 运行时输入。
- 不把实验结果直接写回 `versions/`；评测结果应先绑定到 `draft`。

### 2. `stage2-analyze-run`

用途：把单次 evaluator run 转成可消费的失败分析产物。

职责：

- 读取已有 `run_dir`。
- 调用 `scripts/error_analysis/analyze_stage2_run.py`。
- 基于已有产物输出 failure taxonomy（失败分类）、代表错误和 Markdown 报告。

输出：

- `errors.jsonl`
- `failure_taxonomy.json`
- `analysis.md`

允许改动范围：

- 仅写目标 `run_dir` 内的分析产物

禁止行为：

- 不改原始 `per_run.jsonl`
- 不直接改 cheatsheet

### 3. `stage2-optimize-cheatsheet`

用途：基于单次 run 的失败分析，直接修改 `cheatsheets/*/current/` 工作态 cheatsheet。

职责：

- 读取：
  - `failure_taxonomy.json`
  - `errors.jsonl`
  - `analysis.md`
- 当前英文运行版 cheatsheet
- 当前中文复查版 cheatsheet
- 当前 `manifest.json`
- 提炼可泛化的失败模式。
- 直接修改 `current/` 下的中英文 cheatsheet 和工作态 `manifest.json`。

补充规则：

- `stage2-optimize-cheatsheet` 修改的是未来评测的工作态，不直接回写某个已存在 `draft` 的内容。
- 如果当前优化只是为了继续尝试，不必立刻冻结到 `versions/`；后续评测会先把新的 `current/` 复制成新的 `draft`。

允许改动范围：

- `cheatsheets/<stage>/current/stage2_judge_json_certificate.en.md`
- `cheatsheets/<stage>/current/stage2_judge_json_certificate.zh.md`
- `cheatsheets/<stage>/current/manifest.json`

禁止行为：

- 不改 `versions/` 下的冻结版本。
- 不改已有 `drafts/<draft-id>/` 的快照内容；`draft` 一旦创建，就视为该次评测的只读输入。
- 不把逐题 evidence 写入运行版 cheatsheet。
- 不为单一题目添加不可泛化的特判。
- 不修改 evaluator、parser、Lean verifier 代码来配合这次 cheatsheet 优化。

### 4. `stage2-version-cheatsheet`

用途：把已验证的 `draft` 冻结成可比较、可复现的候选版本。

职责：

- 读取某个 `draft` 下的中英文 cheatsheet、`manifest.json` 和对应评测结果
- 读取来源 `run_dir` 与 `summary.json`
- 调用 `scripts/cheatsheets/version_cheatsheet.py`
- 将候选写入 `cheatsheets/<stage>/versions/<version>/`

输出：

- `cheatsheets/<stage>/versions/<version>/stage2_judge_json_certificate.en.md`
- `cheatsheets/<stage>/versions/<version>/stage2_judge_json_certificate.zh.md`
- `cheatsheets/<stage>/versions/<version>/stage2_judge_json_certificate.md`
- `cheatsheets/<stage>/versions/<version>/manifest.json`

允许改动范围：

- 仅写新的 `versions/<version>/` 目录

禁止行为：

- 不直接从 `current/` 冻结到 `versions/`，除非明确做一次“手工 checkpoint draft -> version”转换
- 不回写 `current/`
- 不覆盖已有版本目录

## 共享规则

所有 `stage2-*` 技能共享以下硬约束：

1. 只通过落盘文件通信，不依赖隐式会话记忆。
2. 优先消费已有产物，不重复执行上一阶段。
3. test split（测试集）只用于候选冻结后的 baseline，不用于日常调参。
4. evaluator 运行时输入只允许 dataset、cheatsheet、配置参数，不允许逐题 evidence 注入。
5. 模型输出的 judge JSON certificate（评测 JSON 证书）是候选答案本身；技能不得在 LLM 输出后修复或替换 Lean code。
6. `drafts/` 是实验绑定快照层，`versions/` 是正式冻结层，两者不能混用。

## 技能结构

第一版每个技能统一采用轻量结构：

```text
skills/
  stage2-<name>/
    SKILL.md
    agents/openai.yaml
    references/
      ...
```

设计原则：

- `SKILL.md` 只保留触发条件、执行流程、硬约束。
- 详细规则拆到 `references/`，按需读取。
- 第一版不为每个技能单独新增 `scripts/`，直接复用项目既有 CLI。

## 参考文件设计

第一版参考文件按最小必要集组织：

```text
skills/
  stage2-evaluate/
    references/stage2-shared-rules.md
    references/evaluator-defaults.md
  stage2-analyze-run/
    references/stage2-shared-rules.md
  stage2-optimize-cheatsheet/
    references/stage2-shared-rules.md
    references/cheatsheet-editing-rules.md
  stage2-version-cheatsheet/
    references/stage2-shared-rules.md
    references/versioning-rules.md
```

其中：

- `stage2-shared-rules.md`
  - 比赛硬约束
  - 目录和产物约定
  - 命名规范
- `evaluator-defaults.md`
  - 并发、失败重跑、默认路径、Lean backend 约定
- `cheatsheet-editing-rules.md`
  - 允许编辑的章节
  - 必须同步的中英文内容
  - `current/manifest.json` 如何更新
- `versioning-rules.md`
  - 版本号格式
  - 何时允许从 `draft` 冻结
  - 何时禁止基于 test split 结果直接调参

## 验证策略

第一版只做轻量验证，不做自动闭环执行：

1. 结构校验
   - 对每个技能目录运行 `skill-creator/scripts/quick_validate.py`
   - 确保 `SKILL.md` frontmatter、命名和目录结构合法
2. 发现校验
   - 确认仓库根目录 `skills/` 可被工作区技能发现机制识别
3. 流程冒烟校验
   - 按技能说明人工走最小链路
   - 确认路径、命令、输入输出文件名没有偏差

## 文档接入

技能体系落地后，需要同步更新以下文档：

- `docs/architecture.md`
  - 说明 `stage2-*` 技能只负责流程编排、分析建议、`current/` 工作态编辑和 `drafts/`/`versions/` 生命周期管理
- `docs/README.md`
  - 记录仓库内 `skills/` 是项目私有技能目录

正式设计规格保存在：

- `docs/superpowers/specs/2026-04-30-stage2-skills-design.md`

## 第一版实现范围

第一版实现仅包含以下新增文件：

```text
skills/
  stage2-evaluate/
    SKILL.md
    agents/openai.yaml
    references/stage2-shared-rules.md
    references/evaluator-defaults.md
  stage2-analyze-run/
    SKILL.md
    agents/openai.yaml
    references/stage2-shared-rules.md
  stage2-optimize-cheatsheet/
    SKILL.md
    agents/openai.yaml
    references/stage2-shared-rules.md
    references/cheatsheet-editing-rules.md
  stage2-version-cheatsheet/
    SKILL.md
    agents/openai.yaml
    references/stage2-shared-rules.md
    references/versioning-rules.md
```

以及以下文档更新：

- `docs/architecture.md`
- `docs/README.md`

## 延后工作

- `stage2-loop` 总控技能
- 技能专用脚本包装层
- 基于 accept/reject 门槛的自动候选复评
- 与后续 experiment harness 的更深集成
- `drafts/` 创建与提升（promote）脚本或专用 skill 的拆分
