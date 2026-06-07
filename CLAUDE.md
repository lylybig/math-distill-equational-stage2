# CLAUDE.md — 项目级原则（全员共同遵守）

## CORE PRINCIPLE: 通用引擎，不写题面针对性 hardcoded

**sample_200 / hard1-3 / 1669 contest 都是从 22M 全图采样的，不是项目目标本身。**

> 不要为某一道难题写专门的 tactic / counterexample table。
> 必须从难题中**总结类型规律**，写**通用型引擎**。
> 这是项目基调，所有 layer / engine / patch 都遵守这条。

### 推论

1. **拒绝 problem-id-keyed hardcoded 表**（除非该题真正没有任何同类规律可总结）。
2. **每发现一个解不动的题型**，先问：这是「类」的代表，还是孤例？
   - 是类 → 写一个新 stage / 新 engine 覆盖这个类
   - 是孤例 → 暂时跳过，记录到 `docs/known_intractable.md`
3. 不复制 euler.py 的 per-problem hardcoded 思路 —— 它只是把工具能力的不足往后拖。

## 反例族命名

用 ETP paper §-name，不用 local nickname：
- `linear-sec`（§3.2）
- `cyclic-sec`（§3.3）
- `twisting-sec`（§2.3.10 / §3.4）
- `cohomology-sec`（§2.3.12 / §3.6）
- `finite-sec`（§3.1 + §3.8 brute Fin）

避免用 `Brockian` / `Ray` / `EULER` 这种历史昵称，没有论文 traceability。

## 分支与目录契约

```
main                公共部分: solvers/ datasets/ docs/ + members/_template/
member/<name>       个人长期分支: 同上 + members/<name>/ 工作目录
feat/<topic>        公共改动短期分支 → PR 进 main
```

| 路径 | 在哪 | 谁可改 | Claude 行为 |
|---|---|---|---|
| `solvers/` `datasets/` `scripts/` `judge_service/` `docs/blueprints/` `docs/playbook/` | main | PR + review | 改这里要先从 main 起 `feat/<topic>` 分支 |
| `members/_template/` | main | PR + review | 改模板影响后续新成员，谨慎 |
| `members/<name>/` | `member/<name>` 分支 | 仅本人 | Claude 在该分支才看得到此目录 |
| `third_party/<sub>/` | main (submodule) | 仅 bump submodule 指针 | **绝不**直接改 submodule 内文件; 只能读 / mining pattern |
| `.env` | 本机, **不入 git** | 本人 | 永远不要把 .env 内容写进 commit / log / 文档 |
| `docs/weekly/YYYY-Www/<name>.md` | main | 仅本人 PR | 每人一个文件, 只 PR 自己那一个 |
| `docs/weekly/YYYY-Www/_lead.md` | main | 组长 PR | 组长本周总结 |

## 全员都受约束的禁忌

- ❌ 写 `if problem_id == 1738: ...`
- ❌ 把巨大输出（>1MB）commit 进 git，应走 Releases
- ❌ 直接在 main 上加 `members/<name>/`（main 上只有 `members/_template/`）
- ❌ 跨 member 分支编辑别人的 `members/<other>/`
- ❌ 编辑 `third_party/<sub>/` 内任何文件（submodule 只能 bump 指针，不能就地改）
- ❌ 把 `.env` 内容（尤其 API key）写进 commit / docs / log / PR description
- ❌ 在代码里 hardcode `JUDGE_SERVICE_URL` 或 `OPENAI_*`（应从 env 读）
- ❌ 跳过 PR review 直接合并到 main
- ❌ 用 `--no-verify` 绕过 hook

## 推荐姿势

- ✅ 想到一个 trick → 先问"它能 generalize 吗"
- ✅ 在 `member/<你>` 分支上跑一周后稳定了 → 在 `members/<你>/notes/cards/` 写卡片
- ✅ 一个 pattern 出现 3 次以上 → 提案 ADR 到 `docs/blueprints/`
- ✅ 改 `solvers/` → 先开 issue 讨论，再从 main 起 `feat/` 分支 PR
- ✅ 每周至少 `git merge origin/main` 一次到自己的 member 分支

## 个人偏好

如需追加只对自己工作目录生效的约束，写在 `members/<you>/CLAUDE.md`（只在你的 `member/<你>` 分支上存在）。
