# Public Eval Harness MVP

日期：2026-04-29

## 目标

建立第一版 public eval harness（公开集实验编排器），让后续负例反模型搜索和证书生成实验都有统一的可复现入口。

## 输入

- `data/processed/public_problem_index.jsonl`
- `data/processed/etp/etp_implications.jsonl`
- `data/processed/etp/etp_facts.jsonl`

## 方法

运行：

```bash
python scripts/public_eval/run_public_eval.py --run-id 2026-04-29-000000-public-eval-mvp --created-at-utc 2026-04-29T00:00:00Z
```

本轮机器产物写入：

```text
artifacts/runs/2026-04-29/000000-public-eval-mvp/
```

该目录包含：

- `manifest.json`：输入文件、backend（后端）和 artifact（产物）列表。
- `metrics.json`：公开集覆盖率指标。
- `errors.jsonl`：当前 harness 识别出的覆盖缺口。
- `uncovered_negatives.jsonl`：缺少 finite refutation（有限反驳）的负例问题。

## 结果

- 总行数：`1669`
- 正例：`819/819` 有 ETP implication path（蕴含路径）覆盖。
- 负例：`60/850` 有直接 finite fact/countermodel（有限事实/反模型）覆盖。
- 未覆盖正例：`0`
- 未覆盖负例：`790`

按子集拆分：

- `normal`：未覆盖负例 `472`
- `hard1`：未覆盖负例 `42`
- `hard2`：未覆盖负例 `89`
- `hard3`：未覆盖负例 `187`

## 结论

实验闭环地基已经可用：现在可以用稳定命令生成 run 目录，并把负例缺口导出给下一步搜索器。当前最大瓶颈仍是 `790` 个缺少有限反例证书路径的负例。

## 下一步

1. 实现 `search_countermodels.py` 的最小版本，读取 `uncovered_negatives.jsonl`。
2. 先对小阶 finite magma（有限岩浆）做受限搜索。
3. 将搜索出的 countermodel bank（反模型库）接回 public eval harness 复评。
