# GPT true certificate bank MVP

## 目标

记录第一版 `gpt_true_certificates` proof bank 的本地 smoke 使用方式。该流程只生成、验证、归档 true proof certificate attempts，不修改 `solver.py`。

## 标准流程

1. 初始化全局 bank：

```bash
python scripts/lean_certificates/proof_bank_init.py \
  --bank data/processed/proof_banks/gpt_true_certificates
```

2. 从候选池生成 prompt pack：

```bash
python scripts/lean_certificates/proof_bank_build_prompt_pack.py \
  --bank data/processed/proof_banks/gpt_true_certificates \
  --candidate-pool data/processed/proof_banks/gpt_true_certificates/candidate_pools/order4_true_unsolved_v1.jsonl \
  --run-id gpt-true-cert-order4-wide-20260511-001 \
  --limit 3
```

3. 使用 `stage2-proofbank-generate-true-certificate` 在当前 Codex 会话中读取 `prompt_pack/*.md`，并写入 `raw_responses/*.txt`。

4. 导入并验证 raw responses：

```bash
python scripts/lean_certificates/proof_bank_import_responses.py \
  --run artifacts/proof_bank_runs/2026-05-11/gpt-true-cert-order4-wide-20260511-001
```

5. 合并到全局 bank：

```bash
python scripts/lean_certificates/proof_bank_merge_run.py \
  --bank data/processed/proof_banks/gpt_true_certificates \
  --run artifacts/proof_bank_runs/2026-05-11/gpt-true-cert-order4-wide-20260511-001 \
  --write
```

6. 检查 bank：

```bash
python scripts/lean_certificates/proof_bank_check.py \
  --bank data/processed/proof_banks/gpt_true_certificates
```

## 边界

- 不使用 `test_locked` individual failures 建池。
- 不修改 `solver.py`。
- 不将 accepted certificate 自动写入 solver template。
