# Countermodel Lean Certificates MVP

日期：2026-04-29

## 目标

把 size-2 countermodel bank（2 元反模型库）转换成 Lean `Fin 2` counterexample certificate（反例证书），并用本地 Lean 验证整批证书。

## 输入

- `artifacts/runs/2026-04-29/000001-countermodel-search-order2-full/countermodels.jsonl`

## 方法

生成证书：

```bash
python scripts/counterexample/generate_countermodel_certificates.py \
  --countermodels artifacts/runs/2026-04-29/000001-countermodel-search-order2-full/countermodels.jsonl \
  --run-id 2026-04-29-000003-countermodel-certificates-order2 \
  --created-at-utc 2026-04-29T00:00:03Z
```

验证 batch：

```bash
cd external/equational_theories
lake build equational_theories.Equations.All
lake env lean /home/bing/.openclaw/workspace-fenshen-executor-agent/Math-Distill-Stage2/artifacts/runs/2026-04-29/000003-countermodel-certificates-order2/batch.lean
```

## 结果

- 生成 Lean 证书：`438`
- 生成单证书目录：`artifacts/runs/2026-04-29/000003-countermodel-certificates-order2/certificates/`
- 生成合并验证文件：`artifacts/runs/2026-04-29/000003-countermodel-certificates-order2/batch.lean`
- `batch.lean` 本地 Lean 验证通过。
- Python 回归测试：`39 passed`

## 结论

size-2 反模型不仅能被 Python 找到，也能被 Lean 验证为真实反例证书。当前公共集负例中，已有 `498/850` 可通过 ETP 直接有限事实或本地搜索出的 Lean 可验证反模型覆盖。

## 下一步

1. 对剩余 `352` 个未覆盖负例做分流：先接入 ETP 全量 outcome 数据，判断哪些已有已知结论。
2. 评估 order-3 搜索成本，再决定是否全量跑。
3. 开始设计最终 solver 的压缩 countermodel bank（反模型库）编码。
