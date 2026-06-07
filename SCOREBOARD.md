# Scoreboard

> 各成员各数据集的最佳分数。**手工维护**：跑完 benchmark 后开 PR 改本文件对应单元格。
> 本文件在 `main` 分支上；编辑需要从 main 起一个 `feat/scoreboard-<你>-<date>` 短期分支再 PR。

格式：`<百分比>% (<solved>/<total>)`，例如 `92.00% (184/200)`。

最后更新：—

| 成员 | sample_200 | hard1 (69) | hard2 (200) | hard3 (400) | normal (1000) | 全图估计 | 最近更新 |
|---|---|---|---|---|---|---|---|
| wubing | — | — | — | — | — | — | — |
| zhangkang | — | — | — | — | — | — | — |
| yanliang | — | — | — | — | — | — | — |

## 更新流程

1. 在自己的 `member/<你>` 分支上跑 benchmark
2. 在 `members/<你>/notes/cards/YYYY-MM-DD-<slug>.md` 写实验卡片（commit 到自己分支）
3. 起 `feat/scoreboard-<你>-<date>` 分支：
   ```bash
   git switch main && git pull
   git checkout -b feat/scoreboard-<你>-$(date +%Y%m%d)
   # 编辑本文件对应单元格 + "最近更新"列 + 顶部"最后更新"
   git add SCOREBOARD.md && git commit -m "scoreboard: <你> sample_200 92.0%"
   git push -u origin HEAD
   gh pr create --title "scoreboard: <你> <dataset> <score>"
   ```
4. 把原始 log/cex 打包后用 `gh release upload <tag> <file.tar.gz>` 推到 Release，**不要**入 git，卡片里贴 URL

## 历史里程碑

| 日期 | 事件 | 成绩 |
|---|---|---|
| 2026-05-25 | 仓库初始化 | — |
