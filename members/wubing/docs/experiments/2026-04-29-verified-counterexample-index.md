# Verified Counterexample Index

日期：2026-04-29

## 目标

将 Python 搜索出的 countermodel（反模型）、Lean 生成的 certificate（证书）、Lean batch verification（批量验证结果）和公开集等式蕴含问题关联落盘，形成可查询的 `verified_counterexamples.jsonl`。

## 输入

- `data/processed/public_problem_index.jsonl`
- `artifacts/runs/2026-04-29/000001-countermodel-search-order2-full/countermodels.jsonl`
- `artifacts/runs/2026-04-29/000003-countermodel-certificates-order2/certificate_index.jsonl`
- `artifacts/runs/2026-04-29/000003-countermodel-certificates-order2/verification.json`

## 方法

运行：

```bash
python scripts/counterexample/build_verified_counterexample_index.py \
  --countermodels artifacts/runs/2026-04-29/000001-countermodel-search-order2-full/countermodels.jsonl \
  --certificate-run artifacts/runs/2026-04-29/000003-countermodel-certificates-order2
```

默认输出到 certificate run（证书运行目录）：

```text
artifacts/runs/2026-04-29/000003-countermodel-certificates-order2/verified_counterexamples.jsonl
artifacts/runs/2026-04-29/000003-countermodel-certificates-order2/verified_counterexamples.summary.json
```

## 结果

- 关联并落盘 verified counterexample（已验证反例）：`438`
- batch verification result（批量验证结果）：`passed`
- `verified_counterexamples.jsonl` 大小约 `332KB`

每行记录包含：

- `id`、`subset`、`eq1_id`、`eq2_id`
- `equation1`、`equation2`
- `eq1_signature`、`eq2_signature`
- Python 搜索出的 `countermodel.order` 和 `countermodel.table`
- Lean `theorem_name`
- Lean certificate path（证书路径）
- Lean certificate sha256（证书哈希）
- batch verification result（批量验证结果）和 `verified`

## 结论

现在已经可以从一个负例问题直接追溯到：

1. 对应的等式蕴含 `(Equation A, Equation B)`。
2. Python 找到的具体有限 magma 运算表。
3. 生成的 Lean 4 证书文件。
4. 本地 Lean batch 验证是否通过。

这为后续压缩 countermodel bank（反模型库）、构建最终 solver、以及调试单个负例证书提供了稳定索引。
