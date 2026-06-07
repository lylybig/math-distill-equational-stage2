# ADR-0001: Monorepo, main 为公共脚手架，每人长期分支

- **Status**: accepted
- **Date**: 2026-05-25
- **Driver**: 组长
- **Reviewers**: 全员

## Context

ETP Stage 2 是个 3.5 个月的小组比赛 (2026-05 → 2026-08-31)，4-8 人。需要：

- 共享底层能力 (judge, closure graph, cex families) 避免重复造轮子
- 每人有独立实验区，互不干扰
- 周报 / scoreboard / 知识库统一沉淀
- 邀请制 private repo

候选方案：

- (a) Multi-repo + submodule
- (b) Multi-repo + fork-and-PR
- (c) Monorepo + 各人目录都在 main + 长期分支兜底
- (d) Monorepo + main 严格公共 + 每人长期分支 ← **本 ADR 采纳**

## Decision

采纳 **(d) Monorepo + main 严格公共 + 每人长期分支**：

```
main                公共部分: solvers/ datasets/ docs/ + members/_template/
member/<name>       个人长期分支 (从 main 起): 同上 + members/<name>/
feat/<topic>        公共改动短期分支 → PR 进 main
```

- main **永远干净**：核心代码 + 数据集 + 文档 + 模板，无任何个人工作目录
- 每个队员在自己的 `member/<name>` 分支上自由 push，不需要 review
- 公共改动走 `feat/<topic>` → PR → main，回 sync 由各 member 分支 owner 自己 merge
- 大输出 (log / cex) 走 GitHub Releases，不入库

## Consequences

**好处**:
- main 极简，**第三方/新人看 main 就懂项目结构**
- 个人分支天然隔离，互不污染 (即使被 force-push 也不影响别人)
- solvers 的变更不会被个人实验脏 commit 淹没
- 每个分支可以独立做 release / 提交比赛包

**代价**:
- 互看队友代码需要 `git fetch && git switch`，比直接 `pull` 多一步
  - 缓解：推荐 `git worktree` 起独立目录看
- 每个 member 分支 owner 要定期 `git merge origin/main` 同步公共改动
  - 缓解：约定每周一次
- SCOREBOARD.md 等公共文件不在你的分支上当前 commit 体现，更新要切回 main 起 PR

**风险**:
- 有人在 main 上直接加 `members/<name>/` → review 时拦截 + ADR 明文禁止
- 有人 force-push 自己的 member 分支删队友 commit (理论上不会，因为只有 owner 改) → 仍要 enable GitHub branch protection 防误操作
- 巨型输出 commit 进 main 或 member 分支 → 靠 review + `.gitignore` 兜底

## Alternatives Considered

- **(a) Multi-repo + submodule**: 每人独立仓库，主仓 submodule → 互看代码要换仓，分享 solvers 难
- **(b) Fork-and-PR**: 主仓只放 solvers/，队员 fork 改 solver → 不利于实时互看实验进展
- **(c) main 直挂个人目录**: 队员 `members/<你>/` 直接在 main 上 → main 历史会被个人 commit 淹没，且四五人并行 push main 时易冲突

## References

- root `README.md` / `CONTRIBUTING.md`
- 决策当时的需求讨论：保留在仓库初始化 commit 与本 ADR 修订历史
