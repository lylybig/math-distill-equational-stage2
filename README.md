# ETP Stage 2 — Team Workspace

> Equational Theories Project · Stage 2 蒸馏赛道协作主仓库

## 一句话目标

在 2026-08-31 截止前，把 ETP 4694 方程之间的 **全图 ~22M 蕴含对** 解到 ≥ 90%（中期）／ ≥ 98%（长期）。1669 题 contest benchmark 只是采样，**不是真目标**。

## 当前状态

- 主里程碑：见 [ROADMAP.md](ROADMAP.md)
- 各成员最佳分数：见 [SCOREBOARD.md](SCOREBOARD.md)
- 本周周报：见 [docs/weekly/](docs/weekly/)
- 攻不下的题：见 [docs/known_intractable.md](docs/known_intractable.md)

## 仓库地图（main 分支）

```
solvers/           共享代码 (engines.py + baseline_solver_v3e.py)
datasets/       数据源说明 (大数据在 third_party / lawbook 本地生成)
docs/           知识库 (周报 / 蓝图 / playbook / glossary)
scripts/        手动运行工具 (run_eval.sh, run_eval.py, run_generic.py)
judge_service/  FastAPI judge 微服务 (本地或团队远端)
third_party/    外部 git submodule
  equational-theories-lean-stage2/   官方比赛仓
  equational_theories/               teorth/Tao 原始 ETP (22M 蕴含 + 反例族)
members/
  _template/    新成员复制此目录起步 (main 上的唯一 members/ 内容)
.env.example    LLM + judge 环境变量模板, 拷贝为 .env 后填 key
```

> **main 分支只有公共部分**。每个队员有自己的长期分支 `member/<name>`，
> 在那个分支上才有 `members/<name>/` 工作目录。

第三方仓库挂在 `third_party/` 下做 submodule，首次 clone 后跑：

```bash
git submodule update --init --recursive
```

详见 [third_party/README.md](third_party/README.md)。

## 分支模型

| 分支 | 内容 | 谁推 |
|---|---|---|
| `main` | `solvers/` `datasets/` `docs/` `members/_template/` | 走 PR + review |
| `member/wubing` | 同上 + `members/wubing/` 工作目录 | 仅吴兵 |
| `member/zhangkang` | 同上 + `members/zhangkang/` | 仅张康 |
| `member/yanliang` | 同上 + `members/yanliang/` | 仅严亮 |
| `feat/*` | 公共改动短期分支 → PR 进 main | 提案人 |

每个 member 分支**长期跟踪 main**：

```bash
# 你的日常 (在 member/<你> 分支上)
git fetch origin
git merge origin/main      # 把 main 上的 solvers/docs 更新合进来
# 或 git rebase origin/main 如果想保持线性历史
```

## 新人 60 秒上手

```bash
git clone <repo>
cd etp-stage2-team
git submodule update --init --recursive        # 拉 third_party/
cp .env.example .env                           # 然后填 OPENAI_API_KEY
git checkout -b member/<your_pinyin> main      # 从 main 开你的长期分支
cp -R members/_template members/<your_pinyin>  # 起步代码
# 编辑器全局替换: __MEMBER__ → <your_pinyin>
# 改 README.md / BLUEPRINT.md / solver.py
git add members/<your_pinyin>
git commit -m "init member <your_pinyin>"
git push -u origin member/<your_pinyin>
```

## 互看队友代码

```bash
git fetch origin
git log --all --oneline --graph    # 看全图

# 切到队友分支看
git switch member/zhangkang

# 或开个独立 worktree 不打断自己工作
git worktree add ../peek-zhangkang member/zhangkang
```

## 项目原则（务必先读）

[CLAUDE.md](CLAUDE.md)：**通用引擎、不写题面针对性 hardcoded**。

## 协作流程

详见 [CONTRIBUTING.md](CONTRIBUTING.md)。要点：
- main 永远是公共脚手架，**任何人的 members/<name>/ 都不在 main 上**
- 你 99% 时间待在自己的 `member/<你>` 分支
- 公共改动 → 从 main 起 `feat/<topic>` → PR
- 大文件 / 实验输出 → GitHub Releases，不入 git
- 没有 CI、没有自动化脚本，全部人工流程
