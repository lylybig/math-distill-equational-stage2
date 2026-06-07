<!-- PR 模板 -->
<!-- 注意: 只有 main 分支接受 PR; member/<name> 分支为个人长期分支, 不走 PR -->

## 改了什么 / Why

<!-- 一段话说明动机 -->

## 影响范围

- [ ] `solvers/` (需 ≥ 1 人 review)
- [ ] `scripts/` / `judge_service/` (需 ≥ 1 人 review)
- [ ] `datasets/` / `docs/blueprints/` / `docs/playbook/` (需 ≥ 1 人 review)
- [ ] `.env.example` 模板更新
- [ ] `members/_template/` (改模板影响后续新成员, 谨慎)
- [ ] `SCOREBOARD.md` 单元格更新
- [ ] `docs/weekly/YYYY-Www/<我>.md` 个人周报 (每人独立 PR)
- [ ] `docs/weekly/YYYY-Www/_lead.md` 组长周报

## 检查清单

- [ ] 没有 problem-id-keyed hardcoded
- [ ] 反例族用 paper §-name (`linear-sec` 而非 `Brockian`)
- [ ] 没有 > 1MB 文件入库 (大输出走 Releases)
- [ ] `members/_template/solver.py` 仍 ≤ 500KB
- [ ] 改了 `solvers/` API → 更新了 `docs/playbook/` 相应章节, 并提醒各 member 分支 owner merge main
- [ ] **没有在 main 上加 `members/<某个具体名字>/`** (个人目录只在 `member/<name>` 分支上)
- [ ] **没有把真的 API key 或 .env 内容写进 diff / commit message / PR description**

## 跑分对照 (如改 solvers)

| 数据集 | 改前 | 改后 |
|---|---|---|
| sample_200 | | |
| hard1 | | |
