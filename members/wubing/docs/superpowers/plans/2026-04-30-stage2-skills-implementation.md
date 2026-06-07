# Stage 2 技能体系 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在仓库根目录 `skills/` 下落地第一版 `stage2-*` 项目私有技能，并补齐最小测试与项目文档接入。

**Architecture:** 技能层只做流程编排、约束和项目知识组织，不复制现有 CLI 业务逻辑。4 个技能共用一套 Stage 2 共享规则，并通过 `references/` 拆出 evaluator 默认参数、cheatsheet 编辑规则和版本冻结规则；测试侧用一个轻量测试文件校验技能目录、frontmatter、关键 reference 文件和文档接入是否存在。

**Tech Stack:** Markdown `SKILL.md`, YAML `agents/openai.yaml`, pytest, Python 标准库, 现有 `scripts/*` CLI.

---

## File Map

- `skills/stage2-evaluate/SKILL.md`
  - 记录评测技能的触发条件、默认参数、执行顺序和禁止行为。
- `skills/stage2-evaluate/agents/openai.yaml`
  - 提供 UI/发现层需要的稳定技能元数据。
- `skills/stage2-evaluate/references/stage2-shared-rules.md`
  - 记录所有 `stage2-*` 技能共用的硬约束。
- `skills/stage2-evaluate/references/evaluator-defaults.md`
  - 记录 evaluator 默认参数、默认 cheatsheet 路径和 Lean backend 约定。
- `skills/stage2-analyze-run/SKILL.md`
  - 记录 run 分析技能的触发条件、读写边界和固定输出。
- `skills/stage2-analyze-run/agents/openai.yaml`
  - 提供 `stage2-analyze-run` 的稳定技能元数据。
- `skills/stage2-analyze-run/references/stage2-shared-rules.md`
  - 与其他技能保持一致的共享规则副本。
- `skills/stage2-optimize-cheatsheet/SKILL.md`
  - 记录 cheatsheet 工作态编辑流程和禁止行为。
- `skills/stage2-optimize-cheatsheet/agents/openai.yaml`
  - 提供 `stage2-optimize-cheatsheet` 的稳定技能元数据。
- `skills/stage2-optimize-cheatsheet/references/stage2-shared-rules.md`
  - 与其他技能保持一致的共享规则副本。
- `skills/stage2-optimize-cheatsheet/references/cheatsheet-editing-rules.md`
  - 约束 `current/` 下中英文 cheatsheet 和 `manifest.json` 的编辑方式。
- `skills/stage2-version-cheatsheet/SKILL.md`
  - 记录版本冻结技能的输入、输出和禁止回写规则。
- `skills/stage2-version-cheatsheet/agents/openai.yaml`
  - 提供 `stage2-version-cheatsheet` 的稳定技能元数据。
- `skills/stage2-version-cheatsheet/references/stage2-shared-rules.md`
  - 与其他技能保持一致的共享规则副本。
- `skills/stage2-version-cheatsheet/references/versioning-rules.md`
  - 约束版本号格式、冻结时机和 test split 使用边界。
- `tests/test_stage2_skills.py`
  - 校验技能目录结构、frontmatter 关键字段、`openai.yaml` 默认 prompt、关键 reference 规则和文档接入。
- `docs/README.md`
  - 记录仓库私有技能目录和用途。
- `docs/architecture.md`
  - 记录 `stage2-*` 技能在整体架构中的职责边界。

---

## Chunk 1: 测试与技能骨架

### Task 1: 为技能目录和元数据写失败测试

**Files:**
- Create: `tests/test_stage2_skills.py`
- Reference: `docs/superpowers/specs/2026-04-30-stage2-skills-design.md`

- [ ] **Step 1: 写第一个失败测试，断言 4 个技能目录存在**

```python
from pathlib import Path


def test_stage2_skill_directories_exist():
    root = Path(__file__).resolve().parents[1]
    expected = [
        root / "skills" / "stage2-evaluate",
        root / "skills" / "stage2-analyze-run",
        root / "skills" / "stage2-optimize-cheatsheet",
        root / "skills" / "stage2-version-cheatsheet",
    ]
    for path in expected:
        assert path.is_dir(), f"missing skill directory: {path}"
```

- [ ] **Step 2: 运行单测并确认失败**

Run: `pytest tests/test_stage2_skills.py::test_stage2_skill_directories_exist -v`
Expected: FAIL，提示缺少 `skills/stage2-*` 目录。

- [ ] **Step 3: 扩展同一个测试文件，增加 frontmatter 与资源文件断言**

```python
import re


def frontmatter_text(skill_dir: Path) -> str:
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    assert match, f"missing frontmatter in {skill_dir / 'SKILL.md'}"
    return match.group(1)


def test_stage2_skill_frontmatter_and_resources():
    skill_dir = Path(__file__).resolve().parents[1] / "skills" / "stage2-evaluate"
    frontmatter = frontmatter_text(skill_dir)
    assert "name: stage2-evaluate" in frontmatter
    assert "description:" in frontmatter
    assert (skill_dir / "agents" / "openai.yaml").exists()
    assert (skill_dir / "references" / "stage2-shared-rules.md").exists()
```

- [ ] **Step 4: 运行新增断言并确认仍然失败**

Run: `pytest tests/test_stage2_skills.py -v`
Expected: FAIL，提示 `SKILL.md`、`openai.yaml` 或 reference 文件不存在。

- [ ] **Step 5: 提交测试骨架**

```bash
git add tests/test_stage2_skills.py
git commit -m "test: add stage2 skill scaffolding checks"
```

### Task 2: 创建共享 reference 骨架与空技能目录

**Files:**
- Create: `skills/stage2-evaluate/SKILL.md`
- Create: `skills/stage2-evaluate/agents/openai.yaml`
- Create: `skills/stage2-evaluate/references/stage2-shared-rules.md`
- Create: `skills/stage2-evaluate/references/evaluator-defaults.md`
- Create: `skills/stage2-analyze-run/SKILL.md`
- Create: `skills/stage2-analyze-run/agents/openai.yaml`
- Create: `skills/stage2-analyze-run/references/stage2-shared-rules.md`
- Create: `skills/stage2-optimize-cheatsheet/SKILL.md`
- Create: `skills/stage2-optimize-cheatsheet/agents/openai.yaml`
- Create: `skills/stage2-optimize-cheatsheet/references/stage2-shared-rules.md`
- Create: `skills/stage2-optimize-cheatsheet/references/cheatsheet-editing-rules.md`
- Create: `skills/stage2-version-cheatsheet/SKILL.md`
- Create: `skills/stage2-version-cheatsheet/agents/openai.yaml`
- Create: `skills/stage2-version-cheatsheet/references/stage2-shared-rules.md`
- Create: `skills/stage2-version-cheatsheet/references/versioning-rules.md`

- [ ] **Step 1: 创建目录结构**

```text
skills/
  stage2-evaluate/
    agents/
    references/
  stage2-analyze-run/
    agents/
    references/
  stage2-optimize-cheatsheet/
    agents/
    references/
  stage2-version-cheatsheet/
    agents/
    references/
```

- [ ] **Step 2: 为每个技能写最小合法 frontmatter**

```markdown
---
name: stage2-evaluate
description: Use when running a reproducible Stage 2 evaluator pass for this repository with the standard Stage 2 constraints and artifacts.
---
```

对另外 3 个技能分别替换为各自名字和职责描述，保证只使用小写、数字和连字符。

- [ ] **Step 3: 为每个技能写最小 `agents/openai.yaml`**

```yaml
interface:
  display_name: "Stage2 Evaluate"
  short_description: "Run the Stage 2 evaluator"
  default_prompt: "Use $stage2-evaluate to run a Stage 2 evaluator pass in this repository."

policy:
  allow_implicit_invocation: true
```

其余技能按相同结构填写，`default_prompt` 必须显式提到对应的 `$stage2-*` 技能名。

- [ ] **Step 4: 先写共享 reference 骨架，再写技能专属 reference 骨架**

`stage2-shared-rules.md` 至少要覆盖：

```markdown
# Stage 2 Shared Rules

- Use files on disk as the only handoff surface between skills.
- Do not inject evidence bank files into evaluator runtime input.
- Do not modify model-produced Lean code after the LLM call.
- Use test split only after a cheatsheet candidate is frozen.
```

`evaluator-defaults.md`、`cheatsheet-editing-rules.md`、`versioning-rules.md` 先写最小章节标题和 4-8 条硬规则，后续再补到完整内容。

- [ ] **Step 5: 运行技能测试，确认目录与最小资源存在**

Run: `pytest tests/test_stage2_skills.py -v`
Expected: 部分测试可能仍失败，但“目录存在”和“文件存在”断言应开始通过。

- [ ] **Step 6: 提交技能骨架**

```bash
git add skills tests/test_stage2_skills.py
git commit -m "feat: scaffold stage2 skills"
```

## Chunk 2: 技能正文与项目文档

### Task 3: 补全 4 个 `SKILL.md` 的触发条件、执行流程和硬约束

**Files:**
- Modify: `skills/stage2-evaluate/SKILL.md`
- Modify: `skills/stage2-analyze-run/SKILL.md`
- Modify: `skills/stage2-optimize-cheatsheet/SKILL.md`
- Modify: `skills/stage2-version-cheatsheet/SKILL.md`
- Reference: `scripts/evaluator/run_stage2_evaluator.py`
- Reference: `scripts/evaluator/run_stage2_smoke.py`
- Reference: `scripts/error_analysis/analyze_stage2_run.py`
- Reference: `scripts/cheatsheets/version_cheatsheet.py`

- [ ] **Step 1: 为 `stage2-evaluate` 写完整工作流**

最少包含：
- 什么时候触发
- 默认 dataset / cheatsheet / concurrency 约定
- 先检查 `run_dir`，再运行 `scripts/evaluator/run_stage2_evaluator.py`
- 禁止 evidence runtime injection 和 LLM 后修复

- [ ] **Step 2: 为 `stage2-analyze-run` 写完整工作流**

最少包含：
- 只在 `run_dir` 已存在时触发
- 优先读取已有 `summary.json`、`per_run.jsonl`
- 运行 `scripts/error_analysis/analyze_stage2_run.py`
- 只写分析产物，不改原始 run 记录

- [ ] **Step 3: 为 `stage2-optimize-cheatsheet` 写完整工作流**

最少包含：
- 先读取 `failure_taxonomy.json`、`errors.jsonl`、`analysis.md`
- 只修改 `cheatsheets/<stage>/current/`
- 同步更新 `.en.md`、`.zh.md` 与 `manifest.json`
- 禁止写单题特判、禁止修改 `versions/`

- [ ] **Step 4: 为 `stage2-version-cheatsheet` 写完整工作流**

最少包含：
- 读取 `current/` 中英文文件和来源 `summary.json`
- 调用 `scripts/cheatsheets/version_cheatsheet.py`
- 明确版本目录输出和禁止回写 `current/`

- [ ] **Step 5: 运行 quick validator 校验 4 个技能**

Run:

```bash
python /home/bing/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/stage2-evaluate
python /home/bing/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/stage2-analyze-run
python /home/bing/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/stage2-optimize-cheatsheet
python /home/bing/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/stage2-version-cheatsheet
```

Expected: 四条命令都输出 `Skill is valid!`

- [ ] **Step 6: 提交技能正文**

```bash
git add skills
git commit -m "feat: add stage2 skill instructions"
```

### Task 4: 更新项目文档，让技能目录和职责进入仓库事实来源

**Files:**
- Modify: `docs/README.md`
- Modify: `docs/architecture.md`
- Reference: `docs/superpowers/specs/2026-04-30-stage2-skills-design.md`

- [ ] **Step 1: 为文档写失败测试，断言 `docs/README.md` 提到 `skills/`**

```python
def test_docs_readme_mentions_workspace_skills():
    text = (Path(__file__).resolve().parents[1] / "docs" / "README.md").read_text(encoding="utf-8")
    assert "skills/" in text
    assert "stage2-" in text
```

- [ ] **Step 2: 追加失败测试，断言 `docs/architecture.md` 提到 `stage2-*` 技能角色**

```python
def test_architecture_mentions_stage2_skills_role():
    text = (Path(__file__).resolve().parents[1] / "docs" / "architecture.md").read_text(encoding="utf-8")
    assert "stage2-*" in text
    assert "编排" in text
```

- [ ] **Step 3: 运行文档断言并确认失败**

Run: `pytest tests/test_stage2_skills.py -v`
Expected: FAIL，提示文档尚未提到 `skills/` 或 `stage2-*` 技能角色。

- [ ] **Step 4: 更新 `docs/README.md`**

加入一条新的核心目录说明，例如：

```markdown
- `../skills/`：仓库内项目私有技能目录，保存 `stage2-*` 比赛技能。
```

并说明这些技能用于编排评测、分析 run、优化工作态 cheatsheet 和冻结候选。

- [ ] **Step 5: 更新 `docs/architecture.md`**

在“实验闭环层”或相邻位置补一小节，明确：
- `stage2-*` 技能放在仓库根目录 `skills/`
- 技能负责流程编排、错误分析消费规则和 `current/` cheatsheet 编辑
- evaluator 与后续 harness 仍是确定性执行主体

- [ ] **Step 6: 运行文档断言并确认通过**

Run: `pytest tests/test_stage2_skills.py -v`
Expected: 文档相关测试 PASS。

- [ ] **Step 7: 提交文档接入**

```bash
git add docs/README.md docs/architecture.md tests/test_stage2_skills.py
git commit -m "docs: document stage2 project skills"
```

## Chunk 3: 回归校验与收尾

### Task 5: 扩展测试，覆盖 `openai.yaml` 和 reference 内容的关键约束

**Files:**
- Modify: `tests/test_stage2_skills.py`

- [ ] **Step 1: 为 `openai.yaml` 增加静态内容校验**

```python
def test_openai_yaml_mentions_matching_skill_name():
    text = (
        Path(__file__).resolve().parents[1]
        / "skills"
        / "stage2-evaluate"
        / "agents"
        / "openai.yaml"
    ).read_text(encoding="utf-8")
    assert 'default_prompt: "Use $stage2-evaluate' in text
    assert "allow_implicit_invocation: true" in text
```

- [ ] **Step 2: 为 reference 文件增加关键规则校验**

```python
def test_shared_rules_forbid_runtime_evidence_and_post_llm_rewrites():
    text = (
        Path(__file__).resolve().parents[1]
        / "skills"
        / "stage2-evaluate"
        / "references"
        / "stage2-shared-rules.md"
    ).read_text(encoding="utf-8")
    assert "Do not inject evidence bank files into evaluator runtime input." in text
    assert "Do not modify model-produced Lean code after the LLM call." in text
```

- [ ] **Step 3: 运行新增测试并在必要时微调技能文件**

Run: `pytest tests/test_stage2_skills.py -v`
Expected: PASS；如失败，只修改对应技能文件，不扩大范围。

- [ ] **Step 4: 提交测试补强**

```bash
git add tests/test_stage2_skills.py skills
git commit -m "test: verify stage2 skill metadata"
```

### Task 6: 运行完整目标校验并整理最终变更

**Files:**
- Verify: `skills/stage2-evaluate/**`
- Verify: `skills/stage2-analyze-run/**`
- Verify: `skills/stage2-optimize-cheatsheet/**`
- Verify: `skills/stage2-version-cheatsheet/**`
- Verify: `tests/test_stage2_skills.py`
- Verify: `docs/README.md`
- Verify: `docs/architecture.md`

- [ ] **Step 1: 跑目标测试文件**

Run: `pytest tests/test_stage2_skills.py -v`
Expected: PASS

- [ ] **Step 2: 跑相关已有测试，确认没有破坏现有 CLI**

Run:

```bash
pytest tests/test_analyze_stage2_run.py tests/test_cheatsheet_versions.py tests/test_evaluator_components.py -q
```

Expected: PASS

- [ ] **Step 3: 再跑 4 个技能 quick validator**

Run:

```bash
python /home/bing/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/stage2-evaluate
python /home/bing/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/stage2-analyze-run
python /home/bing/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/stage2-optimize-cheatsheet
python /home/bing/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/stage2-version-cheatsheet
```

Expected: 四条命令都输出 `Skill is valid!`

- [ ] **Step 4: 检查变更范围**

Run: `git status --short`
Expected: 只包含 `skills/`、`tests/test_stage2_skills.py`、`docs/README.md`、`docs/architecture.md` 和计划/规格文档相关变更；不应出现 evaluator 业务逻辑改动。

- [ ] **Step 5: 最终提交实现**

```bash
git add skills tests/test_stage2_skills.py docs/README.md docs/architecture.md
git commit -m "feat: add stage2 project skills"
```
