# CLAUDE.md — __MEMBER__ 个人偏好

> 这份文件只约束 Claude Code 在 `members/__MEMBER__/` 内的行为。
> 项目级原则在根 [CLAUDE.md](../../CLAUDE.md)，仍然适用。

## 不要跨界

- 不要编辑 `members/` 下其他成员的目录
- 不要编辑 `solvers/` `datasets/` `docs/` —— 那些走 PR

## 我的偏好

- (示例) 响应简洁，不要长 summary
- (示例) 改 `solver.py` 前先跑 `pytest solvers/tests/`
- (示例) 实验脚本命名 `experiments/YYYY-MM-DD-<topic>.py`

## 我的常用命令（示例占位）

```bash
# 跑 baseline (你自己的命令, 项目不提供 harness)
python -m members.__MEMBER__.solver --dataset sample_200

# 跑完后手工编辑 ../../SCOREBOARD.md 对应单元格
# 并在 notes/cards/ 写一张卡片
```
