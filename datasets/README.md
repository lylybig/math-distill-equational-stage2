# datasets/ — 数据来源说明

> 本目录**不保存大数据集**。真正数据来自 `third_party/` submodule + 本地生成的 lawbook。

## 数据从哪来

| 数据 | 路径 | 备注 |
|---|---|---|
| 全图 4694 等式定义 | `third_party/equational_theories/data/Equations.lean` 等 | Lean 表 |
| 全图 22M 蕴含 CSV oracle | `third_party/equational_theories/data/` (CSV 文件分块) | 直接读 submodule |
| 比赛 1669 contest benchmark | `third_party/equational-theories-lean-stage2/` (具体路径以官方 README 为准) | 比赛官方 |
| sample_200 / hard1 / hard2 / hard3 / normal | 从上述 oracle 采样生成；定义见 [docs/playbook/datasets.md](../docs/playbook/datasets.md) | 各成员本地缓存 |
| **lawbook** (~16MB) | `datasets/lawbook/` (gitignored) | zhangkang 的工作; 见 [docs/playbook/lawbook.md](../docs/playbook/lawbook.md) |
| **intractable class samples** (~468KB, in git) | `datasets/intractable_class_samples/` | 6 个按失败类 (V/E/B/R/D/C) 拆的 test set；见 [`docs/known_intractable.md`](../docs/known_intractable.md) + 本目录 [README](intractable_class_samples/README.md) |

## 为什么数据不入 git

- 全图 22M 蕴含 + 4694 等式定义在 `third_party/equational_theories/` 已是权威源，重复入库会冗余且容易漂移
- lawbook 16MB 太大且属个人工作产物
- 采样集 (sample_200 等) 是从上游派生，定义脚本入库 > 派生结果入库

## 例外

如果将来要入 git 的小型派生集（< 1MB 单文件，少改动），可加在本目录下，
并更新本表 + `docs/playbook/datasets.md`，走 PR。
