# CLAUDE.md - wubing 个人工作区

> 这份文件只约束 Claude Code 在 `members/wubing/` 内的行为。
> 项目级原则在根 [CLAUDE.md](../../CLAUDE.md)，仍然适用。

## 工作根目录

- 个人工作根目录是 `members/wubing/`。
- 本目录内的相对路径默认从 `members/wubing/` 解释，例如 `src/`、`scripts/`、`tests/`、`docs/`、`data/`、`external/`、`solvers/` 和 `submissions/`。
- 如果当前 shell 在团队 monorepo 根目录，先 `cd members/wubing`，或把命令工具的 `workdir` 设为 `members/wubing/`。

## 不要跨界

- 不要编辑 `members/` 下其他成员的目录。
- 不要顺手修改 monorepo 根目录的公共 `docs/`、`datasets/`、`solvers/` 或 `scripts/`；公共改动单独走团队 PR。
- Stage 2 solver、proof bank、strategy registry 的具体工作流以 `AGENTS.md` 和 `skills/stage2-*/` 为准。

## 常用验证

```bash
pytest tests/skills/test_stage2_skills.py -q
pytest tests/official/test_official_solo_submission.py -q
```
