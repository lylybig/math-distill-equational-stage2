# Stage 2 Cheatsheet Drafts Layer Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `cheatsheets/<stage>/current/` 和 `cheatsheets/<stage>/versions/` 之间引入 `drafts/` 层，让每次评测前快照、实验结果和 promote/reject 决策都有可复现记录。

**Architecture:** `current/` 继续作为唯一可写工作态；评测前先把 `current/` 固定成只读 `drafts/<draft-id>/` 快照，再用该 draft 参与评测；只有验证通过的 draft 才允许冻结到 `versions/`。确定性落盘逻辑放进 `src/math_distill_stage2/`，CLI 只做参数解析和调用。

**Tech Stack:** Python CLI wrappers, JSON manifests, Markdown cheatsheets, pytest.

---

## File Map

- `src/math_distill_stage2/cheatsheets/drafts.py`
  - 封装 draft 创建、manifest 生成、哈希计算和 run 绑定更新。
- `src/math_distill_stage2/cheatsheets/__init__.py`
  - 暴露 draft 相关公共函数，供脚本与测试使用。
- `scripts/cheatsheets/create_draft_cheatsheet.py`
  - 从 `current/` 创建 `drafts/<draft-id>/` 的命令行入口。
- `scripts/cheatsheets/version_cheatsheet.py`
  - 改成优先从 `draft` 冻结到 `versions/`，而不是默认直接从 `current/` 冻结。
- `tests/test_cheatsheet_drafts.py`
  - 校验 draft 创建、manifest 字段、只读快照语义和 CLI `--help`。
- `tests/test_cheatsheet_versions.py`
  - 更新版本冻结测试，使其覆盖 “draft -> version” 路径。
- `skills/stage2-evaluate/SKILL.md`
  - 改成“评测前必建 draft”。
- `skills/stage2-evaluate/references/evaluator-defaults.md`
  - 记录从 `current/` 发起评测时的 draft 创建要求。
- `skills/stage2-optimize-cheatsheet/SKILL.md`
  - 明确只能改 `current/`，不能回写现有 draft。
- `skills/stage2-optimize-cheatsheet/references/cheatsheet-editing-rules.md`
  - 加入 `current/`、`drafts/`、`versions/` 的写权限边界。
- `skills/stage2-version-cheatsheet/SKILL.md`
  - 改成“从已验证 draft 冻结到 version”。
- `skills/stage2-version-cheatsheet/references/versioning-rules.md`
  - 记录 promote 条件和禁止直接 `current -> version` 的规则。
- `tests/test_stage2_skills.py`
  - 更新 skill 文案与文档断言，使其覆盖 `drafts/` 层。
- `docs/architecture.md`
  - 记录 `current/`、`drafts/`、`versions/` 三层生命周期。
- `docs/cheatsheet-optimization.md`
  - 更新 cheatsheet 优化流程，使每次评测前先建 draft。
- `docs/README.md`
  - 如有需要，补一条 `drafts/` 生命周期说明。
- `cheatsheets/smoke/drafts/.gitkeep`
  - 预留 smoke stage 的 draft 根目录。
- `cheatsheets/mini/drafts/.gitkeep`
  - 预留 mini stage 的 draft 根目录。

---

## Chunk 1: Draft 创建能力

### Task 1: 先写失败测试，定义 draft 的最小行为

**Files:**
- Create: `tests/test_cheatsheet_drafts.py`
- Reference: `docs/superpowers/specs/2026-04-30-stage2-skills-design.md`

- [ ] **Step 1: 写第一个失败测试，要求从 `current/` 创建 draft 目录**

```python
from pathlib import Path

from math_distill_stage2.cheatsheets.drafts import create_draft_cheatsheet


def test_create_draft_cheatsheet_copies_runtime_and_review_files(tmp_path: Path):
    current_dir = tmp_path / "cheatsheets" / "smoke" / "current"
    current_dir.mkdir(parents=True)
    (current_dir / "stage2_judge_json_certificate.en.md").write_text("en", encoding="utf-8")
    (current_dir / "stage2_judge_json_certificate.zh.md").write_text("zh", encoding="utf-8")
    (current_dir / "manifest.json").write_text("{}", encoding="utf-8")

    manifest = create_draft_cheatsheet(
        current_dir=current_dir,
        drafts_root=tmp_path / "cheatsheets" / "smoke" / "drafts",
        draft_id="draft-1",
        based_on="mini-v1",
        notes="before smoke rerun",
    )

    draft_dir = tmp_path / "cheatsheets" / "smoke" / "drafts" / "draft-1"
    assert (draft_dir / "stage2_judge_json_certificate.en.md").read_text(encoding="utf-8") == "en"
    assert (draft_dir / "stage2_judge_json_certificate.zh.md").read_text(encoding="utf-8") == "zh"
    assert manifest["draft_id"] == "draft-1"
```

- [ ] **Step 2: 运行该测试并确认失败**

Run: `pytest tests/test_cheatsheet_drafts.py::test_create_draft_cheatsheet_copies_runtime_and_review_files -v`
Expected: FAIL，因为 `math_distill_stage2.cheatsheets.drafts` 或 `create_draft_cheatsheet` 尚不存在。

- [ ] **Step 3: 追加失败测试，要求 draft manifest 记录来源、哈希和状态**

```python
def test_create_draft_cheatsheet_writes_manifest_with_source_metadata(tmp_path: Path):
    ...
    assert manifest["based_on"] == "mini-v1"
    assert manifest["status"] == "pending_eval"
    assert manifest["runtime_cheatsheet"]["sha256"]
    assert manifest["review_cheatsheet"]["sha256"]
```

- [ ] **Step 4: 追加 CLI `--help` 失败测试**

```python
import subprocess
import sys


def test_create_draft_cheatsheet_script_help_runs():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "scripts/cheatsheets/create_draft_cheatsheet.py", "--help"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "--draft-id" in result.stdout
```

- [ ] **Step 5: 跑整个测试文件并确认仍然失败**

Run: `pytest tests/test_cheatsheet_drafts.py -v`
Expected: FAIL，失败原因应当只与 draft 功能缺失相关。

- [ ] **Step 6: 提交测试骨架**

```bash
git add tests/test_cheatsheet_drafts.py
git commit -m "test: define cheatsheet draft snapshot behavior"
```

### Task 2: 实现 deterministic draft 创建逻辑

**Files:**
- Create: `src/math_distill_stage2/cheatsheets/drafts.py`
- Create: `src/math_distill_stage2/cheatsheets/__init__.py`
- Create: `scripts/cheatsheets/create_draft_cheatsheet.py`
- Create: `cheatsheets/smoke/drafts/.gitkeep`
- Create: `cheatsheets/mini/drafts/.gitkeep`

- [ ] **Step 1: 在 `src/math_distill_stage2/cheatsheets/drafts.py` 写最小实现**

最小接口建议：

```python
def create_draft_cheatsheet(
    *,
    current_dir: Path,
    drafts_root: Path,
    draft_id: str,
    based_on: str,
    notes: str = "",
    source_run: str = "",
) -> dict[str, Any]:
    ...
```

返回 manifest，至少包含：
- `draft_id`
- `based_on`
- `status`
- `created_at_utc`
- `runtime_cheatsheet`
- `review_cheatsheet`
- `source_run`
- `notes`

- [ ] **Step 2: 让实现通过第一个复制测试**

Run: `pytest tests/test_cheatsheet_drafts.py::test_create_draft_cheatsheet_copies_runtime_and_review_files -v`
Expected: PASS

- [ ] **Step 3: 补 manifest 字段与哈希逻辑，直到第二个测试通过**

Run: `pytest tests/test_cheatsheet_drafts.py::test_create_draft_cheatsheet_writes_manifest_with_source_metadata -v`
Expected: PASS

- [ ] **Step 4: 添加 CLI 包装脚本**

参数至少包含：
- `--current-dir`
- `--drafts-root`
- `--draft-id`
- `--based-on`
- `--notes`
- `--source-run`

- [ ] **Step 5: 跑 CLI `--help` 测试**

Run: `pytest tests/test_cheatsheet_drafts.py::test_create_draft_cheatsheet_script_help_runs -v`
Expected: PASS

- [ ] **Step 6: 跑整个 draft 测试文件**

Run: `pytest tests/test_cheatsheet_drafts.py -v`
Expected: PASS

- [ ] **Step 7: 提交 draft 创建能力**

```bash
git add src/math_distill_stage2/cheatsheets scripts/cheatsheets/create_draft_cheatsheet.py cheatsheets/smoke/drafts/.gitkeep cheatsheets/mini/drafts/.gitkeep tests/test_cheatsheet_drafts.py
git commit -m "feat: add cheatsheet draft snapshots"
```

## Chunk 2: Draft 到 Version 的提升路径

### Task 3: 先写失败测试，要求 `version_cheatsheet.py` 以 draft 为主要输入

**Files:**
- Modify: `tests/test_cheatsheet_versions.py`
- Reference: `scripts/cheatsheets/version_cheatsheet.py`

- [ ] **Step 1: 增加失败测试，要求从 `draft_dir` 冻结 version**

```python
def test_version_cheatsheet_freezes_from_draft_dir(tmp_path: Path):
    draft_dir = tmp_path / "drafts" / "draft-1"
    draft_dir.mkdir(parents=True)
    (draft_dir / "stage2_judge_json_certificate.en.md").write_text("body", encoding="utf-8")
    (draft_dir / "stage2_judge_json_certificate.zh.md").write_text("review", encoding="utf-8")
    (draft_dir / "manifest.json").write_text('{"draft_id":"draft-1"}', encoding="utf-8")
    ...
```

- [ ] **Step 2: 增加失败测试，要求输出 manifest 记录 `draft_id` 和 promote 来源**

```python
assert manifest["source_draft"] == "draft-1"
assert manifest["promoted_from"] == str(draft_dir)
```

- [ ] **Step 3: 跑目标测试并确认失败**

Run: `pytest tests/test_cheatsheet_versions.py -v`
Expected: FAIL，失败原因应当是 `version_cheatsheet.py` 还只面向 `current/`。

- [ ] **Step 4: 提交测试更新**

```bash
git add tests/test_cheatsheet_versions.py
git commit -m "test: require draft-based cheatsheet versioning"
```

### Task 4: 实现 `draft -> version` 提升逻辑

**Files:**
- Modify: `scripts/cheatsheets/version_cheatsheet.py`
- Test: `tests/test_cheatsheet_versions.py`

- [ ] **Step 1: 给 `version_cheatsheet` 增加 `draft_dir` 输入**

建议接口：

```python
def version_cheatsheet(
    *,
    draft_dir: Path,
    output_root: Path,
    version: str,
    ...
) -> dict[str, Any]:
    ...
```

内部从 `draft_dir` 读取：
- 英文运行版
- 中文复查版
- `manifest.json`

- [ ] **Step 2: 更新 CLI 参数**

至少新增：
- `--draft-dir`

并把默认行为改成：
- 若提供 `--draft-dir`，从 draft 冻结
- 不再默认鼓励 `current -> version`

- [ ] **Step 3: 运行 draft-based version 测试**

Run: `pytest tests/test_cheatsheet_versions.py -v`
Expected: PASS

- [ ] **Step 4: 保持旧 help 断言通过或按需更新**

Run: `pytest tests/test_cheatsheet_versions.py::test_version_cheatsheet_script_help_runs_when_invoked_by_path -v`
Expected: PASS

- [ ] **Step 5: 提交提升逻辑**

```bash
git add scripts/cheatsheets/version_cheatsheet.py tests/test_cheatsheet_versions.py
git commit -m "feat: freeze versioned cheatsheets from drafts"
```

## Chunk 3: Skill 与文档更新

### Task 5: 更新 skill 文案与 reference，先写断言再修改文档

**Files:**
- Modify: `tests/test_stage2_skills.py`
- Modify: `skills/stage2-evaluate/SKILL.md`
- Modify: `skills/stage2-evaluate/references/evaluator-defaults.md`
- Modify: `skills/stage2-optimize-cheatsheet/SKILL.md`
- Modify: `skills/stage2-optimize-cheatsheet/references/cheatsheet-editing-rules.md`
- Modify: `skills/stage2-version-cheatsheet/SKILL.md`
- Modify: `skills/stage2-version-cheatsheet/references/versioning-rules.md`

- [ ] **Step 1: 为 `tests/test_stage2_skills.py` 增加失败断言**

至少断言：
- `stage2-evaluate` 提到 `drafts/`
- `stage2-optimize-cheatsheet` 明确不改已有 draft
- `stage2-version-cheatsheet` 提到从 draft 冻结

- [ ] **Step 2: 跑技能测试并确认失败**

Run: `pytest tests/test_stage2_skills.py -v`
Expected: FAIL，失败原因来自旧 skill 文案未提 `drafts/`。

- [ ] **Step 3: 更新 3 个 skill 文档和 3 个 reference 文件**

关键点：
- `stage2-evaluate`: 评测前先建 draft
- `stage2-optimize-cheatsheet`: 只改 `current/`
- `stage2-version-cheatsheet`: `draft -> version`

- [ ] **Step 4: 跑技能测试并确认通过**

Run: `pytest tests/test_stage2_skills.py -v`
Expected: PASS

- [ ] **Step 5: 再跑 4 个 quick validator**

Run:

```bash
python /home/bing/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/stage2-evaluate
python /home/bing/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/stage2-analyze-run
python /home/bing/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/stage2-optimize-cheatsheet
python /home/bing/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/stage2-version-cheatsheet
```

Expected: 全部 `Skill is valid!`

- [ ] **Step 6: 提交 skill 更新**

```bash
git add skills tests/test_stage2_skills.py
git commit -m "docs: update stage2 skills for drafts lifecycle"
```

### Task 6: 更新项目文档与优化流程

**Files:**
- Modify: `docs/architecture.md`
- Modify: `docs/cheatsheet-optimization.md`
- Modify: `docs/README.md`

- [ ] **Step 1: 为文档写失败断言**

至少断言：
- `docs/architecture.md` 提到 `drafts/`
- `docs/cheatsheet-optimization.md` 提到“评测前先建 draft”

- [ ] **Step 2: 运行目标测试并确认失败**

可以先把断言加在 `tests/test_stage2_skills.py`，然后运行：
`pytest tests/test_stage2_skills.py -v`

- [ ] **Step 3: 更新 `docs/architecture.md`**

加入三层生命周期说明：
- `current/`
- `drafts/`
- `versions/`

- [ ] **Step 4: 更新 `docs/cheatsheet-optimization.md`**

补充：
- `drafts/` 目录结构
- 评测前必建 draft
- promote/reject 规则

- [ ] **Step 5: 如有必要，更新 `docs/README.md`**

只补最小必要说明，避免和架构文档重复。

- [ ] **Step 6: 运行文档断言并确认通过**

Run: `pytest tests/test_stage2_skills.py -v`
Expected: PASS

- [ ] **Step 7: 提交文档更新**

```bash
git add docs/architecture.md docs/cheatsheet-optimization.md docs/README.md tests/test_stage2_skills.py
git commit -m "docs: describe cheatsheet drafts lifecycle"
```

## Chunk 4: 回归校验

### Task 7: 跑目标回归并检查变更范围

**Files:**
- Verify: `src/math_distill_stage2/cheatsheets/**`
- Verify: `scripts/cheatsheets/create_draft_cheatsheet.py`
- Verify: `scripts/cheatsheets/version_cheatsheet.py`
- Verify: `skills/stage2-evaluate/**`
- Verify: `skills/stage2-optimize-cheatsheet/**`
- Verify: `skills/stage2-version-cheatsheet/**`
- Verify: `tests/test_cheatsheet_drafts.py`
- Verify: `tests/test_cheatsheet_versions.py`
- Verify: `tests/test_stage2_skills.py`

- [ ] **Step 1: 跑 draft 与 version 相关测试**

Run:

```bash
pytest tests/test_cheatsheet_drafts.py tests/test_cheatsheet_versions.py tests/test_stage2_skills.py -q
```

Expected: PASS

- [ ] **Step 2: 跑已有相关回归**

Run:

```bash
pytest tests/test_analyze_stage2_run.py tests/test_evaluator_components.py -q
```

Expected: PASS

- [ ] **Step 3: 检查变更范围**

Run: `git status --short`
Expected: 只包含 cheatsheet draft 相关源码、脚本、skills、docs 和测试；不应出现 evaluator 业务逻辑改动。

- [ ] **Step 4: 最终提交实现**

```bash
git add src/math_distill_stage2/cheatsheets scripts/cheatsheets/create_draft_cheatsheet.py scripts/cheatsheets/version_cheatsheet.py skills docs tests cheatsheets/smoke/drafts/.gitkeep cheatsheets/mini/drafts/.gitkeep
git commit -m "feat: add cheatsheet drafts lifecycle"
```
