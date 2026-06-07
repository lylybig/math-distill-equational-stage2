# Contributing

## 分支模型

```
main                         公共部分：solvers/ datasets/ scripts/ judge_service/
                                       docs/ third_party/ + members/_template/
  ├── feat/<topic>           短期: 公共改动 → PR → 合回 main
  ├── member/wubing          长期: 吴兵的工作分支 (含 members/wubing/)
  ├── member/zhangkang       长期: 张康的工作分支 (含 members/zhangkang/)
  └── member/yanliang        长期: 严亮的工作分支 (含 members/yanliang/)
```

要点：
- **main 永远是公共脚手架**：核心代码 + 数据 + 工具脚本 + 文档 + 模板，无任何个人工作目录
- 每个队员 **99% 时间在自己的 `member/<你>` 分支**上 push
- 公共改动 → 从 main 起 `feat/<topic>` 短期分支 → PR + ≥ 1 review
- 没有 CI 工作流，但有**手动运行**的 `scripts/`（评测）+ `judge_service/`（判定服务）
- `.env` 不入 git，靠 `.env.example` 当模板

## 三类工作流

### 1. 日常：在自己的 `member/<你>` 分支上干活

```bash
git switch member/<你>
git fetch origin && git merge origin/main      # 先把 main 的更新拉进来
# 改 members/<你>/ 下任何东西, 可写自由实验脚本
git add members/<你>/
git commit -m "wubing: try superposition variant"
git push origin member/<你>
```

队友 `git fetch && git switch member/<你>` 即可查看。

### 2. 提案改公共区（solvers / datasets / docs）

```bash
git switch main && git pull
git checkout -b feat/<你>-<topic>
# 改 solvers/ 等
git push -u origin feat/<你>-<topic>
gh pr create --title "..." --body "..."
# 等 ≥ 1 人 review，合并
# 合并后, 每个 member 分支 owner 自己 git merge origin/main 把改动拉下来
```

### 3. 把自己分支上的成熟代码贡献到 solvers

如果你在 `member/<你>` 上发现一段引擎、family、工具足够通用，应该进 `solvers/`：

```bash
git switch main && git pull
git checkout -b feat/<你>-extract-<topic>
# 把相关文件从 members/<你>/ 复制 / 移动到 solvers/<...>/
# 在 docs/blueprints/ 写一个 ADR 说明动机
git push -u origin feat/<你>-extract-<topic>
gh pr create ...
```

> 注意 license / 归属：solvers/ 里的代码默认属于团队公共，作者署名靠 git history。

## 互看队友代码 / 实验

```bash
git fetch origin

# A) 直接切到队友分支看
git switch member/zhangkang

# B) 开个独立 worktree 不打断自己工作（推荐）
git worktree add ../peek-zhangkang member/zhangkang
# 用完: git worktree remove ../peek-zhangkang

# C) 跨分支查看单个文件
git show member/zhangkang:members/zhangkang/solver.py
```

## 大文件政策

- 单文件 > 1MB **不进 git**（人工自觉，review 时检查）
- 单 PR 总 diff > 5MB **不进 git**
- 实验原始输出（log / cex.jsonl / .lean.out）→ 打包后传 GitHub Releases
- 必要时启用 `git-lfs`

## solver.py 大小限制

比赛规定 `members/<你>/solver.py` ≤ 500KB。push 前自己 `ls -l` 检查。

## 周节奏（人工）

周报每周一个目录 `docs/weekly/YYYY-Www/`，里面**每人一个文件**：

```
docs/weekly/2026-W22/
├── _lead.md       (组长写)
├── wubing.md      (吴兵自己 PR 自己的)
├── zhangkang.md
└── yanliang.md
```

每人改自己那个文件，撞编辑零摩擦。详细操作见 [docs/weekly/README.md](docs/weekly/README.md)。

| 时间 | 动作 | 责任人 | 在哪个分支 |
|---|---|---|---|
| 周一上午 | 组长起本周骨架 PR（`mkdir docs/weekly/YYYY-Www && cp -R docs/weekly/_template/* ...`） | 组长 | `feat/weekly-YYYY-Www` |
| 周一—周四 | 自由 push `members/<你>/` | 全员 | 各人 `member/<你>` |
| 周五下午 | 每人 PR 自己那份 `docs/weekly/YYYY-Www/<你>.md` | 全员 | `feat/weekly-YYYY-Www-<你>` |
| 周五晚 | 组长合并所有 member PR + 写 `_lead.md` + PR | 组长 | — |
| 周五晚 | 组长跑 benchmark 后**手工**更新 `SCOREBOARD.md` | 组长 | `feat/scoreboard-YYYY-Www` PR |
| 周一例会 | 看上周完整周报 (`docs/weekly/<上周>/`) 调下周 | 全员 | — |

## 评测与成绩登记（人工）

1. 在自己 `member/<你>` 分支上用任意方式跑 benchmark
2. 在 `members/<你>/notes/cards/YYYY-MM-DD-<slug>.md` 写实验卡片，commit 到自己分支
3. 改 `SCOREBOARD.md` → 起 `feat/scoreboard-<你>-<date>` 短期分支 → PR
4. 巨型 log → tarball → `gh release upload`，卡片里贴 URL

## 把 main 的更新拉进自己的分支

main 上 solvers/ docs/ 更新后，每个 member 分支 owner 自己负责拉取：

```bash
git switch member/<你>
git fetch origin
git merge origin/main             # 推荐: 保留分叉历史
# 或
git rebase origin/main            # 想要线性历史
git push                          # rebase 后可能要 --force-with-lease, 仅你自己的分支可以
```

建议**每周至少 merge 一次** main，避免堆积冲突。

## 命名与编码

- **目录 / 文件**: snake_case
- **分支**:
  - `member/<name>` 长期个人分支
  - `feat/<topic>` 公共 PR
  - `member/<name>/wip-<topic>` 实在不想推到自己主分支的临时实验
- **commit**: 第一行 ≤ 50 字符，前缀 `<area>: <verb> <what>`，如 `solvers: extract closure BFS`
- **实验卡片**: `members/<you>/notes/cards/YYYY-MM-DD-<slug>.md`
- **反例族命名**: 用 paper §-name (`linear-sec`, `cyclic-sec`, `twisting-sec`)，不要 local nickname

## 项目原则

务必先读根 [CLAUDE.md](CLAUDE.md)：**通用引擎、不写题面针对性 hardcoded**。

## 评审清单（review 公共 PR 时）

- [ ] 是否引入了针对单题的 hardcoded？（应拒）
- [ ] 是否有对应跑分对照？（数字附在 PR description）
- [ ] 是否更新了 `docs/playbook/` 相应章节？
- [ ] 是否新增了 > 1MB 的文件？
- [ ] 是否破坏了 `members/_template/solver.py` 接口？
