# cards/

实验卡片。每张卡片回答四个问题：

1. **假设** (Hypothesis): 想验证什么？
2. **做法** (Setup): 数据 / 引擎 / 参数
3. **结果** (Result): 分数 + 关键观察
4. **下一步** (Next): 继续 / 转向 / 放弃

文件名: `YYYY-MM-DD-<short-slug>.md`

**手工创建**：复制下方模板，填好后 push。

```markdown
# <slug> — <dataset>

- date: YYYY-MM-DD
- member: __MEMBER__
- dataset: sample_200
- solved: 184 / 200
- score: 0.9200
- run_id: 2026-W22-001

## 假设
## 做法
## 结果
## 下一步

## Raw outputs
Packed to dist/<...>.tar.gz, uploaded to release tag <tag>: <url>
```

巨型原始输出（log / cex.jsonl）**不进 git**，走 GitHub Releases，卡片里只放 Release URL。
