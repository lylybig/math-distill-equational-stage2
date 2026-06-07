# third_party/

外部依赖。**只读**，不要在这里改代码 —— 改动靠改 submodule 指向的 commit。

## 模块清单

| 路径 | 上游 | 用途 |
|---|---|---|
| `equational-theories-lean-stage2/` | [SAIRcompetition/equational-theories-lean-stage2](https://github.com/SAIRcompetition/equational-theories-lean-stage2) | 比赛**官方** Lean 仓库。judge 规则、sandbox policy、submit 格式都以这里为准。 |
| `equational_theories/` | [teorth/equational_theories](https://github.com/teorth/equational_theories) | Terence Tao 原始 ETP 项目。完整的 ~22M 蕴含数据、论文级反例族、Vampire 翻译过的 superposition 证明。 |

## 初次拉取

```bash
git clone <repo>
cd etp-stage2-team
git submodule update --init --recursive
```

只想拉一个：

```bash
git submodule update --init third_party/equational_theories
```

## 更新 submodule 指向（团队操作）

```bash
git switch main && git pull
cd third_party/equational_theories
git fetch && git checkout <new-commit-or-tag>
cd ../..
git add third_party/equational_theories
git commit -m "deps: bump teorth/equational_theories to <commit-short>"
# PR 进 main
```

更新前确认：upstream 改动是否破坏现有 judge / data API？跑一轮 sample_200 对照。

## 各 member 分支拉取最新 submodule

main 上 submodule 升级后，每个 member 分支 owner 自己：

```bash
git switch member/<我>
git fetch origin && git merge origin/main
git submodule update --init --recursive
```

## 用途速查

### `equational-theories-lean-stage2/`

- judge 规则 + sandbox policy → `solvers/judge.py` / `policy.json`
- 提交格式样例 → `examples/`
- 评测脚本 → `scripts/run.sh`

### `equational_theories/`

- 全图 22M 蕴含数据 → `data/` (主要是 CSV / Lean 表)
- 已知所有反例族 → `EquationalTheories/Counterexamples/`
- Vampire / Z3 翻译后的 superposition 证明 → `EquationalTheories/Generated/`
- 论文 §-name 对应实现 → 按论文章节组织
- closure graph 数据 → `data/implication_graph*`

## 不要做的事

- ❌ 在 `third_party/<sub>/` 里直接改代码（修改丢失风险）
- ❌ 把 submodule 内的大数据文件复制到 `datasets/`（应直接读 submodule 或用 git-lfs）
- ❌ 让 `core/` / `solver.py` 假设某个 submodule 一定在某条 path 上 —— 通过 `core/datasets_api.py` 抽象层访问

## .gitignore 注意

`third_party/` **不**应在 `.gitignore` 里。submodule 是被 git 追踪的（追踪的是指针 commit）。
本地构建产物 (`build/`, `.lake/`) 已在根 `.gitignore` 里。
